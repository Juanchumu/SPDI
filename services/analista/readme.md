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
  "id": 1,
  "created_at": "2026-06-02T20:47:40.623231",
  "contenido": "Resumen Ejecutivo, Estado General del Sistema, Problemas Detectados, Riesgos y Recomendaciones."
}
```

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
