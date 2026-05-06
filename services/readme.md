# Cómo usar

## Levantar servicios

Utilizá uno de estos comandos según tu instalación de Docker:

```bash
sudo docker-compose up --build
# o
sudo docker compose up --build
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

## Crear orden

```bash
curl -X POST http://localhost:8000/orden \
  -H "Content-Type: application/json" \
  -d '{ "dia": 20260318, "lat": -58.745420, "lon": -58.738992 }'
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
curl -X GET http://localhost:8000/orden/1
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
{
  "status": "200"
}
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
sudo docker exec -it captura_worker_1 /bin/bash
```

Dentro del contenedor:

```python
run("20260318", -58.745420, -58.738993, None)
```

