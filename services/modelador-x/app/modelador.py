
import os
import time
# import torch  # disabled
import rasterio
import numpy as np
# import torch.nn as nn  # disabled
import shutil
import urllib3
import xgboost as xgb
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import joblib

from datetime import datetime



from tqdm import tqdm
from minio import Minio
# from torch.utils.data import Dataset, DataLoader  # disabled

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
            .filter(WorkersLogs.name == "modelador-x")
            .first()
        )
        if registro is None:
            registro = WorkersLogs(
                name="modelador-x",
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
class FireDataset:
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

        # Procesar 17 bandas: las primeras 15 son de Sentinel-2, las últimas 2 son distancias de OSM
        x_s2 = x[:15].reshape(3, 5, 200, 200)
        x_min = x_s2.min()
        x_max = x_s2.max()
        x_s2 = (x_s2 - x_min) / (x_max - x_min + 1e-6)
        
        # Normalizar distancias de OSM con un tope de 10km, o usar 1.0 (10km) si no existen
        if x.shape[0] == 15:
            x_osm = np.ones((2, 200, 200), dtype=np.float32)
        else:
            x_osm = x[15:17] / 10000.0
        
        x_final = np.concatenate([x_s2.reshape(15, 200, 200), x_osm], axis=0)

        # x = torch.tensor(x, dtype=torch.float32)  # disabled
        # y = torch.tensor(y, dtype=torch.float32)  # disabled

        return x_final, y
# ==================================================
# MODELO
# ==================================================
# NOTA: Clases de redes neuronales deshabilitadas para el modo exclusivo de XGBoost
# class ConvBlock(nn.Module):
#     def __init__(self, in_c, out_c):
#         super().__init__()
#         self.net = nn.Sequential(
#             nn.Conv2d(in_c, out_c, 3, padding=1),
#             nn.ReLU(),
#             nn.Conv2d(out_c, out_c, 3, padding=1),
#             nn.ReLU()
#         )
#     def forward(self, x):
#         return self.net(x)
# class TemporalFireNet(nn.Module):
#     def __init__(self):
#         super().__init__()
#         self.encoder = ConvBlock(5, 32)
#         self.lstm = nn.LSTM(
#             input_size=32,
#             hidden_size=64,
#             batch_first=True
#         )
#         self.decoder = nn.Sequential(
#             nn.Conv2d(64, 32, 3, padding=1),
#             nn.ReLU(),
#             nn.Conv2d(32, 1, 1),
#             nn.Sigmoid()
#         )
#     def forward(self, x):
#         # x = (B, T, C, H, W)
#         B, T, C, H, W = x.shape
#         feats = []
#         for t in range(T):
#             ft = self.encoder(x[:, t])
#             ft = ft.mean(dim=[2, 3])
#             feats.append(ft)
#         feats = torch.stack(feats, dim=1)
#         out, _ = self.lstm(feats)
#         last = out[:, -1]
#         last = last[:, :, None, None].expand(-1, -1, H, W)
#         return self.decoder(last)

# NOTA: Clase TempCNN deshabilitada para el modo exclusivo de XGBoost
# class TempCNN(nn.Module):
#     """Red convolucional temporal pura (sin LSTM, usa Conv1D)"""
#     def __init__(self):
#         super().__init__()
#         self.encoder = ConvBlock(5, 32)
#         self.temporal_conv = nn.Sequential(
#             nn.Conv1d(32, 64, kernel_size=3, padding=1),
#             nn.ReLU(),
#             nn.Conv1d(64, 64, kernel_size=3, padding=1),
#             nn.ReLU()
#         )
#         self.decoder = nn.Sequential(
#             nn.Conv2d(64, 32, 3, padding=1),
#             nn.ReLU(),
#             nn.Conv2d(32, 1, 1),
#             nn.Sigmoid()
#         )
#
#     def forward(self, x):
#         B, T, C, H, W = x.shape
#         feats = []
#         for t in range(T):
#             ft = self.encoder(x[:, t])  # (B, 32, H, W)
#             ft = ft.mean(dim=[2, 3])    # (B, 32)
#             feats.append(ft)
#         feats = torch.stack(feats, dim=1)  # (B, T, 32)
#         # Conv1D espera (B, C, T)
#         feats = feats.permute(0, 2, 1)     # (B, 32, T)
#         temporal_out = self.temporal_conv(feats)  # (B, 64, T)
#         last = temporal_out[:, :, -1]       # (B, 64)
#         last = last[:, :, None, None].expand(-1, -1, H, W)
#         return self.decoder(last)
# ==================================================
# MINIO
# ==================================================
def get_minio_client():
    #Para que no cuelgue el contenedor si no hay miniO
    http_client = urllib3.PoolManager(
            timeout=urllib3.Timeout(
                connect=5.0,
                read=30.0))
    minio_host = os.getenv("MINIO_HOST", "minio")
    return Minio(
        f"{minio_host}:9000",
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
        Entrenamiento.status == "lista-para-entrenar-x"
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
            "train-inputs-x",
            f"escena_{d.id}.tif",
            f"tmp/dataset/inputs/escena_{d.id}.tif"
        )
        print(f"Input {d.id} descargado")
    #Segundo descargamos los masks 
    for d in datos:
        client.fget_object(
            "train-masks-x",
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
        Entrenamiento.status == "lista-para-entrenar-x"
    ).all()
    db.close()
    return len(datos)
# ==================================================
# VERIFICAR EXISTENCIA MODELO
# ==================================================
def ConsultarModelosNroDeEntrenamiento(nro):
    db = SessionLocal()
    try:
        nombre_modelo = f"fire_model_x_ver_{nro}.pth"
        ultimo_modelo = (
            db.query(Modelos)
            .order_by(Modelos.id.desc())
            .first()
        )
        if ultimo_modelo is None:
            print("No hay modelos x")
            return 1
        modelo = (
            db.query(Modelos)
            .filter(Modelos.name == nombre_modelo)
            .first()
        )
        if modelo is None:
            #print(f"El modelo x {nro} no existe")
            return 2
        return 0
    finally:
        db.close()
# ==================================================
# SUBIR MODELO
# ==================================================
def AlmacenarModelo(nombre,final_loss,best_loss,dataset_size,metricas,tipo="temporal_fire_net"):
    db = SessionLocal()
    nuevoModelo = Modelos(
        name=nombre,
        tipo=tipo,
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
    bucket_name = "modelos-x"
    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)
    client.fput_object(
        bucket_name,
        nombre,
        f"{MODEL_ROOT}/{nombre}"
    )
    print(f"Modelo x {nombre} subido")



# ==================================================
# ENTRENAMIENTO
# ==================================================

# NOTA: EntrenarModelo (entrenamiento de NN) deshabilitado para el modo exclusivo de XGBoost
# def EntrenarModelo(nro):
#     ... (original code omitted)


# ==================================================
# ENTRENAMIENTO XGBOOST
# ==================================================
# NOTA: EntrenarModeloXGBoost ajustado para funcionar con datos de numpy (sin usar torch)
def EntrenarModeloXGBoost(nro):
    print("Iniciando entrenamiento XGBoost...")
    dataset = FireDataset(DATASET_ROOT)
    
    # Preparar datos: aplanar píxeles como filas
    all_X = []
    all_y = []
    max_samples_per_image = 10000  # Submuestrear para no desbordar la memoria
    
    for i in range(len(dataset)):
        x, y = dataset[i]
        # x tiene forma (17, 200, 200)
        x_np = x
        y_np = y
        
        C, H, W = x_np.shape
        # Reorganizar: cada píxel tiene 17 características
        x_flat = x_np.transpose(1, 2, 0).reshape(H * W, C)  # (40000, 17)
        y_flat = y_np.reshape(H * W)  # (40000,)
        # Aplicar máscara de nubes: ignorar píxeles donde la máscara de nubes (banda 4) sea == 1
        cloud_mask = (x_np[3] == 1.0)  # el índice de banda 3 corresponde a la máscara de nubes
        cloud_mask_flat = cloud_mask.reshape(H * W)
        # Conservar únicamente los píxeles sin nubes
        valid_idx = ~cloud_mask_flat
        x_flat = x_flat[valid_idx]
        y_flat = y_flat[valid_idx]
        
        # Submuestrear
        if len(x_flat) > max_samples_per_image:
            indices = np.random.choice(len(x_flat), max_samples_per_image, replace=False)
            x_flat = x_flat[indices]
            y_flat = y_flat[indices]
        
        all_X.append(x_flat)
        all_y.append(y_flat)
    
    X_train = np.concatenate(all_X, axis=0)
    y_train = np.concatenate(all_y, axis=0)
    # Binarizar target
    y_train = (y_train > 0.5).astype(np.float32)
    
    print(f"Dataset XGBoost: {X_train.shape[0]} muestras, {X_train.shape[1]} features")
    
    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        eval_metric='logloss',
        use_label_encoder=False,
        verbosity=1
    )
    model.fit(X_train, y_train)
    
    # Guardar modelo
    nombre_modelo = f"xgb_model_ver_{nro}.json"
    os.makedirs(MODEL_ROOT, exist_ok=True)
    model_path = f"{MODEL_ROOT}/{nombre_modelo}"
    model.save_model(model_path)
    print(f"Modelo XGBoost guardado: {model_path}")
    
    # Evaluar
    metricas = EvaluarModeloXGBoost(model, X_train, y_train)
    
    # Calcular loss aproximado (log loss)
    from sklearn.metrics import log_loss
    y_pred_proba = model.predict_proba(X_train)[:, 1]
    final_loss = log_loss(y_train, y_pred_proba)
    
    AlmacenarModelo(
        nombre_modelo,
        final_loss,
        final_loss,  # best_loss = final_loss para XGBoost
        len(dataset),
        metricas,
        tipo="xgboost"
    )


