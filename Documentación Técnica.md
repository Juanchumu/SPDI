# Documentación Técnica - Ignis Guard

Este documento describe la arquitectura, los componentes y el flujo de datos del Sistema de Predicción de Incendios (Ignis Guard).

## Estructura y Flujo de Datos

El proyecto consiste en un sistema de predicción de incendios basado en el procesamiento de datos satelitales históricos y modelos de *Machine Learning*.

### Diagrama C1
Podemos observar el flujo general de los datos. 
El usuario accede al sistema solicitando una predicción indicando latitud y longitud, el sistema procesa la solicitud, descarga las imagenes satelitales de la zona durante el ultimo mes para generar una predicción la cual devuelve mediante el  frontend web.
Aclaración: El valor de 0.42 km cuadrados tiene que ver con una decisión técnica que involucra tomar imagenes de 200x200 pixeles, midiendo cada uno 10 metros cuadrados, se llega a ese valor de 0.42 km cuadrados.

![Diagrama C1](/diagramas/C1.svg)

---

### Diagrama C2

El siguiente diagrama permite una visión en detalle de los distintos componentes del sistema y como se interrelacionan entre sí. Para verlo en detalle, pueden acceder a `/diagramas`.

![Diagrama C2](/diagramas/C2.png)

## Componentes del Sistema

A nivel técnico, el proyecto sigue una arquitectura modular, separando las distintas etapas del procesamiento de datos, entrenamiento y despliegue.
Los componentes (organizados en contenedores docker) son:

### API
![Diagrama API](/diagramas/api.jpg)

Acá se presentan los endpoints que permiten a los usuarios hacer solicitudes, recibir respuesta, consultar el estado de la consulta y el estado de los servicios en general.
Tambien permite a los administradores probar distintos modelos, conocer el estado de las ordenes y entrenar el modelo (ingresando nuevos datos de incendio mediante el endpoint *Generar_datos*).
Actualización: El endpoint `/Informes` ahora incorpora el uso de un modelo LLM que genera un reporte sobre el estado del servicio, problemas, sugerencias de mejoras/soluciones, etc.

### Entrenador
![Diagrama Entrenador](/diagramas/entrenador.svg)

Este componente se encarga de recibir localizaciones historicas en donde hubo incendios, generando asi, el dataset para los entrenamientos.  

### Modelador
![Diagrama Modelador](/diagramas/modelador.svg)

Este componente se encarga de buscar las imágenes nuevas en minIO para realizar un entrenamiento guardando el modelo nuevo en un bucket de minIO, le asigna un id y lo registra en la base de datos junto a métricas de rendimiento del modelo lo cual permite rankear los modelos y elegir el de mejor performance siempre.

### Predictor
![Diagrama Predictor](/diagramas/predictor.svg)

El predictor revisa la cola de ordenes, toma una orden y procede igual que el modelador: busca las imagenes del ultimo mes en minIO asociadas al id de la orden, realiza la predicción con el modelo indicado (politica actualmente hardcodeada), guarda el resultado en minIO y registra en la base de datos. (Tambien cambia el estado de la orden).

### Validador
![Diagrama Validador](/diagramas/validador.svg)

Este sitema se encarga de validar la orden recibida por la API, de momento contiene unos bloques IF sobre los atributos de las ordenes.
En si, este seria el espacio para verificar (todavia no implementadas) que las ordenes cumplan requerimientos de seguridad, coberturas.. etc. 

### Worker
![Diagrama Worker](/diagramas/worker.svg)

Se encarga de descargar las imagenes satelitales de una orden, sobre las cuales, el predictor realizará la predicción.

### Bases de datos
![Diagrama Base de Datos](/diagramas/bd.jpg)

El sistema tiene dos tipos de bases de datos: 
* **PostgreSQL:** Con una estructura relacional donde se lleva registro de las ordenes solicitadas y sus estados, de los modelos disponibles y sus métricas, los entrenamientos y las descargas.
* **MinIO (AWS Local):** Para almacenar las imagenes de entrenamiento, las usadas para predicción, los modelos y los archivos .tiff que son el resultado de la predicción y se pueden entender como un mapa probabilistico donde cada pixel representa el riesgo de incendio en ese punto.

### Módulos de Inteligencia Artificial
![Diagrama Analista](/diagramas/analista.jpg)

El sistema integra modelos de IA generativa con dos propósitos y arquitecturas distintas:

