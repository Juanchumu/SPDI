# Como usar:

### levantar:

antiguo: docker-compose up --build

# Detener contenedores
docker-compose down

# Reconstruir sin caché para instalar nuevas dependencias
docker-compose build --no-cache

# Levantar servicios
docker-compose up





* Crear Orden:

curl -X POST http://localhost:8000/orden -H "Content-Type: application/json" -d '{ "dia": 20260318, "izquierda": -58.745420, "derecha": -58.738993, "abajo": -34.631716, "arriba": -34.628794 }'
  

* Devuelve

{
  "id": 1,
  "status": "pending"
}
### Consultar:

curl -X GET http://localhost:8000/orden/1

devuelve: 







# En caso de errores:


# Limpiar completamente

### Esto borra volúmenes (incluye postgres_data)
sudo docker-compose down -v 

### Limpia imágenes no usadas
sudo docker system prune -a  

# Reconstruir
sudo docker-compose build --no-cache

# Crear carpetas locales (si no existen)
mkdir -p data descargas

# Levantar
sudo docker-compose up



# Entrar en el worker:

sudo docker exec -it captura_worker_1 /bin/bash
python

run("20260318",-58.745420,-58.738993,-34.631716,-34.628794,None)