# ==================================================
# EVALUAR MODELO XGBOOST
# ==================================================
def EvaluarModeloXGBoost(model, X, y):
    y_pred = model.predict(X)
    y_pred_proba = model.predict_proba(X)[:, 1]
    
    TP = ((y_pred == 1) & (y == 1)).sum()
    TN = ((y_pred == 0) & (y == 0)).sum()
    FP = ((y_pred == 1) & (y == 0)).sum()
    FN = ((y_pred == 0) & (y == 1)).sum()
    
    accuracy = (TP + TN) / (TP + TN + FP + FN + 1e-8)
    precision = TP / (TP + FP + 1e-8)
    recall = TP / (TP + FN + 1e-8)
    f1 = 2 * precision * recall / (precision + recall + 1e-8)
    iou = TP / (TP + FP + FN + 1e-8)
    dice = 2 * TP / (2 * TP + FP + FN + 1e-8)
    
    return {
        "pred_mean": float(np.mean(y_pred_proba)),
        "pred_min": float(np.min(y_pred_proba)),
        "pred_max": float(np.max(y_pred_proba)),
        "accuracy": float(accuracy),
        "precision": float(precision),
        "recall": float(recall),
        "f1_score": float(f1),
        "iou": float(iou),
        "dice": float(dice),
    }


