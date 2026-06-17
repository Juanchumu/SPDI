from sqlalchemy.orm import Session
from db.db import SessionLocal
from db.models import InformesRiesgo, Orden
from datetime import datetime
import json
import time
from openai import OpenAI
import os

OLLAMA_URL = os.getenv("OLLAMA_URL_A")
OLLAMA_TOKEN = os.getenv("OLLAMA_TOKEN")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL_A")

client = OpenAI(
    base_url=OLLAMA_URL,
    api_key=OLLAMA_TOKEN
)

# ==================================================
# Busca un informe de riesgo pendiente
# ==================================================
def obtener_requerido(db: Session):
    return (
        db.query(InformesRiesgo)
        .filter(InformesRiesgo.estado == "requerido")
        .order_by(InformesRiesgo.created_at.asc())
        .first()
    )

# ==================================================
# Busca todas las predicciones del cliente
# ==================================================
def obtener_predicciones_cliente(db: Session, username: str):
    return (
        db.query(Orden)
        .filter(
            Orden.username == username,
            Orden.status == "Predicha"
        )
        .order_by(Orden.created_at.desc())
        .all()
    )

# ==================================================
# Convierte las predicciones a un formato simple
# ==================================================
def serializar_predicciones(predicciones):
    resultado = []

    for pred in predicciones:
        try:
            resultado.append({
                "fecha": pred.created_at.isoformat() if pred.created_at else None,
                "args": json.loads(pred.args),
                "prediccion": json.loads(pred.prediccion),
                "modelo": pred.modelo_utilizado
            })
        except Exception:
            continue

    return resultado

# ==================================================
# Genera informe de asegurabilidad
# ==================================================
def generar_informe(cliente, descripcion, predicciones):

    prompt = f"""
Sos un analista de riesgos de una compañía aseguradora.

Tu tarea es evaluar si conviene asegurar a un cliente teniendo en cuenta:

1. Las predicciones históricas disponibles.
2. La descripción del cliente.
3. Los factores que puedan ayudar o dificultar la prevención y combate de incendios.

Cliente:
{cliente}

Descripción:
{descripcion if descripcion else "No se proporcionó descripción adicional."}

Predicciones:
{json.dumps(predicciones, indent=2)}

Indicaciones:

- El informe puede basarse en una única predicción.
- Si existen varias predicciones, analizarlas en conjunto.
- Una única ubicación puede no representar toda la superficie asegurada.
- Considerar factores positivos:
    * Disponibilidad de personal.
    * Pozos, lagunas o reservorios de agua.
    * Infraestructura de acceso.
    * Equipamiento preventivo.
    * Medidas de mitigación.

- Considerar factores negativos:
    * Vegetación abundante.
    * Riesgos elevados repetidos.
    * Escasez de personal.
    * Falta de acceso a agua.
    * Ubicación aislada.
    * Falta de medidas preventivas.

Generar:

# Informe de Riesgo de Asegurabilidad

## Resumen Ejecutivo

## Análisis de Predicciones

## Factores Atenuantes

## Factores Agravantes

## Evaluación General
Clasificar:
- Bajo
- Medio
- Alto

## Recomendación para la Aseguradora

Elegir una:

- Conviene asegurar.
- Conviene asegurar con condiciones especiales.
- Conviene solicitar información adicional.
- No se recomienda asegurar actualmente.

Justificar la decisión.

No inventar información.
Utilizar lenguaje profesional.
"""

    respuesta = client.chat.completions.create(
        model=OLLAMA_MODEL,
        messages=[
            {
                "role": "system",
                "content": "Sos un analista senior de riesgos para compañías aseguradoras."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        timeout=300
    )

    return respuesta.choices[0].message.content

# ==================================================
# Worker principal
# ==================================================
def run():

    while True:

        db = SessionLocal()

        try:

            informe = obtener_requerido(db)

            if informe is None:
                print("No hay informes de riesgo pendientes.")
                time.sleep(60)
                continue

            print(
                f"Generando informe de riesgo para {informe.cliente}"
            )

            predicciones = obtener_predicciones_cliente(
                db,
                informe.responsable
            )

            if len(predicciones) == 0:
                print(
                    "No existen predicciones para analizar."
                )
                time.sleep(60)
                continue

            predicciones_serializadas = serializar_predicciones(
                predicciones
            )

            texto = generar_informe(
                informe.cliente,
                informe.descripcion,
                predicciones_serializadas
            )

            informe.contenido = texto
            informe.estado = "listo"
            informe.updated_at = datetime.utcnow()

            db.commit()

            print(
                f"Informe de riesgo generado para {informe.cliente}"
            )

        except Exception as e:

            db.rollback()
            print(
                f"Error generando informe de riesgo: {e}"
            )

        finally:

            db.close()

        time.sleep(10)


if __name__ == "__main__":
    run()
