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
from db.models import Orden, Entrenamiento, Modelos, Descargas, InformesClientes, WorkersLogs, Informes, Usuario, InformesRiesgo, Cliente, AreaAsegurada
import os

from passlib.context import CryptContext


# Guardamos el timestamp al momento de cargar el script
START_TIME = time.time()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    #allow_origins=["http://localhost:4200",],
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


####
# Eventos al iniciar
#####





#Funcion para crear un usuario administrador
#Inicial
def create_default_admin():
    db = SessionLocal()
    try:
        # Avoid creating the user if the table doesn't exist yet in an early startup, 
        # though the worker typically handles db creation, here we rely on the DB being up.
        admin_user = db.query(Usuario).filter(Usuario.username == "admin").first()
        if not admin_user:
            nuevo_admin = Usuario(
                username="admin",
                password_hash=hash_password("unluproyectofinal"),
                rol="admin"
            )
            db.add(nuevo_admin)
            db.commit()
    except Exception as e:
        print("Aún no se puede crear el admin o ya existe:", e)
    finally:
        db.close()




@app.on_event("startup")
async def startup_event():
    subprocess.Popen([sys.executable, "app/crearDB.py"])
    create_default_admin()






####
# Encriptado de contraseña| Login
###
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

@app.post("/api/v1/login")
def login(data: LoginRequest,db: Session = Depends(get_db)):
    usuario = (
        db.query(Usuario)
        .filter(Usuario.username == data.username)
        .first()
    )
    if not usuario:
        print(f"no existe el usuario {data.username}")
        raise HTTPException(status_code=401)

    if not verificar_password(
        data.password,
        usuario.password_hash
    ):
        print(f"La contraseña del usuario {data.username} es invalida")
        raise HTTPException(status_code=401)

    return {
        "success": True,
        "username": usuario.username
    }

##
# Encriptado bruno:
##

import hashlib

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

#
# Endpoints bruno
#





#
#MINIO
#
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
    cliente: str
@app.post("/api/v1/orden", status_code=status.HTTP_201_CREATED)
def crear_orden(request: OrdenRequest, db: Session = Depends(get_db)):
    dia_str = str(request.dia)
    usuario_str = str(request.username)
    cliente_str = str(request.cliente)
    args = {
        "dia_de_la_imagen": dia_str,
        "lat": request.lat,
        "lon": request.lon,
    }
    nueva = Orden(
        args=json.dumps(args),
        status="Pendiente..",
        username= usuario_str,
        cliente= cliente_str
    )
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    
    return {"id": nueva.id, "status": "Pendiente.."}
#
# Pedir todas las ordenes
#
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
            "username": orden.username,
            "cliente": orden.cliente,
            "status": orden.status,
            "prediction": orden.prediccion,
            "created_at": orden.created_at.isoformat() if orden.created_at else None
        }
        resultado.append(item)
    return resultado







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

    
    
#
# SOLICITUD DE INFORMES 
#
class InformeClienteRequest(BaseModel):
    responsable: str
    cliente: str

@app.post("/api/v1/informes/clientes", status_code=status.HTTP_201_CREATED)
def crear_informe_cliente(request: InformeClienteRequest,db: Session = Depends(get_db) ):
    informe = InformesClientes(
        responsable=request.responsable,
        cliente=request.cliente,
        estado="requerido"
    )
    db.add(informe)
    db.commit()
    db.refresh(informe)
    return {"id": informe.id,"estado": informe.estado}    
@app.get("/api/v1/informes/clientes/{informe_id}")
def obtener_informe_cliente(informe_id: int, db: Session = Depends(get_db) ):
    informe = (
        db.query(InformesClientes)
        .filter(InformesClientes.id == informe_id)
        .first()
    )
    if not informe:
        raise HTTPException(
            status_code=404,
            detail="Informe no encontrado"
        )

    return {
        "id": informe.id,
        "responsable": informe.responsable,
        "cliente": informe.cliente,
        "estado": informe.estado,
        "contenido": informe.contenido,
        "created_at": informe.created_at,
        "updated_at": informe.updated_at
    }
class InformeRiesgoRequest(BaseModel):
    responsable: str
    cliente: str
    descripcion: str

@app.post("/api/v1/informes/riesgo", status_code=status.HTTP_201_CREATED)
def crear_informe_riesgo(request: InformeRiesgoRequest,db: Session = Depends(get_db) ):
    informe = InformesRiesgo(
        responsable=request.responsable,
        cliente=request.cliente,
        descripcion=request.descripcion,
        estado="requerido"
    )
    db.add(informe)
    db.commit()
    db.refresh(informe)
    return {"id": informe.id,"estado": informe.estado}



