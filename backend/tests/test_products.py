import pytest

@pytest.mark.asyncio
async def test_create_and_get_product(auth_client):
    # Поменяли "title" на "name", как требует твоя схема в Pydantic
    create_res = await auth_client.post("/items", json={
        "name": "Худи GONE.Fludd",
        "price": 132.0,
        "description": "Правда выше флекса"
    }, follow_redirects=True)
    
    assert create_res.status_code in [200, 201]

    # Запрашиваем список товаров
    get_res = await auth_client.get("/items", follow_redirects=True)
    assert get_res.status_code == 200
    
    # Вытаскиваем "name" из каждого объекта в списке
    names = [item["name"] for item in get_res.json()]
    assert "Худи GONE.Fludd" in names