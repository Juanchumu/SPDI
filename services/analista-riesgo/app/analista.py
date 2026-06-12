from sqlalchemy import func
from db.db import SessionLocal
from db.models import Orden, Modelos, WorkersLogs, InformesClientes
import time
from datetime import datetime

import json
from openai import OpenAI
import os

OLLAMA_URL = os.getenv("OLLAMA_URL_A")  # o B
OLLAMA_TOKEN = os.getenv("OLLAMA_TOKEN")

if not OLLAMA_URL:
    raise RuntimeError("OLLAMA_URL_A no configurada")

if not OLLAMA_TOKEN:
    raise RuntimeError("OLLAMA_TOKEN no configurada")

client = OpenAI(
    base_url=f"{OLLAMA_URL}/v1",
    api_key=OLLAMA_TOKEN
)



def recolectar_metricas():
    db = SessionLocal()
    try:
        total_ordenes = db.query(Orden).filter(Orden.cliente == 'cliente buscado' ).count()
        pendientes = db.query(Orden).filter(Orden.status == "Pendiente..").count()
        predichas = db.query(Orden).filter(Orden.status == "Predicha").count()
        errores = db.query(Orden).filter(Orden.status.like("Error%")).count()
        ultimo_modelo = (db.query(Modelos).order_by(Modelos.created_at.desc()).first())
        workers = db.query(WorkersLogs).all()
        return {
                "total_ordenes": total_ordenes,
                "pendientes": pendientes,
                "predichas": predichas,
                "errores": errores,
                "modelo": {
                    "name": ultimo_modelo.name if ultimo_modelo else None,
                    "final_loss": ultimo_modelo.final_loss if ultimo_modelo else None,
                    "accuracy": ultimo_modelo.accuracy if ultimo_modelo else None,
                    "precision": ultimo_modelo.precision if ultimo_modelo else None,
                    "recall": ultimo_modelo.recall if ultimo_modelo else None,
                    "f1_score": ultimo_modelo.f1_score if ultimo_modelo else None,
                    "iou": ultimo_modelo.iou if ultimo_modelo else None,
                    "dice": ultimo_modelo.dice if ultimo_modelo else None,
                    "dataset_size": ultimo_modelo.dataset_size if ultimo_modelo else None
                    },
                "workers": [{
                    "name": w.name,
                    "descripcion": w.descripcion
                    }for w in workers]
                }
    finally:
        db.close()

def generar_informe(metricas):
    prompt = f"""
Analiza el estado de las predicciones para un cliente.
Datos:

{json.dumps(metricas, indent=2)}

Genera:

1. Resumen claro.
4. Riesgos.
5. Recomendaciones.

La respuesta debe ser personalizada para el rubro del cliente, no muy tecnica. 
"""
    respuesta = client.chat.completions.create(
            model="llama3.2:1b",
            messages=[{
                "role": "system",
                "content": "Sos un revisador de predicciones."
                },{
                "role": "user",
                "content": prompt}],
             timeout=400
                )
    return respuesta.choices[0].message.content

def guardar_informe(texto):
    db = SessionLocal()
    try:
        informe = Informes(contenido=texto)
        db.add(informe)
        db.commit()
    finally:
        db.close()

# ==================================================
# logs de estado en la db (actualiza)
# ==================================================
def logearDB(descripcion):
    db = SessionLocal()
    try:
        registro = (
            db.query(WorkersLogs)
            .filter(WorkersLogs.name == "analista-clientes")
            .first()
        )
        if registro is None:
            registro = WorkersLogs(
                name="analista-clientes",
                descripcion=descripcion
            )
            db.add(registro)
        else:
            registro.descripcion = descripcion
            registro.updated_at = datetime.utcnow()
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error guardando heartbeat: {e}")
    finally:
        db.close()

def run():
    while True:
        print("Analista para Clientes UP!")
        logearDB("Iniciado.")
        #Para que no haga un informe apenas inicia la api 
        time.sleep(120)
        try:
            #tiene que buscar si hay ordenes de analisis para clientes 
            logearDB("Generando Reporte.")
            metricas = recolectar_metricas()
            informe = generar_informe(metricas)
            guardar_informe(informe)
            logearDB("Reporte Generado, me duermo.")
            print("Informe generado")
        except Exception as e:
            print(e)
            logearDB("No pude reportar, lo intentare la proxima.")
        time.sleep(300)

if __name__ == "__main__":
    run()
