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

### 🔹 `data/`

Organización de datos siguiendo un flujo típico de ciencia de datos:

* `raw/` → datos originales sin procesar
* `interim/` → datos intermedios
* `processed/` → datos listos para modelado

---

### 🔹 `tools/`

Scripts para generación de datasets o probar la api, una vez levantado los servicios, 
se puede correr un script para que genere unos datos de entrenamiento.
que pueden ser con datos reales o generados

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



