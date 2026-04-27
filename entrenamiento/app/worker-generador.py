import time
import json
from sqlalchemy.orm import Session

from .db import SessionLocal
#from app.db import SessionLocal
from app.models import Entrenamientos
from app import script
import os

def get_pending(db: Session):
    return db.query(Entrenamientos).filter(Entrenamientos.status == "pending").first()

def run():
    while True:
        db = SessionLocal()

        entrenamiento = get_pending(db)

        if entrenamiento:
            # marcar como processing esto deberia ser un try para evitar pisarse con
            # otro worker
            entrenamiento.status = "processing"
            db.commit()

            args = json.loads(orden.args)

            try:
                #os.system("python /app/app/generador.py")
                entrenamiento.status = "lista-para-entrenar"
            except Exception as e:
                entrenamiento.status = "error"
                print(f"Error: {e}")
            db.commit()

        db.close()
        time.sleep(5)


if __name__ == "__main__":
    run()
