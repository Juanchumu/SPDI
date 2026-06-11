from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
import json
import time
import requests
from datetime import timedelta, datetime, timezone

from db.db import SessionLocal
from db.models import Orden, Entrenamiento, Modelos, Descargas, WorkersLogs, Informes
import os


# Guardamos el timestamp al momento de cargar el script
START_TIME = time.time()

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow requests from the web UI (any origin for simplicity)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



def minioVida():
    try:
        r = requests.get("http://minio:9000/minio/health/live",timeout=2)
        estado = "UP" if r.status_code == 200 else "DOWN"
        return estado 
    except Exception:
        return "DOWN"
def dbVida():
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        return "UP"
    except Exception as e:
        print(e)
        return "DOWN"
    finally:
        db.close()

def workerVida(nombre):
    db = SessionLocal()
    try:
        dato = (
            db.query(WorkersLogs)
            .filter(WorkersLogs.name == nombre)
            .order_by(WorkersLogs.id.desc())
            .first()
        )
        if dato is None:
            return {
                "status": "UNKNOWN",
                "descripcion": "Sin registros",
                "last_seen": None
            }
        #ahora = datetime.now(timezone.utc)
        ahora = datetime.utcnow()
        # Ajustá este valor según la frecuencia de heartbeat
        timeout = timedelta(seconds=30)
        if ahora - dato.updated_at > timeout:
            estado = "DOWN"
        else:
            estado = "UP"
        return {
            "status": estado,
            "descripcion": dato.descripcion,
            "last_seen": dato.updated_at.isoformat(),
            "seconds_since_last_heartbeat": int(
                (ahora - dato.updated_at).total_seconds()
            )
        }
    except Exception as e:
        print(e)
        return {
            "status": "ERROR",
            "descripcion": str(e),
            "last_seen": None
        }
    finally:
        db.close()

class EntrenamientoRequest(BaseModel):
    dia: int          # formato YYYYMMDD
    lat: float
    lon: float 

class OrdenRequest(BaseModel):
    dia: int          # formato YYYYMMDD
    lat: float
    lon: float


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/api/v1/orden", status_code=status.HTTP_201_CREATED)
def crear_orden(request: OrdenRequest, db: Session = Depends(get_db)):
    dia_str = str(request.dia)
    args = {
        "dia_de_la_imagen": dia_str,
        "lat": request.lat,
        "lon": request.lon,
    }
    nueva = Orden(
        args=json.dumps(args),
        status="Pendiente.."
    )
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    
    return {"id": nueva.id, "status": "Pendiente.."}


@app.get("/api/v1/orden")
def listar_ordenes(db: Session = Depends(get_db)):
    ordenes = db.query(Orden).order_by(Orden.created_at.desc()).limit(50).all()
    resultado = []
    for orden in ordenes:
        try:
            args = json.loads(orden.args)
            lat = args.get("lat", 0)
            lon = args.get("lon", 0)
            dia = args.get("dia_de_la_imagen", "")
        except:
            lat = 0
            lon = 0
            dia = ""
            
        item = {
            "id": orden.id,
            "lat": lat,
            "lon": lon,
            "dia": dia,
            "status": orden.status,
            "prediction": orden.prediccion
        }
        resultado.append(item)
    return resultado

@app.get("/api/v1/orden/{id}")
def obtener_orden(id: int, db: Session = Depends(get_db)):
    orden = db.query(Orden).filter(Orden.id == id).first()

    if orden is None: 
        raise HTTPException(status_code=404, detail="Orden No encontrada")

    respuesta = {
        "id": orden.id,
        "status": orden.status
    }
    if (orden.status == 'Predicha'):
        respuesta["prediccion"] = orden.prediccion
        respuesta["modelo_utilizado"] = orden.modelo_utilizado
        
    return respuesta

@app.delete("/api/v1/orden/{id}")
def cancelar_orden(id: int, db: Session = Depends(get_db)):
    orden = db.query(Orden).filter(Orden.id == id).first()
    if orden is None: 
        raise HTTPException(status_code=404, detail="Orden No encontrada")
    
    if orden.status == 'Predicha' or 'error' in orden.status.lower():
        raise HTTPException(status_code=400, detail="La orden ya finalizó o dio error")
        
    orden.status = "Cancelada"
    db.commit()
    return {"id": orden.id, "status": orden.status}


