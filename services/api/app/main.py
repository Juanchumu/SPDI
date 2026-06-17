from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
import json
import time
import requests
from datetime import timedelta, datetime, timezone

from db.db import SessionLocal
from db.models import Orden, Entrenamiento, Modelos, Descargas, WorkersLogs, Informes, Cliente, AreaAsegurada
import os
import google.generativeai as genai

# Configuración de Gemini (Se asume que la key se carga en las variables de entorno de docker-compose)
gemini_api_key = os.getenv("GEMINI_API_KEY", "")
if gemini_api_key:
    genai.configure(api_key=gemini_api_key)


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
    codigo_cliente: str
    email: str | None = None
    telefono: str | None = None

    class Config:
        orm_mode = True

class ClienteCreate(BaseModel):
    nombre: str
    codigo_cliente: str
    email: str | None = None
    telefono: str | None = None

class AreaAseguradaCreate(BaseModel):
    nombre_lote: str
    latitud: float
    longitud: float
    descripcion_entorno: str | None = None

class AlertaPreviewRequest(BaseModel):
    area_id: int | None = None # si viene vacío se hace un batch de todas las áreas


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
        status="Lista para el worker.."
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

@app.get("/api/v1/clientes", response_model=list[ClienteResponse])
def listar_clientes(db: Session = Depends(get_db)):
    return db.query(Cliente).order_by(Cliente.id.asc()).all()

@app.get("/api/v1/clientes/{cliente_id}/areas", response_model=list[AreaAseguradaResponse])
def listar_areas_cliente(cliente_id: int, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return db.query(AreaAsegurada).filter(AreaAsegurada.cliente_id == cliente_id).order_by(AreaAsegurada.id.asc()).all()

@app.post("/api/v1/clientes", response_model=ClienteResponse, status_code=status.HTTP_201_CREATED)
def crear_cliente(req: ClienteCreate, db: Session = Depends(get_db)):
    nuevo = Cliente(nombre=req.nombre, codigo_cliente=req.codigo_cliente, email=req.email, telefono=req.telefono)
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
