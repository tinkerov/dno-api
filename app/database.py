from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

SQLALCHEMY_DATABASE_URL = "postgresql+asyncpg://user:password@localhost:5432/my_store_db"

engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=True)

# Переводим сессии на async
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as db:
        yield db
        # Сессия закрывается автоматически после завершения запроса