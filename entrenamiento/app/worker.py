import time
import json
from sqlalchemy.orm import Session

from .db import SessionLocal
#from app.db import SessionLocal
from app.models import Orden
from app import script
import os


def get_pending(db: Session):
    return db.query(Orden).filter(Orden.status == "pending").first()


def run():
    while True:
        db = SessionLocal()

        orden = get_pending(db)

        if orden:
            # marcar como processing esto deberia ser un try para evitar pisarse con
            # otro worker
            orden.status = "processing"
            db.commit()

            args = json.loads(orden.args)

            try:
                os.system("python generador.py")
                orden.status = "lista-para-entrenar"
                #orden.ruta_safe = ruta_safe
                #orden.ruta_stack = ruta_stack

            except Exception as e:
                orden.status = "error"
                print(f"Error: {e}")

            db.commit()

        db.close()
        time.sleep(5)


if __name__ == "__main__":
    run()
