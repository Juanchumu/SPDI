# Sistema de Predicción de Incendios (Ignis Guard)

Este repositorio contiene un proyecto desarrollado para la materia **Proyecto Integrador de Ciencias de Datos**.
El proyecto consiste en un sistema de predicción de incendios basado en el procesamiento de datos satelitales históricos y modelos de *Machine Learning*.

> **Nota:** Para conocer en detalle la arquitectura de microservicios, el flujo de datos y los resultados de la investigación, consulte el archivo `Documentación Técnica.md`.

## Organización de las Carpetas

- `services/`: Contiene los servicios principales del sistema en producción (API, Workers, Configuración Docker, Frontend Angular, etc).
- `tools/`: Scripts auxiliares para generación de datasets y pruebas.
- `notebooks/`: Notebooks utilizados durante la etapa de experimentación y entrenamiento del modelo.
- `test/`: Pruebas y validaciones del sistema.
- `diagramas/`: Diagramas de arquitectura del sistema.

---

## Requisitos Previos e Instalación

Para poder ejecutar este proyecto, es fundamental cumplir con los siguientes requisitos previos:

### 1. Archivo de Variables de Entorno (`.env`)
El sistema requiere un archivo `.env` en el directorio `services/`, el cual debe contener las credenciales y configuraciones necesarias para los distintos servicios (base de datos, MinIO, credenciales de API para los modelos, etc.). Por cuestiones de seguridad, este archivo no se incluye en el repositorio público. Existe un archivo `dotenv_ejemplo.txt` dentro de la carpeta `services/` que debe usarse como plantilla.

### 2. Shapefiles y Datos Geográficos Protegidos
El proyecto requiere una carpeta de Google Drive que contiene *shapefiles* específicos para el procesamiento espacial. **Estos archivos no se encuentran subidos al repositorio público** debido a que la información fue solicitada formalmente a la **Dirección Nacional de Mitigación y Prevención (DNMyP)**, perteneciente a la **Agencia Federal de Emergencias (AFE)**. Esta entidad establece restricciones de confidencialidad que no permiten compartir dicha información públicamente.

---

## Ejecución del Sistema (Docker)

Todo el entorno está dockerizado y se debe levantar desde el directorio `services/`.

1. **Dar permisos de ejecución** (necesario ya que algunos contenedores generan archivos localmente):
   ```bash
   cd services
   sudo chmod -R 777 .
   ```

2. **Levantar los servicios esenciales por primera vez (API y BD)** para crear las tablas:
   ```bash
   sudo docker compose -f docker-compose-x.yml up --build db api
   ```
   Una vez iniciados, abrir otra terminal, entrar al contenedor de la API e inicializar la base de datos:
   ```bash
   sudo docker exec -it services-api-1 bash
   python app/crearDB.py
   exit
   ```
   Luego, detener los servicios con `Ctrl + C`.

3. **Levantar el sistema completo (con modelo XGBoost):**
   Para levantar todo el entorno ejecutando la variante del modelo basado en XGBoost, se debe utilizar explícitamente el archivo `docker-compose-x.yml`. Dependiendo de la versión de Docker instalada, utiliza uno de estos comandos (levantar todo desde cero puede demorar ~25 minutos):
   ```bash
   sudo docker-compose -f docker-compose-x.yml up --build
   # O si usas la versión más reciente:
   sudo docker compose -f docker-compose-x.yml up --build
   ```

### Troubleshooting de Docker
- **Listar servicios configurados:** `sudo docker compose config --services`
- **Detener contenedores:** `sudo docker compose down`
- **Limpiar volúmenes y contenedores (Hard reset):** `sudo docker compose down -v`
- **Reconstruir sin caché:** `sudo docker compose build --no-cache`

---

## Uso del Sistema

Una vez que el sistema está en ejecución, se puede interactuar con él a través de la API REST o de su frontend web.

### Frontend Web (Angular)
El sistema cuenta con un portal interactivo de administración y monitoreo. Si todos los servicios están en ejecución, puede acceder vía navegador a la URL y puerto configurado (ej: `http://localhost:4200` o mapeado mediante Nginx al puerto `80`).

### Documentación Interactiva (Swagger)
Para explorar, testear o automatizar peticiones, la API expone documentación auto-generada:
- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **OpenAPI JSON:** [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

### Ejemplos de uso mediante API (cURL)

**1. Verificar el estado del sistema (Healthcheck):**
```bash
curl -X GET http://localhost:8000/api/v1/health
```

**2. Crear una orden de predicción:**
Genera una nueva orden para evaluar riesgo de incendio en una ubicación y fecha determinada.
```bash
curl -X POST http://localhost:8000/api/v1/orden \
     -H "Content-Type: application/json" \
     -d '{ "dia": 20211125, "lat": -34.249801, "lon": -58.880148 }'
```

**3. Consultar el estado de una orden:**
```bash
curl -X GET http://localhost:8000/api/v1/orden/1
```

**4. Ver los informes automáticos (Módulo Analista IA):**
Devuelve los informes ejecutivos autogenerados.
```bash
curl -X GET http://localhost:8000/api/v1/informes/ultimo
```
