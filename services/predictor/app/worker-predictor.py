import os
import time
import json
import shutil
import urllib3

import torch
import torch.nn as nn
import rasterio
import numpy as np

from minio import Minio
from sqlalchemy.orm import Session
from scipy.ndimage import label, find_objects

from db.db import SessionLocal
from db.models import Orden, Modelos

# ==================================================
# CONFIG
# ==================================================

DB_MINIO_USER = os.getenv("MINIO_ROOT_USER", "minioadmin")
DB_MINIO_PASS = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")

TMP_DIR = "tmp"
ORDERS_DIR = f"{TMP_DIR}/ordenes"
MODELS_DIR = f"{TMP_DIR}/modelos"
PRED_DIR = f"{TMP_DIR}/predicciones"

os.makedirs(ORDERS_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(PRED_DIR, exist_ok=True)

device = torch.device("cpu")

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

    return Minio(
        "minio:9000",
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

# ==================================================
# DESCARGAR MODELO
# ==================================================

def descargar_ultimo_modelo():
    db = SessionLocal()
    try:
        modelo = (
            db.query(Modelos)
            .order_by(Modelos.id.desc())
            .first()
        )
        if modelo is None:
            raise Exception("No hay modelos en la DB")
        model_path = f"{MODELS_DIR}/fire_model_ver_{modelo.id}.pth"
        if not os.path.exists(model_path):
            client = get_minio_client()
            client.fget_object(
                "modelos",
                f"fire_model_ver_{modelo.id}.pth",
                model_path
            )
            print(f"Modelo descargado: {model_path}")
        return modelo.id, model_path
    finally:
        db.close()
# ==================================================
# CARGAR MODELO
# ==================================================
def cargar_modelo(model_path):
    model = TemporalFireNet()
    model.load_state_dict(
        torch.load(
            model_path,
            map_location=device
        )
    )
    model.to(device)
    model.eval()
    print("Modelo cargado OK")
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
def predecir(model, ruta_stack, orden_id):
    data, profile = cargar_stack(ruta_stack)
    x = preprocess(data).to(device)
    with torch.no_grad():
        pred = model(x)
    pred = pred.cpu().numpy()[0, 0]
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
    modelo_id, model_path = descargar_ultimo_modelo()
    model = cargar_modelo(model_path)
    while True:
        db = SessionLocal()
        try:
            orden = get_pending(db)
            if orden is None:
                time.sleep(5)
                continue
            print(f"Procesando orden {orden.id}")
            orden.status = "Prediciendo.."
            db.commit()
            try:
                ruta_stack = descargar_orden(orden.id)
                resultado, tif_path = predecir(
                    model,
                    ruta_stack,
                    orden.id
                )
                subir_prediccion(
                    orden.id,
                    tif_path
                )
                orden.status = "Predicha"
                orden.prediccion = json.dumps(resultado)
                orden.modelo_utilizado = f"fire_model_ver_{modelo_id}"
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
