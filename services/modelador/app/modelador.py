
import os
import time
import torch
import rasterio
import numpy as np
import torch.nn as nn
import shutil
import urllib3

from datetime import datetime



from tqdm import tqdm
from minio import Minio
from torch.utils.data import Dataset, DataLoader

from db.db import SessionLocal
from db.models import Entrenamiento, Modelos, WorkersLogs


# ==================================================
# CONFIG
# ==================================================

DATASET_ROOT = "tmp/dataset"
MODEL_ROOT = "tmp/modelos"

DB_MINIO_USER = os.getenv("DB_MINIO_USER")
DB_MINIO_PASS = os.getenv("DB_MINIO_PASS")

device = "cpu"

# ==================================================
# logs de estado en la db (actualiza)
# ==================================================
def logearDB(descripcion):
    db = SessionLocal()
    try:
        registro = (
            db.query(WorkersLogs)
            .filter(WorkersLogs.name == "modelador")
            .first()
        )
        if registro is None:
            registro = WorkersLogs(
                name="modelador",
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
# DATASET
# ==================================================
class FireDataset(Dataset):
    TARGET_H = 200
    TARGET_W = 200

    def __init__(self, root):
        self.root = root
        self.inputs_dir = os.path.join(root, "inputs")
        self.masks_dir = os.path.join(root, "masks")
        self.files = sorted(os.listdir(self.inputs_dir))

    def __len__(self):
        return len(self.files)

    def _load_tif(self, path):
        with rasterio.open(path) as src:
            return src.read().astype(np.float32)

    def _center_crop(self, arr):
        """
        arr: (bandas, H, W)
        devuelve: (bandas, 200, 200)
        """
        _, h, w = arr.shape

        if h < self.TARGET_H or w < self.TARGET_W:
            raise ValueError(
                f"Imagen demasiado pequeña: {h}x{w}. "
                f"Mínimo requerido: {self.TARGET_H}x{self.TARGET_W}"
            )

        start_h = (h - self.TARGET_H) // 2
        start_w = (w - self.TARGET_W) // 2

        end_h = start_h + self.TARGET_H
        end_w = start_w + self.TARGET_W

        return arr[:, start_h:end_h, start_w:end_w]

    def __getitem__(self, idx):
        fname = self.files[idx]

        x_path = os.path.join(self.inputs_dir, fname)
        y_path = os.path.join(self.masks_dir, fname)

        x = self._load_tif(x_path)
        y = self._load_tif(y_path)

        # Recorte central a 200x200
        x = self._center_crop(x)
        y = self._center_crop(y)

        # 15 bandas -> (3 tiempos, 5 variables, 200, 200)
        x = x.reshape(3, 5, 200, 200)

        x_min = x.min()
        x_max = x.max()
        x = (x - x_min) / (x_max - x_min + 1e-6)

        x = torch.tensor(x, dtype=torch.float32)
        y = torch.tensor(y, dtype=torch.float32)

        return x, y
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
        # x = (B, T, C, H, W)
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
# MINIO
# ==================================================
def get_minio_client():
    #Para que no cuelgue el contenedor si no hay miniO
    http_client = urllib3.PoolManager(
            timeout=urllib3.Timeout(
                connect=5.0,
                read=30.0))
    return Minio(
        "minio:9000",
        access_key=DB_MINIO_USER,
        secret_key=DB_MINIO_PASS,
        secure=False
    )
# ==================================================
# DESCARGA DATASET
# ==================================================
def TraerDeMiniOEntrenamientos():
    db = SessionLocal()
    datos = db.query(Entrenamiento).filter(
        Entrenamiento.status == "lista-para-entrenar"
    ).all()
    db.close()
    if len(datos) == 0:
        print("No hay entrenamientos disponibles")
        return 2
    #Crear directorios en el contenedor:
    #borrar archivos viejos del contenedor: 
    shutil.rmtree("tmp/dataset", ignore_errors=True)
    #Primero descargamos los inputs
    os.makedirs("tmp/dataset/inputs", exist_ok=True)
    os.makedirs("tmp/dataset/masks", exist_ok=True)
    client = get_minio_client()
    #Primero descargamos los inputs
    for d in datos:
        client.fget_object(
            "train-inputs",
            f"escena_{d.id}.tif",
            f"tmp/dataset/inputs/escena_{d.id}.tif"
        )
        print(f"Input {d.id} descargado")
    #Segundo descargamos los masks 
    for d in datos:
        client.fget_object(
            "train-masks",
            f"escena_{d.id}.tif",
            f"tmp/dataset/masks/escena_{d.id}.tif"
        )
        print(f"Mask {d.id} descargada")
    return 0
# ==================================================
# CONSULTAR NRO ENTRENAMIENTOS
# ==================================================
def ConsultarNroDeEntrenamientos():
    db = SessionLocal()
    datos = db.query(Entrenamiento).filter(
        Entrenamiento.status == "lista-para-entrenar"
    ).all()
    db.close()
    return len(datos)
# ==================================================
# VERIFICAR EXISTENCIA MODELO
# ==================================================
def ConsultarModelosNroDeEntrenamiento(nro):
    db = SessionLocal()
    try:
        nombre_modelo = f"fire_model_ver_{nro}.pth"
        ultimo_modelo = (
            db.query(Modelos)
            .order_by(Modelos.id.desc())
            .first()
        )
        if ultimo_modelo is None:
            print("No hay modelos")
            return 1
        modelo = (
            db.query(Modelos)
            .filter(Modelos.name == nombre_modelo)
            .first()
        )
        if modelo is None:
            print(f"El modelo {nro} no existe")
            return 2
        return 0
    finally:
        db.close()
# ==================================================
# SUBIR MODELO
# ==================================================
def AlmacenarModelo(nombre,final_loss,best_loss,dataset_size,metricas):
    db = SessionLocal()
    nuevoModelo = Modelos(
        name=nombre,
        final_loss=final_loss,
        best_loss=best_loss,
        pred_mean=metricas["pred_mean"],
        pred_min=metricas["pred_min"],
        pred_max=metricas["pred_max"],
        accuracy=metricas["accuracy"],
        precision=metricas["precision"],
        recall=metricas["recall"],
        f1_score=metricas["f1_score"],
        iou=metricas["iou"],
        dice=metricas["dice"],
        dataset_size=dataset_size
    )
    db.add(nuevoModelo)
    db.commit()
    db.close()
    client = get_minio_client()
    bucket_name = "modelos"
    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)
    client.fput_object(
        bucket_name,
        nombre,
        f"{MODEL_ROOT}/{nombre}"
    )
    print(f"Modelo {nombre} subido")



