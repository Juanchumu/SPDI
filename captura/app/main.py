from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
import json

from app.db import SessionLocal
from app.models import Orden, Product, Download

app = FastAPI()


class OrdenRequest(BaseModel):
    dia: int          # formato YYYYMMDD
    izquierda: float
    derecha: float
    abajo: float
    arriba: float


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
        "izquierda": request.izquierda,
        "derecha": request.derecha,
        "abajo": request.abajo,
        "arriba": request.arriba
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


