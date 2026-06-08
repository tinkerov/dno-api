# DNO API — Асинхронный Fullstack Интернет-Магазин

[Telegram](https://t.me/char0n4ikbaby)

Асинхронный бэкенд на **FastAPI**, полностью контейнеризированный с помощью **Docker Compose**. Проект включает в себя полноценную систему JWT-аутентификации с использованием Refresh-токенов в защищенных куках, ORM-моделирование и автоматизированное тестирование с высоким покрытием кода.

---

## 🚀 Технологический стек

* **Framework:** FastAPI (полностью асинхронный режим)
* **Database:** PostgreSQL 15 + драйвер `asyncpg`
* **ORM:** SQLAlchemy 2.0 (Async Engine & AsyncSession)
* **Security:** Хэширование паролей **Argon2** (`passlib`), токены **JWT** (`python-jose`)
* **Validation:** Pydantic v2
* **Testing:** Pytest + `pytest-asyncio` + `httpx` (AsyncClient)
* **DevOps:** Docker, Docker Compose, pgAdmin 4

---

## ⚙️ Ключевые архитектурные фичи

1. **Безопасная аутентификация (Access + Refresh):**
   * **Access Token:** Передаётся в заголовке `Authorization: Bearer <token>`, имеет короткий срок жизни.
   * **Refresh Token:** Записывается бэкендом в безопасные куки браузера (`httponly=True`, `samesite="lax"`). Хранится в базе данных для валидации активных сессий пользователя. При его отзыве (`/logout`) сессия полностью уничтожается на стороне бэкенда и стирается у клиента.
2. **Отказоустойчивый запуск инфраструктуры (Lifespan + Retries):**
   * При старте приложения FastAPI выполняет встроенный цикл ретраев подключения к БД (5 попыток с интервалом в 2 секунды). Бэкенд плавно дожидается готовности контейнера PostgreSQL, после чего автоматически создаёт или проверяет структуры таблиц (`Base.metadata.create_all`).
3. **Изолированная среда тестирования:**
   * Тесты запускаются на выделенной базе данных `my_store_db_test`.
   * Использование асинхронных фикстур с `autouse=True` гарантирует, что перед каждым тестом база разворачивается с нуля, а после — полностью очищается (`drop_all`), изолируя тесты друг от друга.

---

## 🛠️ Эндпоинты API (Маршрутизация)

### Аутентификация (`tags=['Authentication']`)
* `POST /register` — Регистрация нового аккаунта. Проверяет дубликаты Email, хэширует пароль через Argon2.
* `POST /login` — Аутентификация (форма `OAuth2PasswordRequestForm`). Генерирует пару токенов, устанавливает `refresh_token` в куки, возвращает `access_token`.
* `POST /refresh` — Обновление сессии. Читает токен из куки, валидирует его подпись и выдает свежий `access_token` на 30 минут без необходимости повторного ввода пароля.
* `POST /logout` — Выход из системы. Стирает токен из базы данных через CRUD-метод и очищает клиентские куки.

### Каталог товаров (`prefix="/items"`)
* `GET /items/` — Получить полный список доступных товаров в магазине.
* `POST /items/` — Добавить новый товар в магазин (требует валидации по схеме Pydantic).

---

## 🧬 Схемы данных (Pydantic & SQLAlchemy Models)

### База данных (SQLAlchemy)
* **User**: `id` (PK), `email` (Unique), `hashed_password`, `is_active`, `refresh_token` (Nullable).
* **Product**: `id` (PK), `name`, `price`, `description` (Nullable), `in_stock`, `image_url` (Nullable).

### Валидация (Pydantic)
* Конфигурация схем ответа (`UserResponse`, `ProductResponse`) использует флаг `from_attributes = True` для прямой совместимости с асинхронными объектами SQLAlchemy.

---

## 💻 Инструкция по локальному запуску (Для чайников)

### 1. Подготовка
Убедитесь, что на вашем компьютере установлены **Python 3.10+**, **Git** и запущен **Docker Desktop**.

### 2. Клонирование и запуск инфраструктуры (БД и Redis)
Откройте терминал в папке с проектом (где лежит файл `docker-compose.yml`) и запустите базу данных и Redis в контейнерах:

`docker-compose up -d`

Убедитесь, что контейнеры успешно поднялись командой docker ps.

3. Настройка виртуального окружения Python
Находясь в очередной папке проекта, выполните команды:

Для Windows:

`python -m venv venv`

`.\venv\Scripts\activate`

Для macOS / Linux:

`python3 -m venv venv`

`source venv/bin/activate`

### 4. Установка библиотек

`pip install --upgrade pip`

`pip install -r requirements.txt`

### 5. Запуск сервера FastAPI
Так как весь код приложения изолирован в папке backend, перейдите в неё и запустите uvicorn:

`cd backend`

`uvicorn app.main:app --reload`
Сервер запущен! Интерактивная документация (Swagger) доступна тут: http://127.0.0.1:8000/docs

## 🧪 Тестирование и Coverage
Чтобы запустить автотесты и проверить покрытие кода, зайдите в папку backend с активным виртуальным окружением (venv) и выполните:

`cd backend`

`pytest --cov=app tests/`

## 🛑 Возможные проблемы при запуске
Ошибка Connect call failed в тестах: Убедитесь, что Docker Desktop запущен, а контейнеры с PostgreSQL и Redis активны (docker ps). Тестам необходим запущенный Docker-контейнер с базой.

Ошибка file or directory not found: tests/: Вы пытаетесь запустить pytest из корня проекта. Сначала перейдите в папку бэкенда: cd backend.