# ==================================================
# ENTRENAMIENTO
# ==================================================

def EntrenarModelo(nro):
    print("Iniciando entrenamiento...")
    dataset = FireDataset(DATASET_ROOT)
    loader = DataLoader(dataset,batch_size=2,shuffle=True)
    model = TemporalFireNet().to(device)
    criterion = nn.BCELoss()
    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=1e-3
    )
    # Utilizamos 5 porque no necesitamos un modelo cientificamente preciso
    # Necesitamos un modelo en 2 minutos o menos
    max_epochs = 5
    best_loss = float("inf")
    final_loss = None
    patience = 2
    no_improve = 0
    # Métricas de diagnóstico
    last_pred_mean = None
    last_pred_min = None
    last_pred_max = None
    for epoch in range(max_epochs):
        model.train()
        total_loss = 0
        for x, y in tqdm(loader):
            x = x.to(device)
            y = y.to(device)
            pred = model(x)
            loss = criterion(pred, y)
            with torch.no_grad():
                last_pred_mean = pred.mean().item()
                last_pred_min = pred.min().item()
                last_pred_max = pred.max().item()
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        avg_loss = total_loss / len(loader)
        final_loss = avg_loss
        if avg_loss < best_loss:
            best_loss = avg_loss
            no_improve = 0
        else:
            no_improve += 1
        if avg_loss < 1e-6:
            print("Early stop: loss ~ 0")
            break
        if no_improve >= patience:
            print("Early stop: sin mejora")
            break
    nombre_modelo = f"fire_model_ver_{nro}.pth"
    os.makedirs(MODEL_ROOT, exist_ok=True)
    model_path = f"{MODEL_ROOT}/{nombre_modelo}"
    torch.save(model.state_dict(),model_path)
    print(f"Modelo guardado: {model_path}")
    metricas = EvaluarModelo(model,loader)
    AlmacenarModelo(
            nombre_modelo,
            final_loss,
            best_loss,
            len(dataset),
            metricas
            )


# ==================================================
# EVALUAR MODELO 
# ==================================================
def EvaluarModelo(model, loader):
    model.eval()
    TP = 0
    TN = 0
    FP = 0
    FN = 0
    pred_means = []
    pred_mins = []
    pred_maxs = []
    with torch.no_grad():
        for x, y in loader:
            x = x.to(device)
            y = y.to(device)
            pred = model(x)
            pred_means.append(pred.mean().item())
            pred_mins.append(pred.min().item())
            pred_maxs.append(pred.max().item())
            pred_bin = (pred > 0.5).float()
            TP += ((pred_bin == 1) & (y == 1)).sum().item()
            TN += ((pred_bin == 0) & (y == 0)).sum().item()
            FP += ((pred_bin == 1) & (y == 0)).sum().item()
            FN += ((pred_bin == 0) & (y == 1)).sum().item()
    accuracy = (TP + TN) / (TP + TN + FP + FN + 1e-8)
    precision = TP / (TP + FP + 1e-8)
    recall = TP / (TP + FN + 1e-8)
    f1_score = ( 2 * precision * recall/ (precision + recall + 1e-8))
    iou = TP / (TP + FP + FN + 1e-8)
    dice = (2 * TP / (2 * TP + FP + FN + 1e-8))
    return {
        "pred_mean": float(np.mean(pred_means)),
        "pred_min": float(np.min(pred_mins)),
        "pred_max": float(np.max(pred_maxs)),
        "accuracy": float(accuracy),
        "precision": float(precision),
        "recall": float(recall),
        "f1_score": float(f1_score),
        "iou": float(iou),
        "dice": float(dice),
    }


# ==================================================
# LOOP PRINCIPAL
# ==================================================
def run():
    while True:
        try:
            nro = ConsultarNroDeEntrenamientos()
            print(f"Entrenamientos disponibles: {nro}")
            logearDB("Consultando Entrenamientos")
            if nro > 0 and ConsultarModelosNroDeEntrenamiento(nro) == 1:
                print("Nuevo modelo inicial requerido")
                logearDB("Modelando")
                descarga = TraerDeMiniOEntrenamientos()
                if descarga == 0:
                    EntrenarModelo(nro)
            if nro > 0 and (nro % 10) == 0:
                #aca tendria que ser, si no hay modelos, y hay 10 registros
                #se empieza a modelar 
                estado = ConsultarModelosNroDeEntrenamiento(nro)
                if estado == 2:
                    print("Nuevo modelo requerido")
                    logearDB("Modelando")
                    descarga = TraerDeMiniOEntrenamientos()
                    if descarga == 0:
                        EntrenarModelo(nro)
                else:
                    print("Modelo ya existente")
            time.sleep(5)
        except Exception as e:
            print(f"ERROR en el modelador: {e}")
            time.sleep(5)
if __name__ == "__main__":
    run()

