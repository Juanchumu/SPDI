FROM python:3.11

WORKDIR /app

# Crear usuario no root
RUN useradd -m appuser

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y netcat-openbsd && rm -rf /var/lib/apt/lists/*

# Copiar requirements primero (mejor caching)
COPY worker-x/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY worker-x/app ./app
COPY db ./db

# Dar permisos al usuario sobre /app
RUN chown -R appuser:appuser /app

# Script entrypoint
COPY worker-x/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh && chown appuser:appuser /entrypoint.sh
RUN mkdir -p /app/ordenes/inputs && chown -R appuser:appuser /app



ENV PYTHONPATH=/app

# Cambiar a usuario no root 👇
USER appuser

ENTRYPOINT ["/entrypoint.sh"]




















