FROM python:3.11-slim

WORKDIR /app

# ==================================================
# Dependencias del sistema
# ==================================================

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    netcat-openbsd \
    gdal-bin \
    libgdal-dev \
    libproj-dev \
    libgeos-dev \
    && rm -rf /var/lib/apt/lists/*

# ==================================================
# Variables GDAL
# ==================================================

ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

# ==================================================
# Usuario no root
# ==================================================

RUN useradd -m appuser

# ==================================================
# Python requirements
# ==================================================

COPY modelador-x/requirements.txt .

RUN pip install --upgrade pip

RUN pip install --no-cache-dir -r requirements.txt

# ==================================================
# Código
# ==================================================

COPY modelador-x/app ./app
COPY db ./db

COPY modelador-x/entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

RUN chown -R appuser:appuser /app /entrypoint.sh

ENV PYTHONPATH=/app

USER appuser

ENTRYPOINT ["/entrypoint.sh"]

