# Repositorio del SPID

Este repositorio contiene un sistema de predicción de incendios basado en procesamiento de datos satelitales historicos y modelos de machine learning.

## Hipotesis:
 Utilizar Imagenes Satelitales de amplio espectro historicas para entrenar modelos y predecir incendios.

## Resultado:
Despues de modelar utilizando todos los registros de incendios en argentina respondemos:

* Utilizar unicamente imagenes satelitales para predecir incendios no entrega un modelo que
prediga algun incendio.

## Imformacion importante para los interesados: 
* Se necesita incluir mas fuentes de datos en los entrenamientos 
- Rayos en tiempo real, pronosticos clima.. etc. 

* La utilizacion de los datos en bruto de sentinelHub te puede bloquear la ip 
- Procura descargan una unica vez cada archivo .safe .
- La api de MS solo da datos ya calculados (que utilizamos debido al bloqueo).


## Estructura del proyecto

El proyecto sigue una arquitectura modular, separando las distintas etapas del pipeline de datos y despliegue:

### 🔹 `services/`

Contiene los servicios principales del sistema en producción:

* API, Workers, todos independientes.
* Configuración Docker

📌 **Punto de entrada recomendado**
Dentro de este directorio hay un `readme.md` con instrucciones para levantar todo el sistema con Docker.

---

### 🔹 `tools/`

Scripts para generación de datasets o probar la api, una vez levantado los servicios, 
se puede correr un script para que genere unos datos de entrenamiento.
que pueden ser con datos reales o generados

---

### 🔹 `notebooks/`

Notebooks de experimentación:

* Entrenamiento del modelo
* Archivo del modelo (`fire_model.pth`)

---


### 🔹 `test/`

Pruebas y validaciones del sistema.

---



