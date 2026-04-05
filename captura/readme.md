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

curl -X POST http://localhost:8000/orden \
  -H "Content-Type: application/json" \
  -d '{
    "dia": 20260318,
    "izquierda": -58.745420,
    "derecha": -58.738993,
    "abajo": -34.631716,
    "arriba": -34.628794
  }'
  

* Devuelve

{
  "id": 1,
  "status": "pending"
}
### Consultar:

GET /orden/1

devuelve: 

status: pending → processing → done
