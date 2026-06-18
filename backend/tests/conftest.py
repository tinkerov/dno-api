import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from app.database import Base, get_db
from app.main import app
import pytest_asyncio

TEST_DATABASE_URL = "postgresql+asyncpg://user:password@127.0.0.1:5432/my_store_db_test"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)

TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

@pytest.fixture(scope="session")
def event_loop():
     policy = asyncio.get_event_loop_policy()
     loop = policy.new_event_loop()
     yield loop
     loop.close()

@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture(scope="function")
async def db_session():
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()

@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport, 
        base_url="http://test",
        cookies={}
    ) as ac:
        yield ac
        
    app.dependency_overrides.clear()

@pytest_asyncio.fixture(scope="function")
async def auth_client(client):
     await client.post("/register", json={
          "email": "auth_email@test.com",
          "password": "test_password"
     })
     login_res = await client.post("/login", data={
          "username": "auth_email@test.com",
          "password": "test_password"
     })
     token = login_res.json()["access_token"]
     client.headers.update({"Authorization": f"Bearer {token}"})
     yield client