@app.post("/api/v1/generar_datos", status_code=status.HTTP_201_CREATED)
def generar_datos(request: EntrenamientoRequest, db: Session = Depends(get_db)):
    dia_str = str(request.dia)
    args = {
        "dia": dia_str, #Dia que hubo un incendio
        "lat": request.lat,
        "lon": request.lon
        }
    nueva = Entrenamiento(
        args=json.dumps(args),
        status="pending"
    )
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    
    return {"id": nueva.id, "status": "pending"}


@app.get("/api/v1/generar_datos/{id}")
def obtener_entrenamiento(id: int, db: Session = Depends(get_db)):
    entrenamientos = db.query(Entrenamiento).filter(Entrenamiento.id == id).first()
    if entrenamientos is None: 
        raise HTTPException(status_code=404, detail="Entrenamiento no encontrado")

    respuesta = f'Estado: {entrenamientos.status}'
    return respuesta

@app.get("/api/v1/health")  # liveness
def health(db: Session = Depends(get_db)):
    # Calculamos cuánto tiempo pasó
    uptime_seconds = int(time.time() - START_TIME)
    uptime_str = str(timedelta(seconds=uptime_seconds))

    q_validador = db.query(Orden).filter(Orden.status == "Pendiente..").count()
    q_worker = db.query(Orden).filter(Orden.status == "Lista para el worker..").count()
    q_predictor = db.query(Orden).filter(Orden.status == "Lista para predecir..").count()
    q_entrenador = db.query(Entrenamiento).filter(Entrenamiento.status == "pending").count()
    q_modelador = db.query(Entrenamiento).filter(Entrenamiento.status == "lista-para-entrenar").count()

    def get_worker_data(name, queue_size):
        data = workerVida(name)
        data["queue_size"] = queue_size
        return data

    respuesta = {
            "services": {
                "api": {
                    "status": "UP",
                    "uptime": uptime_str,
                    "queue_size": 0
                    },
                "worker": get_worker_data("worker", q_worker),
                "validador": get_worker_data("validador", q_validador),
                "entrenador": get_worker_data("entrenador", q_entrenador),
                "modelador": get_worker_data("modelador", q_modelador),
                "predictor": get_worker_data("predictor", q_predictor),
                "analista": get_worker_data("analista", 0),
                },
            "dependencies": {
                "database": dbVida(),
                "minio": minioVida()
                }
            }
    return respuesta 


@app.get("/api/v1/modelos")
def listar_modelos(db: Session = Depends(get_db)):
    modelos = (
        db.query(Modelos)
        .order_by(Modelos.created_at.desc())
        .all()
    )
    if modelos is None:
        return {"Error":"No hay Modelos"}
    if len(modelos) < 1:
        return {"Error":"No hay Modelos"}
    return [{
        "id": modelo.id,
        "name": modelo.name,
        "tipo": modelo.tipo,
        "final_loss": modelo.final_loss,
        "best_loss": modelo.best_loss,
        "pred_mean": modelo.pred_mean,
        "pred_min": modelo.pred_min,
        "pred_max": modelo.pred_max,
        "accuracy": modelo.accuracy,
        "precision": modelo.precision,
        "recall": modelo.recall,
        "f1_score": modelo.f1_score,
        "iou": modelo.iou,
        "dice": modelo.dice,
        "dataset_size": modelo.dataset_size,
        "created_at": modelo.created_at.isoformat() if modelo.created_at else None
        } for modelo in modelos ]
@app.get("/api/v1/informes")
def informes(db: Session = Depends(get_db)):
    informes = (
            db.query(Informes)
            .order_by(Informes.created_at.desc())
            .limit(20).all()
            )
    return [{
        "id": i.id,
        "created_at": i.created_at.isoformat(),
        "contenido": i.contenido
        }for i in informes]
@app.get("/api/v1/informes/ultimo")
def ultimo_informe(db: Session = Depends(get_db)):
    informe = (
            db.query(Informes)
            .order_by(Informes.created_at.desc())
            .first()
            )
    if not informe:
        return {"error": "sin informes"}
    return {
            "id": informe.id,
            "created_at": informe.created_at.isoformat(),
            "contenido": informe.contenido
            }
