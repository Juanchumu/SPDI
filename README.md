# Repositorio del SPID

Este repositorio contiene un sistema de predicción de incendios basado en procesamiento de datos satelitales y modelos de machine learning.

## Estructura del proyecto

El proyecto sigue una arquitectura modular, separando las distintas etapas del pipeline de datos y despliegue:

### 🔹 `services/`

Contiene los servicios principales del sistema en producción:

* API (FastAPI)
* Workers (generación de datos y predicción)
* Configuración Docker

📌 **Punto de entrada recomendado**
Dentro de este directorio hay un `readme.md` con instrucciones para levantar todo el sistema con Docker.

---

### 🔹 `entrenamiento/`

Entorno de entrenamiento del modelo (el cual no funciona por cambios):

* Scripts de entrenamiento
* Definición de modelos
* Workers auxiliares
* Dataset de ejemplo (`datos_reales/`)

Incluye su propio `docker-compose.yml` para ejecutar procesos de entrenamiento de forma aislada.

---

### 🔹 `data/`

Organización de datos siguiendo un flujo típico de ciencia de datos:

* `raw/` → datos originales sin procesar
* `interim/` → datos intermedios
* `processed/` → datos listos para modelado

---

### 🔹 `generador_dataset/`

Scripts para generación de datasets, utilizados en etapas previas al entrenamiento.

---

### 🔹 `notebooks/`

Notebooks de experimentación:

* Entrenamiento del modelo
* Pruebas exploratorias
* Archivo del modelo (`fire_model.pth`)

---

### 🔹 `reports/`

Resultados y visualizaciones:

* Figuras generadas
* Análisis y resúmenes

---

### 🔹 `src/`

Código fuente auxiliar o en desarrollo.

---

### 🔹 `test/`

Pruebas y validaciones del sistema.

---

## Flujo general del sistema

1. Generación/descarga de datos (`generador_dataset/`, `data/`)
2. Procesamiento de datos
3. Entrenamiento del modelo (`entrenamiento/`)
4. Despliegue del modelo y servicios (`services/`)
5. Consulta mediante API

---


