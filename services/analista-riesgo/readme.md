este worker genera un informe sobre un cliente, en particular, y analisa que tan riesgoso es
asegurarlo.

ya que puede haber clientes que con un unico punto no ocupe toda el area del mismo 

el informe es utilizando como minimo 1 punto. 

+
se le pasan las predicciones "predicha" del cliente.

+ 
se le pasa una descripcion del cliente, el cual se tiene que anotar al dar de alta:

[
la descripcion se puede sacar de descripcion de la tabla: 
# si el estado es: requerido | listo 
class InformesRiesgo(Base):
    __tablename__ = "informesriesgo"
    id = Column(Integer, primary_key=True)
    responsable = Column(Text)
    cliente = Column(Text)
    descripcion = Column(Text)
    estado = Column(Text)
    contenido = Column(Text) 
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime,server_default=func.now(),onupdate=func.now())
    
 ]

en la descripcion puede que no haya nada o si haya algo: 
cuanto personal posee | esto es para saber si el cliente posee la capacidad de prepararse para un incendio 
si utiliza agua de pozo o tiene una laguna cerca, si tiene una cantidad inmensa de arboles ..etc

--------
esto crea un informe personalizado de si conviene ono asegurarlo.


-------

si se considera tomar al cliente, se lo da de alta en el sistema, asi puede acceder a su estado.
->>>> esto genera un informe personalizado para ese cliente


----------------------------------------------------------



----



curl -X POST "http://localhost:8000/api/v1/informes/riesgo" \
-H "Content-Type: application/json" \
-d '{
  "responsable": "ricardo",
  "cliente": "Acme Seguros",
  "descripcion": "Cliente ubicado en zona con antecedentes de incendios forestales"
}'

