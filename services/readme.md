detección de incendios basada en evolución temporal multibanda.
# Cómo usar

## 1 
dentro del directorio services se tiene que correr:

```bash
sudo chmod -R 777 .
```
esto es porque algunos contenedores generan archivos en local, de momento...

en los directorios

## 2 
### Levantar servicios
Por primera vez solo hay que levantar 
la api y la db 

```bash
sudo docker compose up --build db api 

```
y despues entrar al contenedor de la api y correr  

```bash
sudo docker exec -it services-api-1  bash

python app/crearDB.py 

```
Con esto ya estarian creadas las tablas 

Ctrl + C para detener todo y ahi recien  levantar todo según tu instalación de Docker:
```bash
sudo docker-compose up --build
# o
sudo docker compose up --build

sudo docker-compose up api db worker minio

```
---

# Interactuar con la API

##  Crear orden o un archivo de entrenamiento

```bash

curl -X POST http://localhost:8000/api/v1/orden -H "Content-Type: application/json" -d '{ "dia": "20211125", "lat": "-34.249801", "lon": "-58.880148" }'
```
```bash

curl -X POST http://localhost:8000/api/v1/generar_datos -H "Content-Type: application/json" -d '{ "dia": "20211125", "lat": "-34.249801", "lon": "-58.880148" }'

```

### Respuesta esperada

```json
{
  "id": 1,
  "status": "pending"
}
```

---

## Consultar orden

```bash
curl -X GET http://localhost:8000/api/v1/orden/1
```
```bash
curl -X GET http://localhost:8000/api/v1/generar_datos/1
```

### Si sale todo bien

```json
{
  "riesgo": "alto",
  "porcentaje_area_riesgo": 23.78,
  "zonas_criticas": [
    {
      "x1": 120,
      "y1": 45,
      "x2": 180,
      "y2": 110,
      "pixels": 3500
    },
    {
      "x1": 300,
      "y1": 200,
      "x2": 360,
      "y2": 260,
      "pixels": 1800
    }
  ],
  "archivo_prediccion": "ordenes/predictions/pred_42.tif"
}
```

### En caso de error

```json
{
  "status": "404"
}
```

---

## Health check (estado de la API)

```bash
curl -X GET http://localhost:8000/api/v1/health
```

### Respuesta esperada

```json
{"status_code":200,"message":"Todo anda bien por acá.","uptime":"0:05:51"}
```

--- 

# Cosas a cambiar:

## Listar Servicios

En caso de levantar un unico servicio.

```bash
sudo docker compose config --services
```

## Detener contenedores

```bash
docker-compose down
```

## Reconstruir sin caché (para instalar nuevas dependencias)

```bash
docker-compose build --no-cache
```

## Levantar servicios (modo normal)

```bash
docker-compose up
```



---

## En caso de errores con Docker

### Limpiar completamente (incluye volúmenes como postgres_data)

```bash
sudo docker-compose down -v
```

### Eliminar imágenes no utilizadas

```bash
sudo docker system prune -a
```

### Reconstruir sin caché

```bash
sudo docker-compose build --no-cache
```

### Crear carpetas locales (si no existen)

```bash
mkdir -p data descargas
```

### Levantar servicios nuevamente

```bash
sudo docker-compose up
```

---

## Entrar en el worker

```bash
sudo docker exec -it services-worker-1 /bin/bash
```

Dentro del contenedor:

```python
run("20211124", -34.249801, -58.880148, None)
```

### Postgre

si la db no se modifica al tocar el codigo,
y permanece con datos antiguos:
sudo docker compose down -v
sudo docker volume prune -f





## TODO: 


* 
* DB de usuarios, con tokens para cada uno. 
* Api -> seccion documentacion para saber como funciona la api
* Healt -> tipo semaforos que muestre todos los servicios
* MiniO para los archivos
* Versionado de modelos de entrenamiento

* 1 contar como funiona todo
* 2 cuando va mejorando el modelo
* 3 las respuestas de la api tienen que servir para que una fuente que la consuma pueda tomar decisiones


