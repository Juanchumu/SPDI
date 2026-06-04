# Repositorio del SPID

Este repositorio contiene un proyecto desarrollado para la materia **Proyecto Integrador de Ciencias de Datos**.

## Estructura del proyecto
El proyecto consiste en un sistema de predicción de incendios basado en el procesamiento de datos satelitales históricos y modelos de *Machine Learning*.

### Diagrama C1
Podemos observar el flujo general de los datos. 
El usuario accede al sistema solicitando una predicción indicando latitud y longitud, el sistema procesa la solicitud, descarga las imagenes satelitales de la zona durante el ultimo mes para generar una predicción la cual devuelve en distintos formatos: un dashboard en frontend web o alertas mediante aplicaciones de mensajería.
Aclaración: El valor de 0.42 km cuadrados tiene que ver con una decisión técnica que involucra tomar imagenes de 200x200 pixeles, midiendo cada uno 10 metros cuadrados, se llega a ese valor de 0.42 km cuadrados.

<img src="https://raw.githubusercontent.com/Juanchumu/SPDI/3547abdf846184c2ec9e81f5e100dce5406014ff/diagramas/C1.svg" >

---

### Diagrama C2

<img src="https://raw.githubusercontent.com/Juanchumu/SPDI/3547abdf846184c2ec9e81f5e100dce5406014ff/diagramas/C2.svg">

A nivel técnico, el proyecto sigue una arquitectura modular, separando las distintas etapas del procesamiento de datos, entrenamiento y despliegue.
Los componentes (organizados en contenedores docker) son:
### API
<img src="https://raw.githubusercontent.com/Juanchumu/SPDI/3547abdf846184c2ec9e81f5e100dce5406014ff/diagramas/API.svg">
Acá se presentan los endpoints que permiten a los usuarios hacer solicitudes, recibir respuesta, consultar el estado de la consulta y el estado de los servicios en general.
Tambien permite a los administradores probar distintos modelos, conocer el estado de las ordenes y entrenar el modelo (ingresando nuevos datos de incendio mediante el endpoint *Generar_datos*).
Actualización: El endpoint Health ahora incorpora el uso de un modelo LLM que genera un reporte ready friendly sobre el estado del servicio, problemas, sugerencias de mejoras/soluciones, etc.

### Entrenador

<img src="https://raw.githubusercontent.com/Juanchumu/SPDI/3547abdf846184c2ec9e81f5e100dce5406014ff/diagramas/entrenador.svg">

### Modelador
<img src="https://raw.githubusercontent.com/Juanchumu/SPDI/3547abdf846184c2ec9e81f5e100dce5406014ff/diagramas/modelador.svg">
Este componente se encarga de buscar las imágenes nuevas en miniIO para realizar un entrenamiento guardando el resultado en un bucket de minIO, le asigna un id y lo registra en la base de datos junto a métricas de rendimiento del modelo lo cual permite rankear los modelos y elegir el de mejor performance siempre.



# Organización de las carpetas y guía de uso
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
