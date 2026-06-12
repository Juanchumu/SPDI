este worker genera informes sobre un cliente en particular y analisa que tan riesgoso es
asegurarlo o tomarlo

osea, le delega a un modelo la decision. entre nosotros sabemos que la respuesta va a estar dada
por la probabilidad de las palabras.

se le pasa una descripcion del cliente, el cual se tiene que anotar al dar de alta:

se tiene que preguntar: 
cuanto personal posee | esto es para saber si el cliente posee la capacidad de prepararse para un incendio 

si utiliza agua de pozo o tiene una laguna cerca 

y se le pasan las predicciones "predicha" del cliente 

----------------------------------------------------------

tendria que agarrar todos los clientes y ver si alguno esta malo y de ahi generar el informe 




## Servicio de análisis automático con LLM

Este worker genera informes técnicos automáticos sobre el estado operativo del sistema utilizando un modelo de lenguaje (LLM).

### ¿Cómo funciona?

Cada 5 minutos el servicio:

1. Recolecta métricas desde la base de datos.
2. Obtiene información sobre:
   - Cantidad total de órdenes.
   - Órdenes pendientes.
   - Órdenes procesadas.
   - Errores detectados.
   - Último modelo entrenado.
   - Estado de los distintos workers.
3. Envía estas métricas al servicio LLM.
4. Genera un informe técnico automático.
5. Almacena el informe en la tabla `Informes`.

### Backend LLM

El proyecto utiliza un servicio remoto compatible con la API de OpenAI.

La infraestructura es provista por los docentes de la materia mediante una URL y un token de acceso. El worker consume dicho servicio para realizar análisis automáticos del estado general de la plataforma.

### Modelo utilizado

```text
llama3.2:3b
```

### Variables de entorno requeridas

| Variable | Descripción |
|-----------|-------------|
| `OLLAMA_URL_A` | URL del servidor LLM compartido por los docentes |
| `OLLAMA_TOKEN` | Token de autenticación para acceder al servicio |

### Prueba de funcionamiento

Durante las pruebas iniciales se verificó la conectividad con el servicio y la capacidad de generación de informes automáticos.

Se obtuvo correctamente un informe almacenado en la base de datos con la siguiente estructura:

```json
{
"id":1,
"created_at":"2026-06-02T20:47:40.623231",
"contenido":"**Resumen Ejecutivo**\n\nEl sistema distribuido analizado presentaba un estado operativo general de satisfacción, con una brecha significativa entre el número predictedo de órdenes y las órdenes reales. Esta diferencia se debe en gran parte a la alta tasa de errores detectados.\n\n**Estado General del Sistema**\n\nEl sistema distribuido presenta los siguientes factores relevantes:\n\n*   **Órdenes:** El sistema tiene un total de 2 órdenes pendientes y 2 predicte, lo que sugiere una brecha significativa entre la información predicta y real.\n*   **Errores:** Se detectaron 0 errores durante el estado revisión realizado al momento del examen.\n\n**Problemas Detectados**\n\nAl analizar el sistema distribuido se detectan los siguientes problemas en este caso:\n\n*   **Difera entre órdenes predita y órdenes reales**\n\n**Riesgos**\n\nLos riesgos más significativos incluyen la alta tasa de erroresdetectados, la brecha significant entre el número predictedo de ordenes y las órdenes reales y la posibilidad que los elementos que realizan estas operaciones tengan alguna falla en su funcionamiento.\n\n**Recomendaciones**\n\nPara abordar estos problemas se recomienda:\n\n*   **Desarrollar un sistema más preciso:** La implementación de algoritmos avanzados y técnicas de aprendizaje automático.\n*   **Validar la información prioralmente:** Para asegurarse que las órdenes sean validadas antes de implementarse en el sistema.\n*   **Diseñar un sistema de alerta para errores:** Para detectar los posibles errores antes de que afecten al público.\n*   **Entrenar a los trabajadores:** sobre la importancia de los datos precisos y cómo identificar errores cuando ocurren."}
```
--- 
### En version md
**Resumen Ejecutivo**

El sistema distribuido analizado presentaba un estado operativo general de satisfacción, con una brecha significativa entre el número predictedo de órdenes y las órdenes reales. Esta diferencia se debe en gran parte a la alta tasa de errores detectados.

**Estado General del Sistema**

El sistema distribuido presenta los siguientes factores relevantes:

**Órdenes:** El sistema tiene un total de 2 órdenes pendientes y 2 predicte, lo que sugiere una brecha significativa entre la información predicta y real.

**Errores:** Se detectaron 0 errores durante el estado revisión realizado al momento del examen.
**Problemas Detectados** Al analizar el sistema distribuido se detectan los siguientes problemas en este caso:
**Difera entre órdenes predita y órdenes reales**

**Riesgos** Los riesgos más significativos incluyen la alta tasa de erroresdetectados, la brecha significant entre el número predictedo de ordenes y las órdenes reales y la posibilidad que los elementos que realizan estas operaciones tengan alguna falla en su funcionamiento.

**Recomendaciones** 
Para abordar estos problemas se recomienda: 
**Desarrollar un sistema más preciso:** La implementación de algoritmos avanzados y técnicas de aprendizaje automático.

**Validar la información prioralmente:** Para asegurarse que las órdenes sean validadas antes de implementarse en el sistema.

**Diseñar un sistema de alerta para errores:** Para detectar los posibles errores antes de que afecten al público. 

**Entrenar a los trabajadores:** sobre la importancia de los datos precisos y cómo identificar errores cuando ocurren.

---
El informe generado incluyó:

- Resumen ejecutivo del estado del sistema.
- Análisis de órdenes procesadas y pendientes.
- Evaluación de posibles problemas operativos.
- Identificación de riesgos.
- Recomendaciones técnicas para mejorar el funcionamiento de la plataforma.

La generación exitosa de este informe confirmó el correcto funcionamiento de la integración entre la aplicación y el servicio LLM proporcionado por los docentes.

### Generación de informes

Los informes generados incluyen:

- Resumen ejecutivo.
- Estado general del sistema.
- Problemas detectados.
- Riesgos operativos.
- Recomendaciones técnicas.

Todos los informes quedan almacenados en la tabla `Informes` para su posterior consulta y auditoría.
