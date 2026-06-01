import time
import json
from sqlalchemy.orm import Session

from db.db import SessionLocal
#from app.db import SessionLocal
from db.models import Orden, WorkersLogs
from app import scriptms


# ==================================================
# logs de estado en la db (actualiza)
# ==================================================
def logearDB(descripcion):
    db = SessionLocal()
    try:
        registro = (
            db.query(WorkersLogs)
            .filter(WorkersLogs.name == "worker")
            .first()
        )
        if registro is None:
            registro = WorkersLogs(
                name="worker",
                descripcion=descripcion
            )
            db.add(registro)
        else:
            registro.descripcion = descripcion
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error guardando heartbeat: {e}")
    finally:
        db.close()



def get_pending(db: Session):
    return db.query(Orden).filter(Orden.status == "Lista para el worker..").first()


def run():
    while True:
        db = SessionLocal()
        logearDB("Tomando Orden")
        orden = get_pending(db)
        if orden:
            # marcar como processing
            orden.status = "Siendo procesada por worker.."
            logearDB("Procesando")
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
                    print("fallo la descarga de imagenes del worker")
                    #aca tendria que hacer vuelta atras 
                    orden.status = "pending"
                    db.commit()
                    db.close()
                    time.sleep(5)
                    continue

                orden.status = "Lista para predecir.."
            except Exception as e:
                orden.status = "error en worker"
                print(f"Error: {e}")

            db.commit()

        db.close()
        time.sleep(5)


if __name__ == "__main__":
    run()
