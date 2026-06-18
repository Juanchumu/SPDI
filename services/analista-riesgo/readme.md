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

Los Endpoints utilizados:

curl -X POST "http://localhost:8000/api/v1/informes/riesgo" \
-H "Content-Type: application/json" \
-d '{
  "responsable": "ricardo",
  "cliente": "Acme Seguros",
  "descripcion": "Cliente ubicado en zona con antecedentes de incendios forestales"
}'

curl -X GET "http://localhost:8000/api/v1/informes/riesgo/3"
{"id":3,"responsable":"ricardo","cliente":"juan","estado":"listo","contenido":"

## Informe de Riesgo de Asegurabilidad - Juan

**Factores Agravantes:**La presencia de zonas críticas de alto riesgo (predicciones “alto”) en la proximidad del cliente, junto con la reiteración de estos riesgos, es un factor preocupante. La ubicación específica también presenta vegetación abundante, lo que incrementa el potencial de propagación de incendios.

**Evaluación General:** Alto

**Recomendación para la Aseguradora:** Conviene solicitar información adicional. Es crucial conocer las medidas de prevención implementadas por el cliente (equipamiento, personal, acceso a agua) y la disponibilidad de recursos en caso de un incendio.  Se requiere una evaluación más profunda antes de considerar cualquier cobertura.

"descripcion":"
## Informe de Riesgo de Asegurabilidad - Juan

**Factores Agravantes:** La presencia de zonas críticas de alto riesgo (predicciones “alto”) en la proximidad del cliente, junto con la reiteración de estos riesgos, es un factor preocupante. La ubicación específica también presenta vegetación abundante, lo que incrementa el potencial de propagación de incendios.

**Evaluación General:** Alto

**Recomendación para la Aseguradora:** Conviene solicitar información adicional. Es crucial conocer las medidas de prevención implementadas por el cliente (equipamiento, personal, acceso a agua) y la disponibilidad de recursos en caso de un incendio.  Se requiere una evaluación más profunda antes de considerar cualquier cobertura."

,"created_at":"2026-06-17T22:42:08.280635"
,"updated_at":"2026-06-17T22:43:34.131516"}

## Servicio de generación de informes de riesgo de asegurabilidad

Este worker genera informes automáticos de evaluación de riesgo para clientes potenciales de una aseguradora utilizando un modelo de lenguaje (LLM).

Su objetivo es asistir al personal de análisis de riesgo durante el proceso de suscripción de pólizas, proporcionando una evaluación técnica sobre la conveniencia de asegurar a un cliente en función de su exposición a incendios y de su capacidad para prevenir o mitigar dichos eventos.

### ¿Cómo funciona?

Cuando se registra una nueva solicitud de evaluación:

1. Se crea un registro en la tabla `InformesRiesgo`.
2. Se recupera la descripción asociada al cliente.
3. Se obtienen las predicciones de incendios vinculadas al cliente.
4. Toda la información es enviada al modelo de lenguaje.
5. El modelo analiza:

   * Predicciones históricas y actuales.
   * Riesgo observado en las distintas ubicaciones disponibles.
   * Características operativas del cliente.
   * Factores atenuantes y agravantes.
6. Se genera un informe técnico estructurado.
7. El resultado queda almacenado en la tabla `InformesRiesgo`.

### Información analizada

El informe se construye utilizando dos fuentes principales de información.

#### Predicciones de incendios

El sistema analiza una o más predicciones asociadas al cliente.

Las predicciones permiten evaluar:

* Nivel de riesgo detectado.
* Persistencia del riesgo en el tiempo.
* Existencia de zonas críticas.
* Concentración geográfica del riesgo.
* Historial reciente de eventos.

El análisis puede realizarse utilizando una única predicción o varias predicciones en conjunto.

Una única ubicación no necesariamente representa toda la superficie asegurada, por lo que el modelo considera la información disponible como una muestra del área de interés.

#### Descripción del cliente

La descripción es ingresada por el analista al momento de solicitar el informe.

Puede contener información como:

* Cantidad de personal disponible.
* Existencia de pozos de agua.
* Presencia de lagunas o reservorios.
* Infraestructura de acceso.
* Equipamiento preventivo.
* Medidas de mitigación implementadas.
* Características de la vegetación.
* Condiciones operativas relevantes.

Esta información permite complementar las predicciones con factores reales que afectan la capacidad de respuesta ante incendios.

### Criterios de evaluación

Durante el análisis se consideran distintos factores.

#### Factores atenuantes

Elementos que podrían reducir el riesgo o facilitar la respuesta ante un incendio:

* Disponibilidad de personal.
* Pozos, lagunas o reservorios de agua.
* Infraestructura de acceso adecuada.
* Equipamiento preventivo.
* Medidas de mitigación implementadas.

#### Factores agravantes

Elementos que podrían incrementar el riesgo:

* Vegetación abundante.
* Predicciones reiteradas de riesgo elevado.
* Escasez de personal.
* Falta de acceso a fuentes de agua.
* Ubicaciones aisladas.
* Ausencia de medidas preventivas.

### Backend LLM

El proyecto utiliza un servicio remoto compatible con la API de OpenAI.

La infraestructura es provista por los docentes de la materia mediante una URL y un token de acceso. El worker consume dicho servicio para generar los informes automáticos.

### Modelo utilizado

```text
llama3.2:3b
```

### Variables de entorno requeridas

| Variable       | Descripción                                      |
| -------------- | ------------------------------------------------ |
| `OLLAMA_URL_A` | URL del servidor LLM compartido por los docentes |
| `OLLAMA_TOKEN` | Token de autenticación para acceder al servicio  |

### Estructura de los informes

Todos los informes siguen la siguiente estructura:

```md
# Informe de Riesgo de Asegurabilidad

## Resumen Ejecutivo

## Análisis de Predicciones

## Factores Atenuantes

## Factores Agravantes

## Evaluación General

Nivel de Riesgo:
- Bajo
- Medio
- Alto

## Recomendación para la Aseguradora
```

### Posibles recomendaciones

El modelo debe seleccionar una de las siguientes opciones:

* Conviene asegurar.
* Conviene asegurar con condiciones especiales.
* Conviene solicitar información adicional.
* No se recomienda asegurar actualmente.

Todas las recomendaciones deben estar justificadas utilizando exclusivamente la información disponible.

### Restricciones del análisis

El modelo tiene instrucciones explícitas para:

* No inventar información.
* Utilizar únicamente las predicciones y la descripción proporcionadas.
* Mantener lenguaje profesional.
* Reconocer cuando la información disponible es insuficiente.
* Solicitar información adicional cuando corresponda.

### Objetivo del módulo

Este componente busca reducir el tiempo de análisis de nuevos clientes y brindar una evaluación homogénea basada en evidencia objetiva.

Los informes generados ayudan a los analistas a comprender rápidamente el nivel de exposición al riesgo de incendios y la capacidad operativa del cliente para prevenir o mitigar eventos adversos.

Todos los informes quedan almacenados en la tabla `InformesRiesgo` para su posterior consulta, auditoría y seguimiento.

