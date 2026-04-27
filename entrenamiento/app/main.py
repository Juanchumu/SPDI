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
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/api/v1/generar_datos")
def generar_datos(request: OrdenRequest, db: Session = Depends(get_db)):
    dia_str = str(request.dia)
    args = {
        "dia": dia_str,
        "tipo": "generacion_dataset",
        "version": "v1"
        }
    nueva = Orden(
        args=json.dumps(args),
        status="pending"
    )
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    
    return {"id": nueva.id, "status": "pending"}


@app.get("/api/v1/generar_datos/{id}")
def obtener_orden(id: int, db: Session = Depends(get_db)):
    orden = db.query(Orden).filter(Orden.id == id).first()
    respuesta = f'Estado: {orden.status}'
    if not orden:
        raise HTTPException(status_code=404, detail="Generador no encontrado")
    if (orden.status == 'done'):
        respuesta = orden.prediccion
    return respuesta