@app.get("/api/v1/informes/riesgo/{riesgo_id}")
def obtener_informe_cliente(riesgo_id: int, db: Session = Depends(get_db) ):
    informe = (
        db.query(InformesRiesgo)
        .filter(InformesRiesgo.id == riesgo_id)
        .first()
    )
    if not informe:
        raise HTTPException(status_code=404,detail="Informe de Riesgo no encontrado")
    return {
        "id": informe.id,
        "responsable": informe.responsable,
        "cliente": informe.cliente,
        "estado": informe.estado,
        "contenido": informe.contenido,
        "descripcion": informe.contenido,
        "created_at": informe.created_at,
        "updated_at": informe.updated_at
    }
@app.get("/api/v1/informes/riesgo")
def obtener_informes_riesgo(username:str, db: Session = Depends(get_db) ):
    if (username == 'admin'):
        informes = ( db.query(InformesRiesgo).all() )
    else:
        informes = (db.query(InformesRiesgo).filter(InformesRiesgo.responsable == username).all())
    if not informes:
        raise HTTPException(status_code=404,detail="Informes de Riesgos no encontrados")
    
    features = []
    for informe in informes:
        features.append({"type": "Feature",
                         "properties": {
                             "id": informe.id,
                             "responsable": informe.responsable,
                             "cliente": informe.cliente,
                             "estado": informe.estado,
                             "contenido": informe.contenido,
                             "descripcion": informe.contenido,
                             "created_at": informe.created_at,
                             "updated_at": informe.updated_at}
                         })
    return {"type": "FeatureCollection",
            "features": features    }
### Endpoint Gemini
import google.generativeai as genai

# Configuración de Gemini (Se asume que la key se carga en las variables de entorno de docker-compose)
gemini_api_key = os.getenv("GEMINI_API_KEY", "")
if gemini_api_key:
    genai.configure(api_key=gemini_api_key)


## Endpoint AreaAsegurada - Cliente

class AreaAseguradaResponse(BaseModel):
    id: int
    nombre_lote: str
    latitud: float
    longitud: float
    riesgo_promedio: float | None = None
    descripcion_entorno: str | None = None

    class Config:
        orm_mode = True

class ClienteResponse(BaseModel):
    id: int
    nombre: str
    responsable : str | None = ""
    codigo_cliente: str
    email: str | None = None
    telefono: str | None = None
    descripcion: str | None = ""

    class Config:
        orm_mode = True

class ClienteCreate(BaseModel):
    nombre: str
    codigo_cliente: str
    responsable : str | None = ''
    email: str | None = None
    telefono: str | None = None
    descripcion: str

class AreaAseguradaCreate(BaseModel):
    nombre_lote: str
    latitud: float
    longitud: float
    descripcion_entorno: str | None = None

class AlertaPreviewRequest(BaseModel):
    area_id: int | None = None # si viene vacío se hace un batch de todas las áreas


@app.get("/api/v1/clientes", response_model=list[ClienteResponse])
def listar_clientes(username: str, db: Session = Depends(get_db)):
    if (username == 'admin'):
        clientes = db.query(Cliente).order_by(Cliente.id.asc()).all()
    else:
        clientes = db.query(Cliente).filter(Cliente.responsable == username).order_by(Cliente.id.asc()).all()
    if not clientes:
        raise HTTPException(status_code=404,detail="Clientes no encontrados")
    features = []
    for cliente in clientes:
        features.append({"type": "Feature",
                         "properties": {
                             "id": cliente.id,
                             "responsable": cliente.responsable,
                             "cliente": cliente.nombre,
                             "codigo": cliente.codigo_cliente,
                             "email": cliente.email,
                             "descripcion": cliente.descripcion,
                             "telefono": cliente.telefono}
                         })
    return {"type": "FeatureCollection", "features": features}


