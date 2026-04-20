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

{"args":"{\"dia_de_la_imagen\": \"20211114\", \"izquierda\": -58.92191, \"derecha\": -58.82097, \"abajo\": -34.28828, \"arriba\": -34.22117}","ruta_safe":null,"id":1,"created_at":"2026-04-19T22:26:38.077911","status":"error","ruta_stack":null,"updated_at":"2026-04-19T22:30:19.166821"}





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

