from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
import json
import os

#from app import generador
from app.db import SessionLocal
from app.models import Orden, Product, Download

app = FastAPI()


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

@app.post("/api/v1/generar_datos")
def generar_datos():
    os.system("python generador.py")
    return {"Generando...."}


@app.get("/api/v1/entrenamiento/{id}")
def obtener_orden(id: int, db: Session = Depends(get_db)):
    orden = db.query(Orden).filter(Orden.id == id).first()
    respuesta = f'Estado: {orden.status}'
    if not orden:
        raise HTTPException(status_code=404, detail="Entrenamiento no encontrado")
    if (orden.status == 'done'):
        respuesta = orden.prediccion
    return respuesta


