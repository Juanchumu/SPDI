import time
import json
from sqlalchemy.orm import Session

from datetime import datetime

from db.db import SessionLocal
#from app.db import SessionLocal
from db.models import Entrenamiento, WorkersLogs
from app import sems
import os

import traceback

# ==================================================
# logs de estado en la db (actualiza)
# ==================================================
def logearDB(descripcion):
    db = SessionLocal()
    try:
        registro = (
            db.query(WorkersLogs)
            .filter(WorkersLogs.name == "entrenador")
            .first()
        )
        if registro is None:
            registro = WorkersLogs(
                name="entrenador",
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




def get_pending(db: Session):
    return db.query(Entrenamiento).filter(Entrenamiento.status == "pending").first()

def upload_folder_to_minio(client, bucket, folder):
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)
    for root, _, files in os.walk(folder):
        for file in files:
            file_path = os.path.join(root, file)
            print(f"Subiendo {file} a {bucket}...")
            client.fput_object(bucket, file, file_path)

def check_minio_and_generate():
    from app.sems import get_minio_client
    from app import generate_dataset_from_shapes
    
    logearDB("Verificando dataset base en MinIO...")
    try:
        client = get_minio_client()
        bucket_name = "train-inputs"
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
        objects = list(client.list_objects(bucket_name))
        if len(objects) < 10:
            logearDB("Dataset base faltante. Iniciando regeneración desde shapefiles...")
            print("MinIO vacío o con menos de 10 escenas. Generando dataset desde shapefiles...")
            generate_dataset_from_shapes.download_and_generate()
            
            logearDB("Subiendo dataset regenerado a MinIO...")
            upload_folder_to_minio(client, "train-inputs", "/app/dataset/train/inputs")
            upload_folder_to_minio(client, "train-masks", "/app/dataset/train/masks")
            logearDB("Regeneración de dataset base completada.")
        else:
            logearDB("Dataset base OK en MinIO.")
    except Exception as e:
        print(f"Error verificando/generando dataset base: {e}")

def run():
    check_minio_and_generate()
    while True:
        db = SessionLocal()
        logearDB("Esperando nuevas ordenes de entrenamiento..")
        entrenamiento = get_pending(db)
        if entrenamiento:
            # marcar como processing esto deberia ser un try para evitar pisarse con
            # otro worker
            entrenamiento.status = "processing"
            logearDB("Procesando orden de entrenamiento..")
            db.commit()
            args = json.loads(entrenamiento.args)
            try:
                resultado = sems.run(
                        dia_de_la_imagen=args.get("dia"),
                        lat=args.get("lat"),
                        lon=args.get("lon"),
                        orden_id=entrenamiento.id)

                if (resultado == 1):
                    print("Fallo la la descarga de imagenes para entrenar")
                    #entonces se vuelve atras
                    entrenamiento.status = "pending"
                    db.commit()
                    db.close()
                    time.sleep(5)
                    continue

                #os.system("python /app/app/generador.py")
                entrenamiento.status = "lista-para-entrenar"
            except Exception as e:
                entrenamiento.status = "error"
                traceback.print_exc()
                print(f"Error: {e}")
            db.commit()

        db.close()
        time.sleep(5)

if __name__ == "__main__":
    run()
