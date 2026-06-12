from sqlalchemy.orm import Session
from db.db import SessionLocal
from db.models import InformesClientes, Orden
from datetime import datetime
import json
import time
from openai import OpenAI
import os

OLLAMA_URL = os.getenv("OLLAMA_URL_A")
OLLAMA_TOKEN = os.getenv("OLLAMA_TOKEN")

client = OpenAI(
    base_url=f"{OLLAMA_URL}/v1",
    api_key=OLLAMA_TOKEN
)

# ==================================================
# Busca un informe pendiente
# ==================================================
def obtener_requerido(db: Session):
    return (
        db.query(InformesClientes)
        .filter(InformesClientes.estado == "requerido")
        .order_by(InformesClientes.created_at.asc())
        .first()
    )

# ==================================================
# Busca la ultima prediccion del cliente
# ==================================================
def obtener_ultima_prediccion(db: Session, username: str):
    return (
        db.query(Orden)
        .filter(
            Orden.username == username,
            Orden.status == "Predicha"
        )
        .order_by(Orden.created_at.desc())
        .first()
    )

# ==================================================
# Genera el informe con IA
# ==================================================
def generar_informe(cliente, prediccion):
    datos_prediccion = json.loads(prediccion.prediccion)
    args = json.loads(prediccion.args)

    prompt = f"""
Sos un asesor de una compañía aseguradora.

Debes generar un aviso personalizado para el cliente.

Datos:

Cliente: {cliente}
Fecha analizada: {args.get('dia_de_la_imagen')}
Latitud: {args.get('lat')}
Longitud: {args.get('lon')}

Resultado de la predicción:
{json.dumps(datos_prediccion, indent=2)}

Reglas:

- Si el riesgo es alto, advertir al cliente que su zona presenta un riesgo elevado de incendio.
- Si el riesgo es medio, recomendar extremar precauciones.
- Si el riesgo es bajo, informar que el riesgo actual es bajo pero que igualmente debe mantener medidas preventivas.
- Explicar las recomendaciones con lenguaje simple.
- No usar lenguaje técnico.
- Máximo 250 palabras.
- Finalizar indicando que ante cualquier duda puede contactar a la empresa aseguradora para recibir asistencia y conocer los próximos pasos.
"""

    respuesta = client.chat.completions.create(
        model="llama3.2:1b",
        messages=[
            {
                "role": "system",
                "content": "Sos un asesor especializado en prevención de incendios."
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
                print("No hay informes requeridos. Durmiendo...")
                time.sleep(60)
                continue

            print(f"Generando informe para {informe.cliente}")

            prediccion = obtener_ultima_prediccion(
                db,
                informe.responsable
            )

            if prediccion is None:
                print("No se encontraron predicciones para el cliente.")
                time.sleep(60)
                continue

            texto = generar_informe(
                informe.cliente,
                prediccion
            )

            informe.contenido = texto
            informe.estado = "listo"
            informe.updated_at = datetime.utcnow()

            db.commit()

            print(f"Informe generado para {informe.cliente}")

        except Exception as e:
            db.rollback()
            print(f"Error: {e}")

        finally:
            db.close()

        time.sleep(10)


if __name__ == "__main__":
    run()
