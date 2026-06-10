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

nota: el gion o espacio, determina el funcionamiento, se crea con uno o con otro
pero no se puede levantar denuevo con el otro comando porque da error. 

Levantar todos estos servicios desde cero demora 1500+ segundos = 25 minutos.

```bash
sudo docker-compose up --build
# o
sudo docker compose up --build 

```
---

# Interactuar con la API

## Documentación interactiva (Swagger)

Una vez iniciada la API:

http://localhost:8000/docs

Documentación OpenAPI:

http://localhost:8000/openapi.json



## Crear orden de predicción

Genera una nueva orden para evaluar riesgo de incendio en una ubicación y fecha determinada.

```bash
curl -X POST http://localhost:8000/api/v1/orden -H "Content-Type: application/json" -d '{ "dia": 20211125,"lat": -34.249801, "lon": -58.880148 }'

```

### Respuesta esperada

```json
{
  "id": 1,
  "status": "Pendiente.."
}
```

---

## Consultar orden

```bash
curl -X GET http://localhost:8000/api/v1/orden/1
```

### Mientras se procesa

```text
Estado: Pendiente..
```

### Cuando la predicción está lista

```json
{
  "id": 1,
  "status": "Predicha",
  "prediccion": "Riesgo Alto",
  "modelo_utilizado": "fire_model_ver_10.pth"
}
```

### Si no existe

```json
{
  "detail": "Orden No encontrada"
}
```

---

## Generar datos de entrenamiento

Crea una orden para descargar y procesar datos históricos que luego podrán utilizarse para entrenamiento.

```bash
curl -X POST http://localhost:8000/api/v1/generar_datos \
-H "Content-Type: application/json" \
-d '{
  "dia": 20211125,
  "lat": -34.249801,
  "lon": -58.880148
}'
```

### Respuesta esperada

```json
{
  "id": 1,
  "status": "pending"
}
```

---

## Consultar estado de generación de datos

```bash
curl -X GET http://localhost:8000/api/v1/generar_datos/1
```

### Respuesta posible

```text
Estado: pending
```

o

```text
Estado: completado
```

### Si no existe

```json
{
  "detail": "Entrenamiento no encontrado"
}
```

---

## Health Check

Permite verificar el estado general del sistema y sus dependencias.

```bash
curl -X GET http://localhost:8000/api/v1/health
```

### Respuesta esperada

```json
{
  "services": {
    "api": {
      "status": "UP",
      "uptime": "0:15:42"
    },
    "worker": {
      "status": "UP",
      "descripcion": "Buscando Ordenes",
      "last_seen": "2026-06-02T07:11:26.355989",
      "seconds_since_last_heartbeat": 4
    },
    "validador": {
      "status": "UP"
    },
    "entrenador": {
      "status": "UP"
    },
    "modelador": {
      "status": "UP"
    },
    "predictor": {
      "status": "UP"
    },
    "analista": {
      "status": "UP"
    }
  },
  "dependencies": {
    "database": "UP",
    "minio": "UP"
  }
}
```

---

## Listar modelos entrenados

```bash
curl -X GET http://localhost:8000/api/v1/modelos
```

### Respuesta esperada

```json
[
  {
    "id": 2,
    "name": "fire_model_ver_10.pth",
    "final_loss": 0.5877,
    "best_loss": 0.5877,
    "pred_mean": 0.7220,
    "pred_min": 0.6190,
    "pred_max": 0.7255,
    "accuracy": 0.7256,
    "precision": 0.7256,
    "recall": 1.0,
    "f1_score": 0.8409,
    "iou": 0.7256,
    "dice": 0.8409,
    "dataset_size": 10,
    "created_at": "2026-06-02T07:22:49.181331"
  }
]
```

### Si todavía no existen modelos

```json
{
  "Error": "No hay Modelos"
}
```

---

## Obtener últimos informes analíticos

Devuelve los 20 informes más recientes generados por el analista.

```bash
curl -X GET http://localhost:8000/api/v1/informes
```

### Respuesta esperada

```json
[
  {
    "id": 5,
    "created_at": "2026-06-02T20:47:40.623231",
    "contenido": "Resumen Ejecutivo..."
  }
]
```

---

## Obtener último informe

```bash
curl -X GET http://localhost:8000/api/v1/informes/ultimo
```

### Respuesta esperada

```json
{
  "id": 5,
  "created_at": "2026-06-02T20:47:40.623231",
  "contenido": "Resumen Ejecutivo..."
}
```

### Si no existen informes

```json
{
  "error": "sin informes"
}
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


