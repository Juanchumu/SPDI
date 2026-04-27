detección de incendios basada en evolución temporal multibanda.

Indice A es ndvi
Indice B es nbr
Indice C es ndbi

dataset/
├── train/
│   ├── inputs/
│   │   ├── escena_001.tif   (25 bandas)
│   │   └── ...
│   └── masks/
│       ├── escena_001.tif   (1 banda)
│       └── ...




inputs/escena_001.tif
├── banda 1 → imagen 1 índice A
├── banda 2 → imagen 1 índice B
├── banda 3 → imagen 1 índice C
├── banda 4 → imagen 1 máscara de nubes
├── banda 5 → imagen 1 fecha normalizada
├── banda 6 → imagen 2 índice A
├── banda 7 → imagen 2 índice B
├── banda 8 → imagen 2 índice C
├── banda 9 → imagen 2 máscara de nubes
├── banda 10 → imagen 2 fecha normalizada
├── banda 11 → imagen 3 índice A
├── banda 12 → imagen 3 índice B
├── banda 13 → imagen 3 índice C
├── banda 14 → imagen 3 máscara de nubes
├── banda 15 → imagen 3 fecha normalizada
├── banda 16 → imagen 4 índice A
├── banda 17 → imagen 4 índice B
├── banda 18 → imagen 4 índice C
├── banda 19 → imagen 4 máscara de nubes
├── banda 20 → imagen 4 fecha normalizada
├── banda 21 → imagen 5 índice A
├── banda 22 → imagen 5 índice B
├── banda 23 → imagen 5 índice C
├── banda 24 → imagen 5 máscara de nubes
└── banda 25 → imagen 5 fecha normalizada

masks/escena_001.tif
└── banda 1 → imagen 6 incendio (0/1)






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

curl -X POST http://localhost:8000/api/v1/generar_datos

curl -X POST http://localhost:8000/orden -H "Content-Type: application/json" -d '{ "dia": 20260318, "izquierda": -58.745420, "derecha": -58.738993, "abajo": -34.631716, "arriba": -34.628794 }'
  

* Devuelve

{
  "id": 1,
  "status": "pending"
}
### Consultar:

curl -X GET http://localhost:8000/orden/1

devuelve: 

{Estado: pending}
{Estado: Riesgo de Incendio Elevado}



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

sudo docker exec -it entrenamiento-worker-1 /bin/bash
python
from app.script import run

run("20211124",-34.209041,-58.886371,None)

run("20260318",-58.745420,-58.738993,-34.631716,-34.628794,None)


## Problemas de permisos de usuario por utilizar un usuario en vez de root


touch /app/descargas/test.txt

# Problemas de SPAM

We apologize, but you have reached the maximum number of concurrent sessions.