# ==================================================
# ENTRENAMIENTO TEMPCNN
# ==================================================
# NOTE: EntrenarModeloTempCNN (CNN training) disabled for XGBoost-only mode
# # NOTE: EntrenarModeloTempCNN disabled (already commented above). (original code omitted)


# ==================================================
# EVALUAR MODELO 
# ==================================================
# NOTE: EvaluarModelo (NN evaluation) disabled for XGBoost-only mode
# def EvaluarModelo(model, loader):
#     model.eval()
#     TP = 0
#     TN = 0
#     FP = 0
#     FN = 0
#     pred_means = []
#     pred_mins = []
#     pred_maxs = []
#     with torch.no_grad():
#         for x, y in loader:
#             x = x.to(device)
#             y = y.to(device)
#             pred = model(x)
#             pred_means.append(pred.mean().item())
#             pred_mins.append(pred.min().item())
#             pred_maxs.append(pred.max().item())
#             pred_bin = (pred > 0.5).float()
#             TP += ((pred_bin == 1) & (y == 1)).sum().item()
#             TN += ((pred_bin == 0) & (y == 0)).sum().item()
#             FP += ((pred_bin == 1) & (y == 0)).sum().item()
#             FN += ((pred_bin == 0) & (y == 1)).sum().item()
#     accuracy = (TP + TN) / (TP + TN + FP + FN + 1e-8)
#     precision = TP / (TP + FP + 1e-8)
#     recall = TP / (TP + FN + 1e-8)
#     f1_score = ( 2 * precision * recall/ (precision + recall + 1e-8))
#     iou = TP / (TP + FP + FN + 1e-8)
#     dice = (2 * TP / (2 * TP + FP + FN + 1e-8))
#     return {
#         "pred_mean": float(np.mean(pred_means)),
#         "pred_min": float(np.min(pred_mins)),
#         "pred_max": float(np.max(pred_maxs)),
#         "accuracy": float(accuracy),
#         "precision": float(precision),
#         "recall": float(recall),
#         "f1_score": float(f1_score),
#         "iou": float(iou),
#         "dice": float(dice),
#     }


# ==================================================
# LOOP PRINCIPAL
# ==================================================
def run():
    while True:
        try:
            nro = ConsultarNroDeEntrenamientos()
            
            db = SessionLocal()
            ultimo_modelo = db.query(Modelos).order_by(Modelos.id.desc()).first()
            ultimo_size = ultimo_modelo.dataset_size if ultimo_modelo else 0
            db.close()
            
            if nro > 0 and nro >= ultimo_size + 5:
                print(f"Nuevo modelo requerido (Actual: {nro}, Ultimo: {ultimo_size})")
                logearDB("Modelando x")
                descarga = TraerDeMiniOEntrenamientos()
                if descarga == 0:
                    EntrenarModeloXGBoost(nro)
            elif ultimo_size == 0 and nro > 0:
                print("Nuevo modelo inicial requerido")
                logearDB("Modelando x")
                descarga = TraerDeMiniOEntrenamientos()
                if descarga == 0:
                    EntrenarModeloXGBoost(nro)
            else:
                print(f"Entrenamientos disponibles: {nro} (Se necesitan {ultimo_size + 10} para nuevo modelo)")
                time.sleep(5)
        except Exception as e:
            print(f"ERROR en el modelador: {e}")
            time.sleep(5)
if __name__ == "__main__":
    run()

