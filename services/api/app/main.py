from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
import json
import time
import requests
from datetime import timedelta, datetime, timezone

from db.db import SessionLocal
from db.models import Orden, Entrenamiento, Modelos, Descargas, WorkersLogs
import os


# Guardamos el timestamp al momento de cargar el script
START_TIME = time.time()

app = FastAPI()


def minioVida():
    try:
        r = requests.get("http://minio:9000/minio/health/live",timeout=2)
        estado = "UP" if r.status_code == 200 else "DOWN"
        return estado 
    except Exception:
        return "DOWN"
def dbVida():
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        return "UP"
    except Exception as e:
        print(e)
        return "DOWN"
    finally:
        db.close()

def workerVida(nombre):
    db = SessionLocal()
    try:
        dato = (
            db.query(WorkersLogs)
            .filter(WorkersLogs.name == nombre)
            .order_by(WorkersLogs.id.desc())
            .first()
        )
        if dato is None:
            return {
                "status": "UNKNOWN",
                "descripcion": "Sin registros",
                "last_seen": None
            }
        #ahora = datetime.now(timezone.utc)
        ahora = datetime.utcnow()
        # Ajustá este valor según la frecuencia de heartbeat
        timeout = timedelta(seconds=30)
        if ahora - dato.updated_at > timeout:
            estado = "DOWN"
        else:
            estado = "UP"
        return {
            "status": estado,
            "descripcion": dato.descripcion,
            "last_seen": dato.updated_at.isoformat(),
            "seconds_since_last_heartbeat": int(
                (ahora - dato.updated_at).total_seconds()
            )
        }
    except Exception as e:
        print(e)
        return {
            "status": "ERROR",
            "descripcion": str(e),
            "last_seen": None
        }
    finally:
        db.close()

class EntrenamientoRequest(BaseModel):
    dia: int          # formato YYYYMMDD
    lat: float
    lon: float 

class OrdenRequest(BaseModel):
    dia: int          # formato YYYYMMDD
    lat: float
    lon: float


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/api/v1/orden", status_code=status.HTTP_201_CREATED)
def crear_orden(request: OrdenRequest, db: Session = Depends(get_db)):
    dia_str = str(request.dia)
    args = {
        "dia_de_la_imagen": dia_str,
        "lat": request.lat,
        "lon": request.lon,
    }
    nueva = Orden(
        args=json.dumps(args),
        status="Pendiente.."
    )
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    
    return {"id": nueva.id, "status": "Pendiente.."}


@app.get("/api/v1/orden/{id}")
def obtener_orden(id: int, db: Session = Depends(get_db)):
    orden = db.query(Orden).filter(Orden.id == id).first()

    if orden is None: 
        raise HTTPException(status_code=404, detail="Orden No encontrada")

    respuesta = f'Estado: {orden.status}'
    if (orden.status == 'Predicha'):
        respuesta = {
                "id": orden.id,
                "status": orden.status,
                "prediccion": orden.prediccion,
                "modelo_utilizado": orden.modelo_utilizado
                }
    return respuesta



@app.post("/api/v1/generar_datos", status_code=status.HTTP_201_CREATED)
def generar_datos(request: EntrenamientoRequest, db: Session = Depends(get_db)):
    dia_str = str(request.dia)
    args = {
        "dia": dia_str, #Dia que hubo un incendio
        "lat": request.lat,
        "lon": request.lon
        }
    nueva = Entrenamiento(
        args=json.dumps(args),
        status="pending"
    )
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    
    return {"id": nueva.id, "status": "pending"}


@app.get("/api/v1/generar_datos/{id}")
def obtener_entrenamiento(id: int, db: Session = Depends(get_db)):
    entrenamientos = db.query(Entrenamiento).filter(Entrenamiento.id == id).first()
    if entrenamientos is None: 
        raise HTTPException(status_code=404, detail="Entrenamiento no encontrado")

    respuesta = f'Estado: {entrenamientos.status}'
    return respuesta

@app.get("/api/v1/health")  # liveness
def health():
    # Calculamos cuánto tiempo pasó
    uptime_seconds = int(time.time() - START_TIME)
    # Formateamos a un formato legible (HH:MM:SS)
    uptime_str = str(timedelta(seconds=uptime_seconds))

    #return {"status_code": 200,"message": "Todo anda bien por acá.","uptime": uptime_str}
    respuesta = {
            "services": {
                "api": {
                    "status": "UP",
                    "uptime": uptime_str
                    },
                "worker": workerVida("worker"),
                "validador": workerVida("validador"),
                "entrenador": workerVida("entrenador"),
                "modelador":workerVida("modelador"),
                "predictor": workerVida("predictor"),
                },
            "dependencies": {
                "database": dbVida(),
                "minio": minioVida()
                }
            }
    return respuesta 


@app.get("/api/v1/modelos")
def listar_modelos(db: Session = Depends(get_db)):
    modelos = (
        db.query(Modelos)
        .order_by(Modelos.created_at.desc())
        .all()
    )
    if modelos is None:
        return {"Error":"No hay Modelos"}
    if len(modelos) < 1:
        return {"Error":"No hay Modelos"}
    return [{
        "id": modelo.id,
        "name": modelo.name,
        "final_loss": modelo.final_loss,
        "best_loss": modelo.best_loss,
        "pred_mean": modelo.pred_mean,
        "pred_min": modelo.pred_min,
        "pred_max": modelo.pred_max,
        "accuracy": modelo.accuracy,
        "precision": modelo.precision,
        "recall": modelo.recall,
        "f1_score": modelo.f1_score,
        "iou": modelo.iou,
        "dice": modelo.dice,
        "dataset_size": modelo.dataset_size,
        "created_at": modelo.created_at.isoformat() if modelo.created_at else None
        } for modelo in modelos ]
