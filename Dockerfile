FROM python:3.11-slim

WORKDIR /app

# Установка зависимостей
RUN apt-get update && \
    apt-get install -y --no-install-recommends unzip && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt --no-cache-dir

COPY . .

RUN mkdir -p uploads model

# Убираем явное EXPOSE (Render сам управляет портами)
CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "app:app"]