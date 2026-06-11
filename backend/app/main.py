from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from . import models
from .database import engine
from .routers import items
from .routers import auth
from fastapi.staticfiles import StaticFiles
import asyncio
from sqlalchemy import text

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ретраи для проверки подключения к базе данных при старте
    retries = 5
    while retries > 0:
        try:
            print("Проверка подключения к базе данных...")
            # ИСПРАВЛЕНО: Вместо создания таблиц просто пингуем базу
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            print("Подключение к базе данных успешно проверено!")
            break  # Если всё прошло успешно, выходим из цикла
        except Exception as e:
            retries -= 1
            print(f"База данных ещё не готова ({e}). Осталось попыток: {retries}. Ждём 2 секунды...")
            if retries == 0:
                print("Не удалось подключиться к базе данных после всех попыток. Выход.")
                raise e
            await asyncio.sleep(2)
    yield

app = FastAPI(title="DNO", lifespan=lifespan)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем items, auth
app.include_router(items.router)
app.include_router(auth.router)

@app.get("/")
async def root(): # Добавил async
    return {"message": "DNO API is running"}