@app.get("/api/v1/clientes/{cliente_id}/areas", response_model=list[AreaAseguradaResponse])
def listar_areas_cliente(cliente_id: int, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return db.query(AreaAsegurada).filter(AreaAsegurada.cliente_id == cliente_id).order_by(AreaAsegurada.id.asc()).all()

@app.post("/api/v1/clientes", response_model=ClienteResponse, status_code=status.HTTP_201_CREATED)
def crear_cliente(req: ClienteCreate, db: Session = Depends(get_db)):
    nuevo = Cliente(nombre=req.nombre, codigo_cliente=req.codigo_cliente, email=req.email, telefono=req.telefono, descripcion=req.descripcion)
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

@app.post("/api/v1/clientes/{cliente_id}/areas", response_model=AreaAseguradaResponse, status_code=status.HTTP_201_CREATED)
def crear_area_cliente(cliente_id: int, req: AreaAseguradaCreate, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    nueva = AreaAsegurada(cliente_id=cliente_id, nombre_lote=req.nombre_lote, latitud=req.latitud, longitud=req.longitud, descripcion_entorno=req.descripcion_entorno)
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva

@app.post("/api/v1/clientes/{cliente_id}/alerta/preview")
def preview_alerta_gemini(cliente_id: int, req: AlertaPreviewRequest, db: Session = Depends(get_db)):
    if not gemini_api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY no configurada en el servidor.")
        
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
        
    query = db.query(AreaAsegurada).filter(AreaAsegurada.cliente_id == cliente_id)
    if req.area_id:
        query = query.filter(AreaAsegurada.id == req.area_id)
    areas = query.all()
    
    if not areas:
        raise HTTPException(status_code=404, detail="No hay áreas para generar alerta.")

    # Para este MVP si se piden múltiples áreas, generamos el texto para la que tiene el riesgo más alto o las concatenamos.
    # Por simplicidad del prompt pedido, vamos a tomar el área con el mayor riesgo_promedio de la lista obtenida.
    area_critica = max(areas, key=lambda a: a.riesgo_promedio if a.riesgo_promedio is not None else -1)
    riesgo_val = area_critica.riesgo_promedio if area_critica.riesgo_promedio is not None else 0
    nivel_riesgo = "ALTO" if riesgo_val > 0.5 else "MEDIO" if riesgo_val > 0.2 else "BAJO"
    
    # Mock NDMI/NDVI for demonstration purposes since we don't have them straight from DB yet
    ndmi_valor = "-0.15"
    ndvi_valor = "0.45"
    
    prompt = f'''Actúa como un Asistente Experto en Gestión de Riesgos Agropecuarios y Comunicación de Emergencias. Tu tarea es redactar un correo electrónico personalizado de alerta de riesgo de incendio para un productor agropecuario. El tono debe ser sumamente amable, preventivo, claro y de apoyo (compañerismo), evitando alarmismos innecesarios pero manteniendo la importancia de la prevención.

Se te proporcionarán los siguientes datos específicos extraídos de la base de datos:
- Nombre del Cliente (Dueño/Gestor): {cliente.nombre}
- Nombre del Campo/Establecimiento: {area_critica.nombre_lote}
- Nivel de Riesgo Detectado: {nivel_riesgo} (Valores posibles: MEDIO o ALTO)
- Índices de Monitoreo Satelital Recientes: NDMI (Humedad de vegetación) = {ndmi_valor}, NDVI (Biomasa) = {ndvi_valor}
- Directivas de Acción Interna (Extraídas del perfil del campo): {area_critica.descripcion_entorno or 'Sin directivas específicas.'}

INSTRUCCIONES DE REDACCIÓN:
1. Saluda cordialmente al cliente por su nombre.
2. Infórmale de manera empática que el sistema de monitoreo satelital ha detectado un riesgo [{nivel_riesgo}] de incendio en su establecimiento "{area_critica.nombre_lote}", debido a un descenso en el índice de humedad de la vegetación (NDMI: {ndmi_valor}).
3. Incorpora de forma natural, fluida y conversacional las "Directivas de Acción Interna" proporcionadas (por ejemplo, recordarles de manera amable que avisen a su grupo de WhatsApp de caporales, que coordinen con los encargados del campo, o que estén atentos a los canales informativos locales). No los listes de forma robótica; intégralos como consejos sugeridos para proteger el establecimiento.
4. Cierra el correo ofreciendo el apoyo de la gerencia de riesgos y con un saludo cálido.

RESTRICCIÓN DE FORMATO: Debe devolver ÚNICAMENTE un objeto JSON válido, sin bloques de código Markdown (no uses ```json), sin texto antes ni después. El JSON debe tener exactamente esta estructura:
{{
  "asunto": "Texto corto y claro para el asunto del mail, que incluya el nombre del campo y el nivel de alerta",
  "cuerpo_mail": "Texto completo del cuerpo del mail estructurado con saltos de línea (\\n) para una lectura cómoda."
}}'''

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        # Parse JSON
        import json
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        data = json.loads(text.strip())
        return data
    except Exception as e:
        print("Gemini Error:", e)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/clientes/{cliente_id}/alerta/send")
def send_alerta(cliente_id: int, req: dict, db: Session = Depends(get_db)):
    # Aquí iría la lógica de SMTP.
    print("=========================================")
    print(f"SIMULANDO ENVIO DE MAIL PARA CLIENTE {cliente_id}")
    print(f"ASUNTO: {req.get('asunto')}")
    print("CUERPO:")
    print(req.get('cuerpo_mail'))
    print("=========================================")
    return {"status": "ok", "message": "Correo enviado con éxito (Simulado)."}


