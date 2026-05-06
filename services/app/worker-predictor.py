import time
import json
import torch
import rasterio
import numpy as np
from sqlalchemy.orm import Session

from .db import SessionLocal
from app.models import Orden

# =========================
# 🔧 MODELO (COPIADO DEL TRAINING)
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
            ft = self.encoder(x[:, t])       # (B, 32, H, W)
            ft = ft.mean(dim=[2,3])          # (B, 32)
            feats.append(ft)

        feats = torch.stack(feats, dim=1)    # (B, T, 32)

        out, _ = self.lstm(feats)            # (B, T, 64)
        last = out[:, -1]                    # (B, 64)

        last = last[:, :, None, None].expand(-1, -1, H, W)

        return self.decoder(last)


# =========================
# 🚀 CARGA DEL MODELO
# =========================

MODEL_PATH = "model.pth"  # <-- poné tu path real

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
        data = src.read().astype(np.float32)  # (25, H, W)
    return data


def preprocess(data):
    # reshape: (25, H, W) -> (5, 5, H, W)
    x = data.reshape(5, 5, data.shape[1], data.shape[2])

    # normalización igual que training
    x_min = x.min()
    x_max = x.max()
    x = (x - x_min) / (x_max - x_min + 1e-6)

    x = torch.tensor(x, dtype=torch.float32)
    x = x.unsqueeze(0)  # (1, 5, 5, H, W)

    return x


# =========================
# 🔮 PREDICCIÓN
# =========================

def predecir(ruta_stack):
    data = cargar_stack(ruta_stack)

    x = preprocess(data).to(device)

    with torch.no_grad():
        pred = model(x)  # ya tiene sigmoid

    pred = pred.cpu().numpy()[0, 0]  # (H, W)

    # score global
    score = pred.mean()

    if score > 0.5:
        return "Riesgo de Incendio Elevado"
    else:
        return "Riesgo Bajo"


# =========================
# 🔁 WORKER LOOP
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
                if not orden.ruta_stack:
                    raise Exception("No hay ruta_stack")

                pred = predecir(orden.ruta_stack)

                orden.status = "done"
                orden.prediccion = pred

            except Exception as e:
                orden.status = "error"
                print(f"Error en predicción: {e}")

            db.commit()

        db.close()
        time.sleep(5)


if __name__ == "__main__":
    run()
