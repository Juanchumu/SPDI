FROM python:3.11

WORKDIR /app

# Crear usuario no root
RUN useradd -m appuser

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y netcat-openbsd && rm -rf /var/lib/apt/lists/*

# Copiar requirements primero (mejor caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Dar permisos al usuario sobre /app
RUN chown -R appuser:appuser /app

# Script entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh && chown appuser:appuser /entrypoint.sh

ENV PYTHONPATH=/app

# Cambiar a usuario no root 👇
USER appuser

ENTRYPOINT ["/entrypoint.sh"]

CMD ["sh", "-c", "python app/crearDB.py && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
