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

def run():
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
