FROM python:3.11

WORKDIR /app

# Crear usuario no root
RUN useradd -m appuser

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y netcat-openbsd && rm -rf /var/lib/apt/lists/*

# Copiar requirements primero (mejor caching)
COPY entrenador/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY entrenador/app ./app
COPY db ./db
COPY worker/app/osm_utils.py ./app/osm_utils.py
COPY validador/app/argentina.geojson ./argentina.geojson


# Dar permisos al usuario sobre /app
RUN chown -R appuser:appuser /app

# Script entrypoint
COPY entrenador/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh && chown appuser:appuser /entrypoint.sh
RUN mkdir -p /app/dataset/train/inputs && chown -R appuser:appuser /app
RUN mkdir -p /app/dataset/train/masks && chown -R appuser:appuser /app

ENV PYTHONPATH=/app

# Cambiar a usuario no root 👇
USER appuser

ENTRYPOINT ["/entrypoint.sh"]

