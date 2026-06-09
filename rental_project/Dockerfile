FROM python:3.14-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# ПРОВЕРКА: есть ли нужные файлы
RUN test -f manage.py && echo "✓ manage.py found" || echo "✗ ERROR: manage.py not found"
RUN test -f rental_project/wsgi.py && echo "✓ wsgi.py found" || echo "✗ ERROR: wsgi.py not found"

ENV DJANGO_SETTINGS_MODULE=rental_project.settings

EXPOSE 8000

CMD ["gunicorn", "rental_project.wsgi:application", "--bind", "0.0.0.0:8000"]
