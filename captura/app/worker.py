import time
import json
from sqlalchemy.orm import Session

from .db import SessionLocal
#from app.db import SessionLocal
from app.models import Orden
from app import script


def get_pending(db: Session):
    return db.query(Orden).filter(Orden.status == "pending").first()


def run():
    while True:
        db = SessionLocal()

        orden = get_pending(db)

        if orden:
            # marcar como processing
            orden.status = "processing"
            db.commit()

            args = json.loads(orden.args)

            try:
                # ejecutar script con los 5 argumentos + orden_id
                ruta_safe, ruta_stack = script.run(
                    dia_de_la_imagen=args.get("dia_de_la_imagen"),
                    izquierda=args.get("izquierda"),
                    derecha=args.get("derecha"),
                    abajo=args.get("abajo"),
                    arriba=args.get("arriba"),
                    orden_id=orden.id
                )

                orden.status = "predict-ready"
                orden.ruta_safe = ruta_safe
                orden.ruta_stack = ruta_stack

            except Exception as e:
                orden.status = "error"
                print(f"Error: {e}")

            db.commit()

        db.close()
        time.sleep(5)


if __name__ == "__main__":
    run()