1. **Auditoría Local para Administradores (Ollama):** Se implementó Ollama de forma local (utilizando el modelo `llama3.2:3b`) para generar reportes sobre el estado del servicio. Este analista ingesta logs, estados de órdenes y métricas de modelos para generar un resumen ejecutivo con problemas detectados, riesgos y recomendaciones operativas. El procesamiento local garantiza la privacidad de la información de infraestructura.
2. **Generación de Alertas para Clientes (Gemini API):** Se integró la API de Google Gemini (`gemini-2.5-flash`) para redactar dinámicamente correos electrónicos de alerta personalizados dirigidos a los clientes. Al delegar esta tarea a la API de Gemini, se asegura una redacción rápida, natural y de alta calidad sin sobrecargar los recursos computacionales locales del servidor.

---

## Notas de Investigación y Resultados

### Hipótesis planteada
Utilizar imágenes satelitales históricas de amplio espectro para entrenar modelos capaces de predecir incendios.

### Resultado obtenido
Tras entrenar y evaluar modelos utilizando la totalidad de los registros históricos de incendios disponibles para Argentina, se concluye que:
- El uso exclusivo de imágenes satelitales no permite construir un modelo con capacidad predictiva suficiente para anticipar incendios de manera útil.

### Información importante para continuar el proyecto

#### Fuentes de datos adicionales
Para mejorar los resultados es necesario incorporar nuevas fuentes de información, por ejemplo:
- Detección de rayos en tiempo real.
- Pronósticos meteorológicos.
- Variables atmosféricas y climáticas.
- Información topográfica y de vegetación.

#### Requisitos de hardware
Originalmente, el sistema requería disponer de al menos **64 GB de RAM** para procesar imágenes satelitales en su formato bruto monolítico (`.SAFE`). Gracias a la migración a la API de Microsoft Planetary Computer y la estrategia de submuestreo de XGBoost, estos requerimientos disminuyeron drásticamente, permitiendo su ejecución en estaciones de trabajo o servidores estándar.

#### Optimización del Entrenamiento (Submuestreo de Píxeles)
Durante la etapa de entrenamiento en el módulo **Modelador**, se aplica un submuestreo aleatorio limitado a **10.000 píxeles por imagen** (aproximadamente el 25% de una imagen estándar de 200x200). Esta decisión técnica se fundamenta en:

1. **Eficiencia de Memoria RAM:** Una imagen completa de 200x200 píxeles representa 40.000 filas de datos. Si se procesan conjuntos de datos extensos (por ejemplo, 70 imágenes), el modelo XGBoost tendría que ingerir millones de filas simultáneamente. Limitar la ingesta de píxeles evita la saturación de la memoria y previene caídas por falta de recursos en el contenedor Docker.
2. **Mitigación de la Autocorrelación Espacial:** En las imágenes satelitales, los píxeles adyacentes suelen ser altamente redundantes (un píxel de "bosque quemado" es estadísticamente casi idéntico a su vecino inmediato). Ingerir 40.000 píxeles por imagen no aporta información sustancialmente nueva al modelo frente a tomar una muestra de 10.000. 

Mediante este muestreo, el modelo logra capturar de manera óptima las firmas espectrales de las distintas superficies (incendios, vegetación, cuerpos de agua, nubosidad) manteniendo una alta precisión y reduciendo drásticamente la carga computacional.

#### Balanceo del Dataset y Casos de Control
El conjunto de datos de entrenamiento se encuentra **balanceado de forma natural**, garantizando una adecuada representación de casos positivos ("Incendio") y negativos ("No Incendio"). Esto se logra mediante dos estrategias fundamentales:

1. **Aprovechamiento del Contexto Espacial:** Al procesar una imagen satelital de 4x4 km (200x200 píxeles) correspondiente a un evento de incendio, el área afectada (delimitada por el *shapefile*) generalmente ocupa una porción menor de la imagen. Los píxeles restantes se etiquetan automáticamente como clase `0` (No Incendio). Esta técnica provee al modelo XGBoost con ejemplos negativos que comparten exactamente las mismas condiciones atmosféricas y lumínicas que los píxeles positivos, mejorando la capacidad discriminativa del algoritmo entre vegetación sana y afectada.
2. **Escenas de Control Estáticas:** En el proceso de recopilación de imágenes históricas (ver [`services/entrenador-x/app/generate_dataset_from_shapes.py`](services/entrenador-x/app/generate_dataset_from_shapes.py)), se incorporaron intencionalmente cinco escenas de control donde la superficie quemada es estrictamente nula (`0.0`). Estas escenas actúan como casos extremos para mitigar falsos positivos:
   - Centro urbano densamente construido (ej. Ciudad de Buenos Aires).
   - Extensas masas de agua profunda (ej. Lago Nahuel Huapi).
   - Superficies acuáticas con alta salinidad/sedimentos (ej. Laguna Mar Chiquita).
   - Suelo desnudo o arado sin cobertura vegetal (ej. campos en Santa Fe). 
   Estas escenas previenen que el modelo confunda firmas espectrales de espejos de agua o áreas urbanas con áreas quemadas o cenizas.

