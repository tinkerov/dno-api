import pytest
import pytest_asyncio
from jose import jwt
import os

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