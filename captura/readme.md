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

POST /orden
{
  "lat": -34.6,
  "lon": -58.4
}

* Devuelve

{ "id": 1 }

### Consultar:

GET /orden/1

devuelve: 

status: pending → processing → done
