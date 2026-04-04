# Como usar:

### levantar:

docker-compose up --build

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
