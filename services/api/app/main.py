from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
import json
import time
from datetime import timedelta

from db.db import SessionLocal
from db.models import Orden, Entrenamiento, Modelos, Descargas
import os


# Guardamos el timestamp al momento de cargar el script
START_TIME = time.time()

app = FastAPI()

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


@app.post("/api/v1/orden")
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
        respuesta = respuesta +"\n"+ orden.prediccion +"\n"+ "Modelo Utilizado:"+ orden.modelo_utilizado
    return respuesta



@app.post("/api/v1/generar_datos")
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

    return {"status_code": 200,
        "message": "Todo anda bien por acá.",
        "uptime": uptime_str
        }