#### Ingesta y Procesamiento mediante XGBoost
A nivel computacional, XGBoost no procesa la imagen en su estructura matricial bidimensional nativa. Durante el submuestreo aleatorio, el sistema transforma los 10.000 píxeles seleccionados en un conjunto tabular estructurado. Cada píxel se convierte en una fila independiente que consta de 18 columnas:

- **Columnas 1 a 17 (Features):** Variables derivadas de las bandas satelitales e índices calculados (como Infrarrojo, NDVI, NBR), sumado a variables espaciales (distancia a rutas, distancia a zonas de acampe).
- **Columna 18 (Target):** La variable objetivo que indica la presencia (`1`) o ausencia (`0`) de incendio.

A partir de este conjunto de datos (que puede superar el millón de filas al agregar múltiples imágenes), XGBoost construye iterativamente un ensamble de árboles de decisión. El algoritmo infiere patrones estadísticos complejos multivariables, determinando probabilidades basadas en la combinación de los índices espectrales y factores antrópicos.

#### APIs y Fuentes de Datos Utilizadas
El sistema se nutre de distintas APIs para componer tanto el dataset de entrenamiento como la interfaz de usuario:

1. **Microsoft Planetary Computer (MPC):** Se utiliza su API STAC (`stac/v1`) para consultar y descargar las imágenes satelitales multiespectrales históricas y recientes (Sentinel-2). Estas imágenes son la base para calcular los índices espectrales (NDVI, NBR, etc.) que alimentan al modelo. 
   *(Nota sobre la migración: En una primera instancia, se intentó descargar las imágenes directamente desde Copernicus en su formato bruto original `.SAFE`. No obstante, este enfoque resultó ser tan pesado e impráctico para procesar localmente que se decidió migrar a MPC, lo cual permite un acceso fraccionado y mucho más ágil a los datos).*
2. **OpenStreetMap (OSM):** Mediante esta API se obtienen vectores de infraestructura y factores antrópicos (rutas y zonas de acampe), fundamentales como variables predictoras de riesgo.
3. **ESRI (ArcGIS World Imagery):** Se emplea como capa base (*basemap*) en el frontend (portal web), brindando imágenes satelitales de alta resolución para que el usuario tenga una referencia visual clara al visualizar el mapa de riesgos superpuesto.

#### Cálculo de Distancias Antrópicas (Rutas y Campings)
Para determinar el impacto humano en el riesgo de incendio, el sistema calcula la distancia exacta desde cada píxel del mapa hasta la ruta o camping más cercano. El proceso técnico (implementado en `osm_utils.py`) es el siguiente:

1. **Extracción y Filtrado:** Se consulta la API de OSM solicitando geometrías específicas dentro del perímetro de la imagen extendida. Para las rutas se buscan vías de tránsito, y para los campings se filtra estrictamente por la etiqueta `tourism=camp_site`.
2. **Proyección y Rasterización:** Las coordenadas obtenidas se reproyectan al sistema de coordenadas local UTM. Esto es crítico para que los cálculos métricos sean exactos. Luego, las geometrías vectoriales se rasterizan, convirtiéndose en una máscara binaria sobre la grilla satelital.
3. **Transformada de Distancia Euclidiana:** Se aplica un algoritmo de *Distance Transform* (mediante `scipy.ndimage.distance_transform_edt`). Este algoritmo calcula la distancia euclidiana más corta desde cada píxel de la imagen hasta el píxel más cercano marcado como ruta o camping. Al multiplicar el resultado por la resolución espacial (10 metros por píxel), se obtiene una matriz donde cada celda contiene su distancia real en metros. Para evitar errores de cálculo en los bordes (*edge effects*), el sistema descarga un perímetro extendido de OSM antes de realizar el cómputo y luego recorta el resultado al tamaño exacto de la imagen.

#### Consideraciones y Restricciones de Datos
Durante etapas tempranas del proyecto, el acceso masivo a imágenes satelitales sin procesar generó bloqueos por IP.
Según los lineamientos académicos, el uso de datos pre-procesados de terceros presenta una menor precisión que los datos satelitales originales, debido al truncamiento de decimales. Esto puede mermar la calidad predictiva.

Se recomienda para uso en producción intensivo:
- Descargar cada imagen `.SAFE` una única vez y mantener copias locales.
- Trabajar directamente con la imagen original para conservar la máxima precisión flotante.
- Utilizar fuentes procesadas únicamente como plan de contingencia ante caídas de la API principal.
