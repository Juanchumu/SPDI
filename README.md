# Repositorio del SPID

Este repositorio contiene un proyecto desarrollado para la materia **Proyecto Integrador de Ciencias de Datos**.

<img src="https://raw.githubusercontent.com/Juanchumu/SPDI/e9f17bf140584c73542d7b34e4e5b3df9219dd31/C1.svg" >

## Estructura del proyecto
El proyecto consiste en un sistema de predicción de incendios basado en el procesamiento de datos satelitales históricos y modelos de *Machine Learning*.


---

# Estructura del proyecto

El proyecto sigue una arquitectura modular, separando las distintas etapas del procesamiento de datos, entrenamiento y despliegue.

## 🔹 `services/`

Contiene los servicios principales del sistema en producción:

- API
- Workers.. Servicios independientes
- Configuración Docker

### 📌 Punto de entrada recomendado

Dentro de este directorio se encuentra un archivo `README.md` con las instrucciones necesarias para desplegar todo el sistema utilizando Docker.

---

## 🔹 `tools/`

Contiene scripts auxiliares para:

- Generación de datasets
- Pruebas de la API
- Creación de datos de entrenamiento

Una vez levantados los servicios, pueden ejecutarse scripts para generar conjuntos de entrenamiento utilizando datos reales o datos sintéticos.

---

## 🔹 `notebooks/`

Notebooks utilizados durante la etapa de experimentación:

- Entrenamiento del modelo
- Evaluación de resultados
- Generación del archivo del modelo (`fire_model.pth`)

---

## 🔹 `test/`

Pruebas y validaciones del sistema.

---

# Notas finales

## Hipótesis planteada

Utilizar imágenes satelitales históricas de amplio espectro para entrenar modelos capaces de predecir incendios.

## Resultado obtenido

Tras entrenar y evaluar modelos utilizando la totalidad de los registros históricos de incendios disponibles para Argentina, se concluye que:

- El uso exclusivo de imágenes satelitales no permite construir un modelo con capacidad predictiva suficiente para anticipar incendios de manera útil.

## Información importante para quienes deseen continuar el proyecto

### Fuentes de datos adicionales

Para mejorar los resultados es necesario incorporar nuevas fuentes de información, por ejemplo:

- Detección de rayos en tiempo real.
- Pronósticos meteorológicos.
- Variables atmosféricas y climáticas.
- Información topográfica y de vegetación.

### Requisitos de hardware

Se recomienda disponer de al menos **64 GB de RAM** para procesar imágenes satelitales en formato bruto (`.SAFE`).

### Consideraciones sobre las fuentes de datos

Durante el desarrollo del proyecto se utilizaron principalmente datos obtenidos mediante otra api, ya que el acceso masivo a imágenes satelitales sin procesar generó restricciones y bloqueos por IP.

Según lo indicado por el profesor de la materia, estos datos presentan una menor precisión que los datos satelitales originales, debido a que son distribuidos con una menor cantidad de decimales y ya procesados previamente. Esto puede haber afectado negativamente la calidad de los entrenamientos y los resultados obtenidos.

Se recomienda, cuando sea posible:

- Descargar cada archivo `.SAFE` una única vez.
- Mantener una copia local de los datos descargados.
- Trabajar directamente con las imágenes satelitales originales para conservar la máxima precisión disponible.
- Utilizar las fuentes procesadas únicamente cuando existan limitaciones de acceso o recursos de hardware.
