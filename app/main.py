from fastapi import FastAPI
from contextlib import asynccontextmanager
from . import models
from .database import engine
from .routers import items
from .routers import auth

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Асинхронно создаем таблицы если их нет
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
    yield

app = FastAPI(title="DNO", lifespan=lifespan)

# Подключаем items, auth
app.include_router(items.router)
app.include_router(auth.router)

@app.get("/")
async def root(): # Добавил async
    return {"message": "DNO API is running"}