FROM python:3.14-slim

WORKDIR /app

# Копируем requirements.txt и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем ВСЕ файлы проекта
COPY . .

# Проверяем, что manage.py на месте
RUN test -f rental_project/manage.py || (echo "ERROR: manage.py not found in rental_project/" && exit 1)

# Переменные окружения
ENV DJANGO_SETTINGS_MODULE=rental_project.settings
ENV PYTHONUNBUFFERED=1

# Открываем порт
EXPOSE 8000

# Запускаем gunicorn
CMD ["gunicorn", "rental_project.wsgi:application", "--bind", "0.0.0.0:8000"]
