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


@app.post("/orden")
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


@app.get("/orden/{id}")
def obtener_orden(id: int, db: Session = Depends(get_db)):
    orden = db.query(Orden).filter(Orden.id == id).first()
    if not orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    return orden


@app.get("/products")
def get_products(db: Session = Depends(get_db)):
    productos = db.query(Product).all()
    return productos


@app.get("/downloads")
def get_downloads(db: Session = Depends(get_db)):
    downloads = db.query(Download).all()
    return downloads


@app.get("/downloads/{product_id}")
def check_download(product_id: str, db: Session = Depends(get_db)):
    download = db.query(Download).filter(Download.product_id == product_id).first()
    if download:
        return {"status": "downloaded", "data": download}
    else:
        return {"status": "not_downloaded"}
