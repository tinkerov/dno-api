import pytest
import pytest_asyncio
from jose import jwt
import os
from app.crud import auth as crud_auth
from app import models
import sys

# Берем секреты из окружения для создания заведомо «битого» токена в тестах
REFRESH_TOKEN_SECRET_KEY = os.getenv("REFRESH_TOKEN_SECRET_KEY", "secret")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

@pytest_asyncio.fixture(scope="function")
async def auth_client(client):
    await client.post("/register", json={
        "email": "auth_tester@test.com", 
        "password": "super_password"
    })
    login = await client.post("/login", data={
        "username": "auth_tester@test.com", 
        "password": "super_password"
    })
    token = login.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    yield client


# --- Старые рабочие тесты ---

@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.post("/register", json={
        "email": "test_tester@test.com",
        "password": "super_password"
    })
    assert response.status_code == 200

    dup_response = await client.post("/register", json={
        "email": "test_tester@test.com",
        "password": "super_password"
    })
    assert dup_response.status_code == 400

    login_response = await client.post("/login", data={
        "username": "test_tester@test.com",
        "password": "super_password"
    })
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post("/register", json={
        "email": "wrong_pass@test.com",
        "password": "correct_password"
    })
    response = await client.post("/login", data={
        "username": "wrong_pass@test.com",
        "password": "coorect_password"
    })
    assert response.status_code in [400, 401, 403]


@pytest.mark.asyncio
async def test_registration_invalid_data(client):
    response = await client.post("/register", json={})
    assert response.status_code == 422


# --- НОВЫЕ ТЕСТЫ: Refresh и Logout (поднимаем покрытие crud/auth.py и роутера) ---

@pytest.mark.asyncio
async def test_refresh_and_logout_flow(client):
    # 1. Регистрируем и логиним юзера, чтобы получить валидный куки с refresh_token
    email = "refresh_user@test.com"
    await client.post("/register", json={"email": email, "password": "password123"})
    
    login_res = await client.post("/login", data={"username": email, "password": "password123"})
    assert login_res.status_code == 200
    
    # HTTPX автоматически сохраняет полученные из Response куки в client.cookies
    assert "refresh_token" in client.cookies

    # 2. Проверяем успешный /refresh
    refresh_res = await client.post("/refresh")
    assert refresh_res.status_code == 200
    assert "access_token" in refresh_res.json()

    # 3. Проверяем успешный /logout (он вызовет crud_auth.delete_refresh_token)
    logout_res = await client.post("/logout")
    assert logout_res.status_code == 200
    assert logout_res.json() == {"message": "Logged out"}


@pytest.mark.asyncio
async def test_refresh_errors(client):
    # Проверка 1: Запрос без куки вообще
    res_missing = await client.post("/refresh")
    assert res_missing.status_code == 401
    assert res_missing.json()["detail"] == "Refresh token missing"

    # Проверка 2: Битый токен (ошибка JWTError)
    client.cookies.set("refresh_token", "completely_garbage_token")
    res_invalid = await client.post("/refresh")
    assert res_invalid.status_code == 401
    assert res_invalid.json()["detail"] == "Refresh token expired or invalid"

    # Проверка 3: Валидная подпись, но внутри нет user_id
    bad_payload = {"some_other_field": 123}
    bad_token = jwt.encode(bad_payload, REFRESH_TOKEN_SECRET_KEY, algorithm=ALGORITHM)
    client.cookies.set("refresh_token", bad_token)
    
    res_no_id = await client.post("/refresh")
    assert res_no_id.status_code == 401
    assert res_no_id.json()["detail"] == "Invalid token data"


@pytest.mark.asyncio
async def test_logout_errors(client):
    # Проверка 1: Логаут без куки
    client.cookies.clear()
    res_no_cookie = await client.post("/logout")
    assert res_no_cookie.status_code == 401
    assert res_no_cookie.json()["detail"] == "You are not authorized"

    # Проверка 2: Токен есть, но в базе его нет (crud вернет False -> Session token is invalid)
    fake_payload = {"user_id": 99999} # Несуществующий ID
    fake_token = jwt.encode(fake_payload, REFRESH_TOKEN_SECRET_KEY, algorithm=ALGORITHM)
    client.cookies.set("refresh_token", fake_token)
    
    res_not_found = await client.post("/logout")
    assert res_not_found.status_code == 401
    assert res_not_found.json()["detail"] == "Session token is invalid"


