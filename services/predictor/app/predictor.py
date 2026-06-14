import os
import time
import json
import shutil
import urllib3

import torch
import torch.nn as nn
import rasterio
import numpy as np


from datetime import datetime



from minio import Minio
from sqlalchemy.orm import Session
from scipy.ndimage import label, find_objects
import xgboost as xgb

from db.db import SessionLocal
from db.models import Orden, Modelos, WorkersLogs

# ==================================================
# CONFIG
# ==================================================

DB_MINIO_USER = os.getenv("DB_MINIO_USER")
DB_MINIO_PASS = os.getenv("DB_MINIO_PASS")

TMP_DIR = "tmp"
ORDERS_DIR = f"{TMP_DIR}/ordenes"
MODELS_DIR = f"{TMP_DIR}/modelos"
PRED_DIR = f"{TMP_DIR}/predicciones"

os.makedirs(ORDERS_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(PRED_DIR, exist_ok=True)

device = torch.device("cpu")

# ==================================================
# logs de estado en la db (actualiza)
# ==================================================
def logearDB(descripcion):
    db = SessionLocal()
    try:
        registro = (
            db.query(WorkersLogs)
            .filter(WorkersLogs.name == "predictor")
            .first()
        )
        if registro is None:
            registro = WorkersLogs(
                name="predictor",
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





# ==================================================
# MINIO
# ==================================================
def get_minio_client():
    http_client = urllib3.PoolManager(
        timeout=urllib3.Timeout(
            connect=5.0,
            read=30.0
        )
    )
    minio_host = os.getenv("MINIO_HOST", "minio")
    return Minio(
        f"{minio_host}:9000",
        access_key=DB_MINIO_USER,
        secret_key=DB_MINIO_PASS,
        secure=False,
        http_client=http_client
    )
# ==================================================
# MODELO
# ==================================================

class ConvBlock(nn.Module):
    def __init__(self, in_c, out_c):
        super().__init__()

        self.net = nn.Sequential(
            nn.Conv2d(in_c, out_c, 3, padding=1),
            nn.ReLU(),
            nn.Conv2d(out_c, out_c, 3, padding=1),
            nn.ReLU()
        )

    def forward(self, x):
        return self.net(x)


class TemporalFireNet(nn.Module):
    def __init__(self):
        super().__init__()

        self.encoder = ConvBlock(5, 32)

        self.lstm = nn.LSTM(
            input_size=32,
            hidden_size=64,
            batch_first=True
        )

        self.decoder = nn.Sequential(
            nn.Conv2d(64, 32, 3, padding=1),
            nn.ReLU(),
            nn.Conv2d(32, 1, 1),
            nn.Sigmoid()
        )

    def forward(self, x):
        B, T, C, H, W = x.shape

        feats = []

        for t in range(T):
            ft = self.encoder(x[:, t])
            ft = ft.mean(dim=[2, 3])
            feats.append(ft)

        feats = torch.stack(feats, dim=1)

        out, _ = self.lstm(feats)

        last = out[:, -1]
        last = last[:, :, None, None].expand(-1, -1, H, W)

        return self.decoder(last)

class TempCNN(nn.Module):
    """Red convolucional temporal pura (sin LSTM, usa Conv1D)"""
    def __init__(self):
        super().__init__()
        self.encoder = ConvBlock(5, 32)
        self.temporal_conv = nn.Sequential(
            nn.Conv1d(32, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv1d(64, 64, kernel_size=3, padding=1),
            nn.ReLU()
        )
        self.decoder = nn.Sequential(
            nn.Conv2d(64, 32, 3, padding=1),
            nn.ReLU(),
            nn.Conv2d(32, 1, 1),
            nn.Sigmoid()
        )

    def forward(self, x):
        B, T, C, H, W = x.shape
        feats = []
        for t in range(T):
            ft = self.encoder(x[:, t])  # (B, 32, H, W)
            ft = ft.mean(dim=[2, 3])    # (B, 32)
            feats.append(ft)
        feats = torch.stack(feats, dim=1)  # (B, T, 32)
        feats = feats.permute(0, 2, 1)     # (B, 32, T)
        temporal_out = self.temporal_conv(feats)  # (B, 64, T)
        last = temporal_out[:, :, -1]       # (B, 64)
        last = last[:, :, None, None].expand(-1, -1, H, W)
        return self.decoder(last)

# ==================================================
# DESCARGAR MODELO
# ==================================================

def descargar_ultimo_modelo():
    """Descarga el modelo con mejor F1 score de la DB"""
    time.sleep(5)
    db = SessionLocal()
    try:
        modelo = (
            db.query(Modelos)
            .order_by(Modelos.f1_score.desc())
            .first()
        )
        if modelo is None:
            print("No hay modelos en la DB")
            return None, None, None
        
        tipo = modelo.tipo or "temporal_fire_net"
        # Determinar extensión según tipo
        ext = ".json" if tipo == "xgboost" else ".pth"
        model_path = f"{MODELS_DIR}/{modelo.name}"
        
        if not os.path.exists(model_path):
            client = get_minio_client()
            client.fget_object(
                "modelos",
                modelo.name,
                model_path
            )
            print(f"Modelo descargado: {model_path} (tipo: {tipo})")
        return modelo.id, model_path, tipo
    finally:
        db.close()
# ==================================================
# CARGAR MODELO
# ==================================================
def cargar_modelo(model_path, tipo="temporal_fire_net"):
    """Carga el modelo según su tipo"""
    if tipo == "xgboost":
        model = xgb.XGBClassifier()
        model.load_model(model_path)
        print(f"Modelo XGBoost cargado OK")
        return model
    elif tipo == "temp_cnn":
        model = TempCNN()
        model.load_state_dict(
            torch.load(model_path, map_location=device)
        )
        model.to(device)
        model.eval()
        print(f"Modelo TempCNN cargado OK")
        return model
    else:  # temporal_fire_net
        model = TemporalFireNet()
        model.load_state_dict(
            torch.load(model_path, map_location=device)
        )
        model.to(device)
        model.eval()
        print("Modelo TemporalFireNet cargado OK")
        return model
# ==================================================
# DESCARGAR ORDEN
# ==================================================
def descargar_orden(orden_id):
    client = get_minio_client()
    local_path = f"{ORDERS_DIR}/escena_{orden_id}.tif"
    client.fget_object(
        "ordenes",
        f"escena_{orden_id}.tif",
        local_path
    )
    print(f"Orden descargada: {local_path}")
    return local_path
# ==================================================
# CARGAR STACK
# ==================================================
def cargar_stack(ruta):
    with rasterio.open(ruta) as src:
        data = src.read().astype(np.float32)
        profile = src.profile
    return data, profile
# ==================================================
# PREPROCESS
# ==================================================
def preprocess(data):
    if data.shape[0] != 15:
        raise Exception(
            f"El TIFF debe tener 15 bandas y tiene {data.shape[0]}"
        )
    H = data.shape[1]
    W = data.shape[2]

    # 3 tiempos, 5 canales
    x = data.reshape(3, 5, H, W)

    x_min = x.min()
    x_max = x.max()

    x = (x - x_min) / (x_max - x_min + 1e-6)

    x = torch.tensor(
        x,
        dtype=torch.float32
    ).unsqueeze(0)

    return x

# ==================================================
# PREDICCION XGBOOST
# ==================================================
def predecir_xgboost(model, ruta_stack, orden_id):
    """Predicción usando modelo XGBoost"""
    data, profile = cargar_stack(ruta_stack)
    if data.shape[0] != 17:
        raise Exception(f"El TIFF debe tener 17 bandas y tiene {data.shape[0]}")
    
    H = data.shape[1]
    W = data.shape[2]
    
    # Procesar Sentinel-2 (primeras 15 bandas)
    x_s2 = data[:15].reshape(3, 5, H, W)
    x_min = x_s2.min()
    x_max = x_s2.max()
    x_s2 = (x_s2 - x_min) / (x_max - x_min + 1e-6)
    
    # Aplanar Sentinel-2: (H*W, 15)
    x_s2_flat = x_s2.transpose(2, 3, 0, 1).reshape(H * W, 15)
    
    # Normalizar distancias de OSM: (H*W, 2)
    x_osm = data[15:] / 10000.0
    x_osm_flat = x_osm.transpose(1, 2, 0).reshape(H * W, 2)
    
    # Concatenar: (H*W, 17)
    x_flat = np.concatenate([x_s2_flat, x_osm_flat], axis=1)
    
    # Predecir probabilidades usando todas las 17 variables
    pred_proba = model.predict_proba(x_flat)[:, 1]  # (H*W,)
    pred = pred_proba.reshape(H, W)  # (H, W)
    
    # Enmascarar píxeles sin datos (franjas negras en el borde de los tiles de S2)
    nodata_mask = np.zeros((H, W), dtype=bool)
    for t in range(3):
        ndvi = data[t*5 + 0]
        nbr = data[t*5 + 1]
        ndbi = data[t*5 + 2]
        t_nodata = (ndvi == 0.0) & (nbr == 0.0) & (ndbi == 0.0)
        nodata_mask = nodata_mask | t_nodata
    pred[nodata_mask] = 0.0
    # Aplicar máscara de nubes (banda 4 del T1)
    nubes_t1 = data[3]
    pred[nubes_t1 == 1.0] = 0.0
    tif_path = guardar_pred_tif(pred, profile, orden_id)
    porcentaje = calcular_porcentaje(pred)
    zonas = detectar_zonas(pred)
    resultado = {
        "riesgo": "alto" if porcentaje > 30 else "bajo",
        "porcentaje_area_riesgo": porcentaje,
        "zonas_criticas": zonas,
        "archivo_prediccion": f"pred_{orden_id}.tif"
    }
    return resultado, tif_path

# ==================================================
# GUARDAR PREDICCION
# ==================================================
def guardar_pred_tif(pred, profile, orden_id):
    profile.update(
        count=1,
        dtype="float32"
    )
    path = f"{PRED_DIR}/pred_{orden_id}.tif"
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(pred.astype("float32"), 1)
    return path
# ==================================================
# SUBIR PREDICCION
# ==================================================
def subir_prediccion(orden_id, local_path):
    client = get_minio_client()
    bucket_name = "predicciones"
    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)
    client.fput_object(
        bucket_name,
        f"pred_{orden_id}.tif",
        local_path
    )
    print(f"Prediccion subida: pred_{orden_id}.tif")
# ==================================================
# METRICAS
# ==================================================
def calcular_porcentaje(pred, threshold=0.5):
    mask = pred > threshold
    return float(mask.mean()) * 100
# ==================================================
# ZONAS
# ==================================================
def detectar_zonas(pred, threshold=0.5, min_pixels=50):
    binary = pred > threshold
    labeled, num = label(binary)
    slices = find_objects(labeled)
    boxes = []
    for i, slc in enumerate(slices):
        if slc is None:
            continue
        region = labeled[slc] == (i + 1)
        if region.sum() < min_pixels:
            continue
        y1, y2 = slc[0].start, slc[0].stop
        x1, x2 = slc[1].start, slc[1].stop
        boxes.append({
            "x1": int(x1),
            "y1": int(y1),
            "x2": int(x2),
            "y2": int(y2),
            "pixels": int(region.sum())
        })
    return boxes
# ==================================================
# PREDICCION
# ==================================================
def predecir(model, ruta_stack, orden_id, tipo="temporal_fire_net"):
    if tipo == "xgboost":
        return predecir_xgboost(model, ruta_stack, orden_id)
    # El resto funciona para TemporalFireNet y TempCNN
    data, profile = cargar_stack(ruta_stack)
    x = preprocess(data).to(device)
    with torch.no_grad():
        pred = model(x)
    pred = pred.cpu().numpy()[0, 0]
    
    # Enmascarar píxeles sin datos (franjas negras en el borde de los tiles de S2)
    H, W = pred.shape
    nodata_mask = np.zeros((H, W), dtype=bool)
    for t in range(3):
        ndvi = data[t*5 + 0]
        nbr = data[t*5 + 1]
        ndbi = data[t*5 + 2]
        t_nodata = (ndvi == 0.0) & (nbr == 0.0) & (ndbi == 0.0)
        nodata_mask = nodata_mask | t_nodata
    pred[nodata_mask] = 0.0
    
    tif_path = guardar_pred_tif(
        pred,
        profile,
        orden_id
    )
    porcentaje = calcular_porcentaje(pred)
    zonas = detectar_zonas(pred)
    resultado = {
        "riesgo": "alto" if porcentaje > 10 else "bajo",
        "porcentaje_area_riesgo": porcentaje,
        "zonas_criticas": zonas,
        "archivo_prediccion": f"pred_{orden_id}.tif"
    }
    return resultado, tif_path
# ==================================================
# BUSCAR ORDEN PENDIENTE
# ==================================================
def get_pending(db: Session):
    return (
        db.query(Orden)
        .filter(
            Orden.status == "Lista para predecir.."
        )
        .order_by(Orden.id.asc())
        .first()
    )
# ==================================================
# WORKER
# ==================================================
def run():
    while True:
        modelo_id, model_path, modelo_tipo = descargar_ultimo_modelo()
        logearDB("Buscando Modelos Nuevos...")
        if modelo_id is None:
            logearDB("No hay Modelos, me pongo a dormir...")
            time.sleep(5)
            continue
        model = cargar_modelo(model_path, modelo_tipo)
        db = SessionLocal()
        try:
            orden = get_pending(db)
            if orden is None:
                time.sleep(5)
                continue
            print(f"Procesando orden {orden.id}")
            orden.status = "Prediciendo.."
            logearDB("Prediciendo...")
            db.commit()
            try:
                ruta_stack = descargar_orden(orden.id)
                resultado, tif_path = predecir(
                    model,
                    ruta_stack,
                    orden.id,
                    modelo_tipo
                )
                subir_prediccion(
                    orden.id,
                    tif_path
                )
                orden.status = "Predicha"
                orden.prediccion = json.dumps(resultado)
                orden.modelo_utilizado = f"{modelo_tipo}:{model_path.split('/')[-1]}"
                db.commit()
                print(f"Orden {orden.id} completada")
            except Exception as e:
                db.rollback()
                orden.status = "Error"
                db.commit()
                print(f"Error procesando orden {orden.id}: {e}")
        except Exception as e:
            print(f"Error general worker: {e}")
        finally:
            db.close()
        time.sleep(5)

# ==================================================
# MAIN
# ==================================================
if __name__ == "__main__":
    run()
