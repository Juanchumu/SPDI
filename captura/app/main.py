from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session, inspect
import json
import os

from app.db import engine


from app.db import SessionLocal
from app.models import Orden, Product, Download  # 👈 nuevos modelos

app = FastAPI()


# 🔌 DB session (única)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 🟢 Crear orden
@app.post("/orden")
def crear_orden(args: dict, db: Session = Depends(get_db)):
    nueva = Orden(
        args=json.dumps(args),
        status="pending"
    )

    db.add(nueva)
    db.commit()
    db.refresh(nueva)

    return {"id": nueva.id}


# 🔍 Consultar estado
@app.get("/orden/{id}")
def obtener_orden(id: int, db: Session = Depends(get_db)):
    orden = db.query(Orden).filter(Orden.id == id).first()
    return orden


# 📦 Productos disponibles
@app.get("/products")
def get_products(db: Session = Depends(get_db)):
    productos = db.query(Product).all()
    return productos


# 📥 Descargas realizadas
@app.get("/downloads")
def get_downloads(db: Session = Depends(get_db)):
    downloads = db.query(Download).all()
    return downloads


# 🔎 Estado de descarga
@app.get("/downloads/{product_id}")
def check_download(product_id: str, db: Session = Depends(get_db)):
    download = db.query(Download).filter(Download.product_id == product_id).first()

    if download:
        return {"status": "downloaded", "data": download}
    else:
        return {"status": "not_downloaded"}
