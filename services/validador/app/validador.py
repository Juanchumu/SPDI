import time
import json
from sqlalchemy.orm import Session

from db.db import SessionLocal
from db.models import Orden
from app import scriptms


def get_pending(db: Session):
    return db.query(Orden).filter(Orden.status == "Pendiente..").first()


def run():
    while True:
        db = SessionLocal()

        orden = get_pending(db)

        if orden:
            # marcar como processing
            orden.status = "Validando.."
            db.commit()
            args = json.loads(orden.args)

            try:
                # ejecutar script con los 3 argumentos + orden_id
                resultado = scriptms.run(
                        dia_de_la_imagen=args.get("dia_de_la_imagen"),
                        lat=args.get("lat"),
                        lon=args.get("lon"),
                        orden_id=orden.id)
                if (resultado == 1):
                    print("Error en la Fecha")
                    #aca tendria que hacer vuelta atras 
                    orden.status = "Error en la fecha..."
                    db.commit()
                    db.close()
                    time.sleep(5)
                    continue
                if (resultado == 2):
                    print("Error en las coordenadas")
                    #aca tendria que hacer vuelta atras 
                    orden.status = "Error en las coordenadas..."
                    db.commit()
                    db.close()
                    time.sleep(5)
                    continue

                orden.status = "Lista para el worker.."
            except Exception as e:
                orden.status = "error"
                print(f"Error: {e}")

            db.commit()

        db.close()
        time.sleep(5)


if __name__ == "__main__":
    run()
