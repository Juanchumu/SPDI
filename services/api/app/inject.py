import os
import json
from minio import Minio
from sqlalchemy.orm import Session
from db.db import SessionLocal, engine, Base
from db.models import Modelos

def inject_model():
    print("Conectando a la DB para asegurar que las tablas existan...")
    # Asegurar que las tablas existan (por si acaso no corrió crearDB.py)
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    # Datos del modelo XGBoost
    modelo_path_local = "/tmp/xgb_test_model.json"
    nombre_modelo = "xgb_test_model.json"
    
    if not os.path.exists(modelo_path_local):
        print(f"Error: No se encontró el modelo en {modelo_path_local}")
        return

    print("Conectando a MinIO...")
    # Subir a MinIO
    client = Minio(
        "minio:9000",
        access_key=os.getenv("DB_MINIO_USER", "admin"),
        secret_key=os.getenv("DB_MINIO_PASS", "Masterkey2026"),
        secure=False
    )
    
    if not client.bucket_exists("modelos"):
        client.make_bucket("modelos")
        
    client.fput_object(
        "modelos",
        nombre_modelo,
        modelo_path_local
    )
    print(f"Modelo subido a MinIO: modelos/{nombre_modelo}")

    print("Insertando registro en PostgreSQL...")
    # Crear registro en la BD
    nuevo_modelo = Modelos(
        name=nombre_modelo,
        tipo="xgboost",
        final_loss=0.01,
        best_loss=0.01,
        pred_mean=0.5,
        pred_min=0.0,
        pred_max=1.0,
        accuracy=0.98,
        precision=0.98,
        recall=0.98,
        f1_score=0.98,
        iou=0.96,
        dice=0.98,
        dataset_size=60000
    )
    db.add(nuevo_modelo)
    db.commit()
    db.close()
    
    print("¡Modelo XGBoost inyectado con éxito!")

if __name__ == "__main__":
    inject_model()
