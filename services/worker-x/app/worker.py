import time
import json
from sqlalchemy.orm import Session

from datetime import datetime

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
            .filter(WorkersLogs.name == "worker-x")
            .first()
        )
        if registro is None:
            registro = WorkersLogs(
                name="worker-x",
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
    return db.query(Orden).filter(Orden.status == "Lista para el worker..").first()


def run():
    while True:
        db = SessionLocal()
        logearDB("Buscando Ordenes")
        orden = get_pending(db)
        if orden:
            # marcar como processing
            orden.status = "Siendo procesada por worker-x.."
            logearDB("Procesando")
            db.commit()
            args = json.loads(orden.args)

            try:
                # ejecutar script con los 3 argumentos + orden_id
                resultado = scriptms.run(
                        dia_de_la_imagen=args.get("dia_de_la_imagen"),
                        lat=args.get("lat"),
                        lon=args.get("lon"),
                        orden_id=orden.id,
                        db=db,
                        orden=orden)
                if (resultado == 1):
                    print("fallo la descarga de imagenes del worker-x")
                    #aca tendria que hacer vuelta atras 
                    orden.status = "Lista para el worker.."
                    db.commit()
                    db.close()
                    time.sleep(50)
                    continue

                orden.status = "Lista para predecir-x.."
            except Exception as e:
                orden.status = "error en worker-x"
                print(f"Error del worker-x: {e}")

            db.commit()

        db.close()
        time.sleep(5)


if __name__ == "__main__":
    run()
