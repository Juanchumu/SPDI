import time
import json
import torch
import rasterio
import numpy as np
from sqlalchemy.orm import Session
from scipy.ndimage import label, find_objects

from .db import SessionLocal
from app.models import Orden

# =========================
# 🔧 MODELO
# =========================

import torch.nn as nn

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
        self.lstm = nn.LSTM(input_size=32, hidden_size=64, batch_first=True)
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
            ft = ft.mean(dim=[2,3])
            feats.append(ft)

        feats = torch.stack(feats, dim=1)

        out, _ = self.lstm(feats)
        last = out[:, -1]

        last = last[:, :, None, None].expand(-1, -1, H, W)

        return self.decoder(last)


# =========================
# 🚀 CARGA
# =========================

MODEL_PATH = "model.pth"

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

model = TemporalFireNet()
model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
model.to(device)
model.eval()

print("Modelo cargado OK")


# =========================
# 📦 DATA
# =========================

def cargar_stack(ruta):
    with rasterio.open(ruta) as src:
        data = src.read().astype(np.float32)
        profile = src.profile
    return data, profile


def preprocess(data):
    x = data.reshape(5, 5, data.shape[1], data.shape[2])

    x_min = x.min()
    x_max = x.max()
    x = (x - x_min) / (x_max - x_min + 1e-6)

    x = torch.tensor(x, dtype=torch.float32).unsqueeze(0)
    return x


# =========================
# 🗺️ GUARDAR TIF
# =========================

def guardar_pred_tif(pred, profile, orden_id):
    profile.update(count=1, dtype="float32")

    path = f"dataset/predictions/pred_{orden_id}.tif"

    import os
    os.makedirs("dataset/predictions", exist_ok=True)

    with rasterio.open(path, "w", **profile) as dst:
        dst.write(pred.astype("float32"), 1)

    return path


# =========================
# 📊 % AREA EN RIESGO
# =========================

def calcular_porcentaje(pred, threshold=0.5):
    mask = pred > threshold
    return float(mask.mean()) * 100


# =========================
# 📦 BOUNDING BOXES
# =========================

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


# =========================
# 🔮 PREDICCIÓN COMPLETA
# =========================

def predecir(ruta_stack, orden_id):
    data, profile = cargar_stack(ruta_stack)

    x = preprocess(data).to(device)

    with torch.no_grad():
        pred = model(x)

    pred = pred.cpu().numpy()[0, 0]

    # 🗺️ guardar tif
    tif_path = guardar_pred_tif(pred, profile, orden_id)

    # 📊 porcentaje
    porcentaje = calcular_porcentaje(pred)

    # 📦 zonas
    zonas = detectar_zonas(pred)

    resultado = {
        "riesgo": "alto" if porcentaje > 10 else "bajo",
        "porcentaje_area_riesgo": porcentaje,
        "zonas_criticas": zonas,
        "archivo_prediccion": tif_path
    }

    return json.dumps(resultado)


# =========================
# 🔁 WORKER
# =========================

def get_pending(db: Session):
    return db.query(Orden).filter(Orden.status == "predict-ready").first()


def run():
    while True:
        db = SessionLocal()

        orden = get_pending(db)

        if orden:
            orden.status = "predicting"
            db.commit()

            try:
                pred = predecir(orden.ruta_stack, orden.id)

                orden.status = "done"
                orden.prediccion = pred

            except Exception as e:
                orden.status = "error"
                print(f"Error: {e}")

            db.commit()

        db.close()
        time.sleep(5)


if __name__ == "__main__":
    run()