id | responsable | cliente | estado | contenido | descripcion | created_at | updated_at 



 curl -X GET "http://localhost:8000/api/v1/informes/riesgo/2"
{"id":2,"responsable":"ricardo","cliente":"juan","estado":"listo","contenido":"## Informe de Riesgo de Asegurabilidad\n\n**Cliente:** Juan\n\n**Ubicación:** Zona con antecedentes de incendios forestales (Lat: -34.9118363580797, Lon: -59.83016967773438)\n\n**Fecha del Informe:** 26 de Octubre de 2023\n\n---\n\n### Resumen Ejecutivo\n\nEste informe evalúa la asegurabilidad del cliente Juan, ubicado en una zona con un historial significativo de riesgo de incendios forestales. Las predicciones disponibles indican zonas de alto riesgo concentradas, combinadas con la presencia de áreas de alto riesgo identificadas en predicciones anteriores.  Aunque las predicciones recientes muestran un bajo riesgo general, la existencia de focos críticos y el historial de la zona plantean serias preocupaciones que requieren una evaluación detallada antes de recomendar una cobertura completa. Se recomienda solicitar información adicional para comprender mejor los factores específicos del cliente y las posibles medidas de mitigación.\n\n### Análisis de Predicciones\n\nEl análisis de las predicciones disponibles revela un panorama mixto:\n\n* **Predicciones Recientes (2026-06-12):** Las tres predicciones de este día indican un riesgo \"bajo\" con porcentajes de área de riesgo muy bajos y sin zonas críticas. Este es un dato positivo que sugiere una situación actual relativamente tranquila en términos de riesgo de incendio. Los modelos XGBoost se muestran consistentemente precisos en la evaluación del riesgo bajo estas condiciones.\n* **Predicción de Alto Riesgo (2026-06-12):**  Una predicción a una ubicación cercana (-34.905642327699454, -59.91256713867188) el 12 de junio de 2026 identifica un área con un riesgo \"alto\" (100%) y una ocupación significativa de 43056 píxeles.  Este resultado es preocupante debido a la alta probabilidad e intensidad del riesgo, sugiriendo vulnerabilidades significativas en esta sección específica. El uso del modelo “fire_model_ver_2” indica un enfoque más operativo y posiblemente alerta sobre condiciones peligrosas inmediatas.\n* **Predicciones Anteriores (2026-06-10):**  Dos predicciones anteriores, también utilizando el modelo \"fire_model_ver_2\", revelan áreas de riesgo \"alto\" (100%) con alta ocupación de píxeles en distintos puntos del área. Esto refuerza la preocupación por la persistencia de las condiciones peligrosas y la necesidad de una evaluación más granular.\n\nEn conjunto, estas predicciones indican que el cliente Juan se encuentra operando dentro de un área con históricamente altos riesgos de incendios forestales,  con focos críticos altamente concentrados en ciertas ubicaciones, como evidenciado por los datos del 12 de Junio.\n\n### Factores Atenuantes\n\n* **Ubicación:** Aunque la ubicación es vulnerable a incendios forestales, no podemos obtener información sobre las características específicas del terreno o vegetación que podrían influir en el riesgo.\n* **Ausencia de Datos Concretos:**  La falta de información sobre medidas de mitigación implementadas por Juan (equipamiento preventivo, gestión de vegetación, etc.) dificulta una evaluación precisa de los factores protectores, así como la disponibilidad de recursos locales para combatir incendios.\n\n### Factores Agravantes\n\n* **Antecedentes de Incendios Forestales:** El cliente se encuentra ubicado en una zona con \"antecedentes de incendios forestales\", un factor clave que indica una alta probabilidad y potencial severidad del riesgo.\n* **Predicciones de Alto Riesgo:** La presencia de predicciones con un riesgo “alto” (100%) y zonas críticas significativas es, sin duda, el factor agravante más importante.\n* **Potencial Vegetación Abundante:**  La localización en una zona con antecedentes de incendios forestales implica que la vegetación local puede ser abundante, y por lo tanto la rápida propagación del fuego sería más probable.\n\n### Evaluación General\n\n**Nivel de Riesgo: Alto**\n\nEl alto nivel global del riesgo se debe principalmente a las predicciones de alta intensidad y distribución geográfica específica de áreas críticas para incendios forestales. Aunque las prediciciones recientes muestran un bajo riesgo general, no eliminan la amenaza constante representada por los focos críticos identificados en los modelos de vigilancia. La información disponible sugiere la necesidad de una prudencia considerable.\n\n### Recomendación para la Aseguradora\n\n**Conviene asegurar con condiciones especiales.**  La cobertura básica sería demasiado arriesgada ante este perfil de riesgo. Se recomienda ofrecer un esquema de seguro que incorpore las siguientes condiciones:\n\n* **Análisis de Riesgo Ampliado:** Una evaluación detallada de las características específicas de la propiedad (tipo de construcción, materiales, vulnerabilidad a la radiación térmica, etc.)\n* **Cláusulas de Exclusión Específicas:**  Excluir explícitamente el riesgo de incendios forestales.\n* **Revisión Periódica:** Establecer un programa de revisión periódica de las predicciones y condiciones para ajustar la cobertura según sea necesario .\n\n**Justificación:** Debido al alto nivel de riesgo inherente a la ubicación, la cobertura del seguro estándar no sería suficiente para proteger adecuadamente los intereses de la compañía aseguradora. Se deben considerar medidas adicionales que reflejen el potencial impacto financiero de un incendio forestal. La exigencia de condiciones especiales asegura el manejo apropiado del riesgo y la protección de los activos\n\n---\nFin del Informe.","descripcion":"## Informe de Riesgo de Asegurabilidad\n\n**Cliente:** Juan\n\n**Ubicación:** Zona con antecedentes de incendios forestales (Lat: -34.9118363580797, Lon: -59.83016967773438)\n\n**Fecha del Informe:** 26 de Octubre de 2023\n\n---\n\n### Resumen Ejecutivo\n\nEste informe evalúa la asegurabilidad del cliente Juan, ubicado en una zona con un historial significativo de riesgo de incendios forestales. Las predicciones disponibles indican zonas de alto riesgo concentradas, combinadas con la presencia de áreas de alto riesgo identificadas en predicciones anteriores.  Aunque las predicciones recientes muestran un bajo riesgo general, la existencia de focos críticos y el historial de la zona plantean serias preocupaciones que requieren una evaluación detallada antes de recomendar una cobertura completa. Se recomienda solicitar información adicional para comprender mejor los factores específicos del cliente y las posibles medidas de mitigación.\n\n### Análisis de Predicciones\n\nEl análisis de las predicciones disponibles revela un panorama mixto:\n\n* **Predicciones Recientes (2026-06-12):** Las tres predicciones de este día indican un riesgo \"bajo\" con porcentajes de área de riesgo muy bajos y sin zonas críticas. Este es un dato positivo que sugiere una situación actual relativamente tranquila en términos de riesgo de incendio. Los modelos XGBoost se muestran consistentemente precisos en la evaluación del riesgo bajo estas condiciones.\n* **Predicción de Alto Riesgo (2026-06-12):**  Una predicción a una ubicación cercana (-34.905642327699454, -59.91256713867188) el 12 de junio de 2026 identifica un área con un riesgo \"alto\" (100%) y una ocupación significativa de 43056 píxeles.  Este resultado es preocupante debido a la alta probabilidad e intensidad del riesgo, sugiriendo vulnerabilidades significativas en esta sección específica. El uso del modelo “fire_model_ver_2” indica un enfoque más operativo y posiblemente alerta sobre condiciones peligrosas inmediatas.\n* **Predicciones Anteriores (2026-06-10):**  Dos predicciones anteriores, también utilizando el modelo \"fire_model_ver_2\", revelan áreas de riesgo \"alto\" (100%) con alta ocupación de píxeles en distintos puntos del área. Esto refuerza la preocupación por la persistencia de las condiciones peligrosas y la necesidad de una evaluación más granular.\n\nEn conjunto, estas predicciones indican que el cliente Juan se encuentra operando dentro de un área con históricamente altos riesgos de incendios forestales,  con focos críticos altamente concentrados en ciertas ubicaciones, como evidenciado por los datos del 12 de Junio.\n\n### Factores Atenuantes\n\n* **Ubicación:** Aunque la ubicación es vulnerable a incendios forestales, no podemos obtener información sobre las características específicas del terreno o vegetación que podrían influir en el riesgo.\n* **Ausencia de Datos Concretos:**  La falta de información sobre medidas de mitigación implementadas por Juan (equipamiento preventivo, gestión de vegetación, etc.) dificulta una evaluación precisa de los factores protectores, así como la disponibilidad de recursos locales para combatir incendios.\n\n### Factores Agravantes\n\n* **Antecedentes de Incendios Forestales:** El cliente se encuentra ubicado en una zona con \"antecedentes de incendios forestales\", un factor clave que indica una alta probabilidad y potencial severidad del riesgo.\n* **Predicciones de Alto Riesgo:** La presencia de predicciones con un riesgo “alto” (100%) y zonas críticas significativas es, sin duda, el factor agravante más importante.\n* **Potencial Vegetación Abundante:**  La localización en una zona con antecedentes de incendios forestales implica que la vegetación local puede ser abundante, y por lo tanto la rápida propagación del fuego sería más probable.\n\n### Evaluación General\n\n**Nivel de Riesgo: Alto**\n\nEl alto nivel global del riesgo se debe principalmente a las predicciones de alta intensidad y distribución geográfica específica de áreas críticas para incendios forestales. Aunque las prediciciones recientes muestran un bajo riesgo general, no eliminan la amenaza constante representada por los focos críticos identificados en los modelos de vigilancia. La información disponible sugiere la necesidad de una prudencia considerable.\n\n### Recomendación para la Aseguradora\n\n**Conviene asegurar con condiciones especiales.**  La cobertura básica sería demasiado arriesgada ante este perfil de riesgo. Se recomienda ofrecer un esquema de seguro que incorpore las siguientes condiciones:\n\n* **Análisis de Riesgo Ampliado:** Una evaluación detallada de las características específicas de la propiedad (tipo de construcción, materiales, vulnerabilidad a la radiación térmica, etc.)\n* **Cláusulas de Exclusión Específicas:**  Excluir explícitamente el riesgo de incendios forestales.\n* **Revisión Periódica:** Establecer un programa de revisión periódica de las predicciones y condiciones para ajustar la cobertura según sea necesario .\n\n**Justificación:** Debido al alto nivel de riesgo inherente a la ubicación, la cobertura del seguro estándar no sería suficiente para proteger adecuadamente los intereses de la compañía aseguradora. Se deben considerar medidas adicionales que reflejen el potencial impacto financiero de un incendio forestal. La exigencia de condiciones especiales asegura el manejo apropiado del riesgo y la protección de los activos\n\n---\nFin del Informe.","created_at":"2026-06-17T22:07:58.316585","updated_at":"2026-06-17T22:10:15.125646"}




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
