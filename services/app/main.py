from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
import json

from app.db import SessionLocal
from app.models import Orden, Product, Download

app = FastAPI()

class EntrenamientoRequest(BaseModel):
    dia: int          # formato YYYYMMDD
    lat: float
    lon: float 

class OrdenRequest(BaseModel):
    dia: int          # formato YYYYMMDD
    lat: float
    lot: float


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
        status="pending"
    )
    
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    
    return {"id": nueva.id, "status": "pending"}


@app.get("/api/v1/orden/{id}")
def obtener_orden(id: int, db: Session = Depends(get_db)):
    orden = db.query(Orden).filter(Orden.id == id).first()
    respuesta = f'Estado: {orden.status}'
    if not orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    if (orden.status = 'done'):
        respuesta = orden.prediccion
    return respuesta



@app.post("/api/v1/generar_datos")
def generar_datos(request: EntrenamientoRequest, db: Session = Depends(get_db)):
    dia_str = str(request.dia)
    args = {
        "dia": dia_str, #Dia que hubo un incendio
        "lat": request.lat,
        "lon": request.lon
        }
    nueva = Entrenamientos(
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
    respuesta = f'Estado: {entrenamientos.status}'
    if not orden:
        raise HTTPException(status_code=404, detail="Generador no encontrado")
    if (orden.status == 'done'):
        respuesta = "Almacenado"
    return respuesta


