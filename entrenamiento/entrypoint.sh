#!/bin/bash
# entrypoint.sh

echo "Esperando a que PostgreSQL esté listo..."
while ! nc -z db 5432; do
  sleep 1
done
echo "PostgreSQL está listo!"

# Ejecutar el comando que se pasó al contenedor
exec "$@"
