# Используем легковесный официальный образ Python
FROM python:3.11-slim

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /backend

# Запрещаем Python писать файлы .pyc на диск и буферизировать stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Сначала копируем ТОЛЬКО requirements.txt, чтобы Docker кэшировал установку зависимостей
COPY requirements.txt .

# Обновляем pip и ставим все либы
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Теперь копируем всё остальное приложение (код, тесты, статику)
COPY . .

# Открываем порт, на котором будет крутиться FastAPI
EXPOSE 8000

# Команда для запуска сервака через uvicorn
# Предполагаем, что экземпляр FastAPI (app = FastAPI()) находится в app/main.py
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]