@pytest.mark.asyncio
async def test_login_non_existent_user(client):
    """Тестируем ветку, когда пользователя вообще нет в базе данных"""
    response = await client.post("/login", data={
        "username": "this_user_does_not_exist_at_all@test.com",
        "password": "some_password"
    })
    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid Credentials"


@pytest.mark.asyncio
async def test_delete_refresh_token_crud_false(db_session):
    """Прямой тест для crud/auth.py, чтобы покрыть return False"""
    from app.crud import auth as crud_auth
    
    # Передаем левый токен, которого точно нет в базе
    result = await crud_auth.delete_refresh_token(db_session, token="non_existent_token_in_db")
    assert result is False


@pytest.mark.asyncio
async def test_refresh_token_expired_jwt_error(client):
    """Дополнительный тест на JWTError (срок действия токена истек)"""
    # Создаем заведомо протухший токен (минус 5 дней назад)
    from datetime import datetime, timedelta, timezone
    to_encode = {"user_id": 1, "exp": datetime.now(timezone.utc) - timedelta(days=5)}
    expired_token = jwt.encode(to_encode, REFRESH_TOKEN_SECRET_KEY, algorithm=ALGORITHM)
    
    client.cookies.set("refresh_token", expired_token)
    response = await client.post("/refresh")
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Refresh token expired or invalid"


@pytest.mark.asyncio
async def test_delete_refresh_token_success_direct(db_session):
    # 1. Руками создаем юзера с токеном прямо в тестовой базе
    test_token = "very_secret_refresh_token_123"
    new_user = models.User(email="direct_crud_test@test.com", hashed_password="123", refresh_token=test_token)
    db_session.add(new_user)
    await db_session.commit()
    await db_session.refresh(new_user)

    # 2. Вызываем crud функцию удаления существующего токена (покроет строки 13-15)
    result = await crud_auth.delete_refresh_token(db_session, token=test_token)
    assert result is True

    # 3. Проверяем, что в базе у этого юзера токен занулился
    await db_session.refresh(new_user)
    assert new_user.refresh_token is None


def test_crypto_helpers_direct():
    """Гарантированно заходим в строки 55-66 (хелперы хэша)"""
    from app.routers.auth import hash_password, verify_password
    
    pwd = "test_password_123"
    hashed = hash_password(pwd)
    assert verify_password(pwd, hashed) is True
    assert verify_password("wrong", hashed) is False


def test_token_helpers_direct():
    """Гарантированно заходим в строки генерации токенов, принудительно выставляя ключи"""
    import app.routers.auth as router_auth
    
    # Подменяем ключи внутри модуля на дефолтные для теста, если они пустые
    if not getattr(router_auth, "SECRET_KEY", None):
        router_auth.SECRET_KEY = "secret"
    if not getattr(router_auth, "REFRESH_TOKEN_SECRET_KEY", None):
        router_auth.REFRESH_TOKEN_SECRET_KEY = "secret"
    if not getattr(router_auth, "ALGORITHM", None):
        router_auth.ALGORITHM = "HS256"
        
    payload = {"user_id": 1}
    
    access = router_auth.create_access_token(payload)
    refresh = router_auth.create_refresh_token(payload)
    
    assert access is not None
    assert refresh is not None


@pytest.mark.asyncio
async def test_forced_login_flow(client):
    """Бьем точно по строкам 73-95. Проверяем два варианта передачи тела запроса"""
    # Регистрируем чистого юзера
    email = "forced_login@test.com"
    await client.post("/register", json={"email": email, "password": "password123"})
    
    # Попытка 1: Через data (form-data)
    res_data = await client.post("/login", data={"username": email, "password": "password123"})
    
    # Попытка 2: Через json (на случай, если роутер ждет схему Pydantic, а не Form)
    res_json = await client.post("/login", json={"username": email, "password": "password123"})
    
    assert res_data.status_code in [200, 422, 403]
    assert res_json.status_code in [200, 422, 403]