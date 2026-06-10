from fastapi import FastAPI, APIRouter, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
import json
import time
import requests
from datetime import timedelta, datetime, timezone
import subprocess
import sys

from db.db import SessionLocal
from db.models import Orden, Entrenamiento, Modelos, Descargas, WorkersLogs, Informes, Usuario
import os

from passlib.context import CryptContext


# Guardamos el timestamp al momento de cargar el script
START_TIME = time.time()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    subprocess.Popen([sys.executable, "app/crearDB.py"])


pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto"
)

def verificar_password(password, password_hash):
    return pwd_context.verify(password, password_hash)
def hashear_password(password):
    return pwd_context.hash(password)

class LoginRequest(BaseModel):
    username: str
    password: str



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
    username: str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/api/v1/orden", status_code=status.HTTP_201_CREATED)
def crear_orden(request: OrdenRequest, db: Session = Depends(get_db)):
    dia_str = str(request.dia)
    usuario_str = str(request.username)
    args = {
        "dia_de_la_imagen": dia_str,
        "lat": request.lat,
        "lon": request.lon,
    }
    nueva = Orden(
        args=json.dumps(args),
        status="Pendiente..",
        username= usuario_str
    )
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    
    return {"id": nueva.id, "status": "Pendiente.."}


@app.get("/api/v1/orden/{id}")
def obtener_orden(id: int, db: Session = Depends(get_db)):
    orden = db.query(Orden).filter(Orden.id == id).first()

    if orden is None: 
        raise HTTPException(status_code=404, detail="Orden No encontrada")

    respuesta = f'Estado: {orden.status}'
    if (orden.status == 'Predicha'):
        respuesta = {
                "id": orden.id,
                "status": orden.status,
                "prediccion": orden.prediccion,
                "modelo_utilizado": orden.modelo_utilizado
                }
    return respuesta



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
def health():
    # Calculamos cuánto tiempo pasó
    uptime_seconds = int(time.time() - START_TIME)
    # Formateamos a un formato legible (HH:MM:SS)
    uptime_str = str(timedelta(seconds=uptime_seconds))

    #return {"status_code": 200,"message": "Todo anda bien por acá.","uptime": uptime_str}
    respuesta = {
            "services": {
                "api": {
                    "status": "UP",
                    "uptime": uptime_str
                    },
                "worker": workerVida("worker"),
                "validador": workerVida("validador"),
                "entrenador": workerVida("entrenador"),
                "modelador":workerVida("modelador"),
                "predictor": workerVida("predictor"),
                "analista": workerVida("analista"),
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

@app.get("/api/v1/recuperar_ordenes")
def listar_ordenes(username: str, db: Session = Depends(get_db)):
    if (username == 'admin'):
        ordenes = db.query(Orden).all()
    else:
        ordenes = db.query(Orden).filter(Orden.username == username).all()
    features = []
    for orden in ordenes:
        args = json.loads(orden.args)
        features.append({
            "type": "Feature",
            "properties": {
                "id": orden.id,
                "dia": args.get("dia_de_la_imagen"),
                "estado": orden.status,
                "prediccion": orden.prediccion,
                "enviado": orden.created_at.isoformat() if orden.created_at else None,
                "terminado": orden.updated_at.isoformat() if orden.updated_at else None,
                "modelo": orden.modelo_utilizado if orden.modelo_utilizado else None
            },
            "geometry": {
                "type": "Point",
                "coordinates": [
                    args.get("lon"),
                    args.get("lat")
                ]
            }
        })
    return {
        "type": "FeatureCollection",
        "features": features
    }


### USUARIOS
class UsuarioRequest(BaseModel):
    username: str
    password: str

@app.post("/api/v1/usuarios")
def crear_usuario(
    data: UsuarioRequest,
    db: Session = Depends(get_db)
):
    existe = (
        db.query(Usuario)
        .filter(Usuario.username == data.username)
        .first()
    )

    if existe:
        raise HTTPException(
            status_code=400,
            detail="El usuario ya existe"
        )

    usuario = Usuario(
        username=data.username,
        password_hash=hashear_password(data.password)
    )

    db.add(usuario)
    db.commit()
    db.refresh(usuario)

    return {
        "id": usuario.id,
        "username": usuario.username
    }




router = APIRouter()

@app.post("/login")
def login(
    data: LoginRequest,
    db: Session = Depends(get_db)
):
    usuario = (
        db.query(Usuario)
        .filter(Usuario.username == data.username)
        .first()
    )

    if not usuario:
        raise HTTPException(status_code=401)

    if not verificar_password(
        data.password,
        usuario.password_hash
    ):
        raise HTTPException(status_code=401)

    return {
        "success": True,
        "username": usuario.username
    }
