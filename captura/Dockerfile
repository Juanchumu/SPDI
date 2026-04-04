FROM python:3.11

WORKDIR /app

# Instalar netcat para el healthcheck y esperar a la DB
RUN apt-get update && apt-get install -y netcat-openbsd && rm -rf /var/lib/apt/lists/*

# Copiar requirements primero (mejor para caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Asegurar que Python encuentre los módulos correctamente
ENV PYTHONPATH=/app

# Script de entrada para esperar a la base de datos
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

# Comando por defecto (puede ser sobrescrito por docker-compose)
CMD ["sh", "-c", "python app/crearDB.py && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
