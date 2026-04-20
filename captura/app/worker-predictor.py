import time
import json
from sqlalchemy.orm import Session

from .db import SessionLocal
#from app.db import SessionLocal
from app.models import Orden
from app import script


def get_pending(db: Session):
    return db.query(Orden).filter(Orden.status == "predict-ready").first()


def run():
    while True:
        db = SessionLocal()
        orden = get_pending(db)
        if orden:
            # marcar como predicting
            orden.status = "predicting"
            db.commit()
            args = json.loads(orden.args)

            try:
                #Modelo.Predecir(orden.ruta_stack) todavia no hay modelo entrenado pero recibe el stack
                orden.status = "done"
                orden.prediccion = "Riesgo de Incendio Elevado"

            except Exception as e:
                orden.status = "error"
                print(f"Error: {e}")

            db.commit()

        db.close()
        time.sleep(5)


if __name__ == "__main__":
    run()
