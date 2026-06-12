FROM python:3.11-slim

WORKDIR /app

# Dependencias del sistema necesarias para rasterio
RUN apt-get update && apt-get install -y netcat-openbsd \
    gdal-bin \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

# Usuario no root
RUN useradd -m appuser

# Requirements primero (cache docker)
COPY predictor-x/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Código
COPY predictor-x/app ./app
COPY db ./db

# Entrypoint
COPY predictor-x/entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

# Directorios temporales
RUN mkdir -p /app/tmp && chown -R appuser:appuser /app /entrypoint.sh

ENV PYTHONPATH=/app

USER appuser

ENTRYPOINT ["/entrypoint.sh"]
