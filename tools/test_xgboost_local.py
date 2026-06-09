#!/usr/bin/env python3
"""
Script de prueba local: entrena XGBoost con datos REALES de Sentinel-2
descargados de Microsoft Planetary Computer.

Usa coordenadas de incendios reales en Argentina para generar datos
de entrenamiento y evaluar el modelo.

Uso:
    source tools/.venv/bin/activate
    python3 tools/test_xgboost_local.py
"""

import os
import sys
import time
import numpy as np
from datetime import datetime, timedelta, timezone

# ==================================================
# CONFIG
# ==================================================

# Coordenadas de incendios reales en Argentina
# (fecha YYYYMMDD, latitud, longitud, descripción)
INCENDIOS = [
    ("20250101", -34.60, -58.45, "Buenos Aires"),
    ("20250115", -31.42, -64.18, "Córdoba"),
    ("20250201", -27.45, -59.00, "Chaco"),
    ("20250110", -33.30, -66.35, "San Luis"),
    ("20250120", -26.83, -65.20, "Tucumán"),
    ("20250205", -38.00, -57.55, "Mar del Plata"),
    ("20250125", -32.95, -60.65, "Rosario"),
    ("20250210", -24.78, -65.42, "Jujuy"),
]

# Cuántas muestras usar (max = len(INCENDIOS))
N_MUESTRAS = min(6, len(INCENDIOS))

# Subsampleo de pixeles por imagen
MAX_SAMPLES_PER_IMG = 10000

# Directorio de salida
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(BASE_DIR, "xgb_test_data")

# ==================================================
# FUNCIÓN AUXILIAR - índice espectral
# ==================================================
def idx(a, b):
    """Calcula índice normalizado (a-b)/(a+b)"""
    return np.divide(
        a - b,
        a + b,
        out=np.zeros_like(a),
        where=(a + b) != 0
    )

# ==================================================
# DESCARGAR DATOS DE SENTINEL-2
# ==================================================
def descargar_escena(dia_str, lat, lon, descripcion):
    """
    Descarga imágenes Sentinel-2 de Microsoft Planetary Computer.
    Replica la lógica del entrenador del SPDI.
    Retorna: (stack_15bandas, mask_incendio) o None si falla.
    """
    import planetary_computer
    import pystac_client
    from odc.stac import stac_load

    fecha_base = datetime.strptime(dia_str, "%Y%m%d").replace(tzinfo=timezone.utc)
    fecha_inicio = (fecha_base - timedelta(days=40)).strftime("%Y-%m-%d")
    fecha_fin = fecha_base.strftime("%Y-%m-%d")

    # BBOX (~1km x 1km)
    lat_buffer = 0.009
    lon_buffer = 0.011
    bbox = [lon - lon_buffer, lat - lat_buffer, lon + lon_buffer, lat + lat_buffer]

    print(f"   📡 Buscando imágenes para {descripcion} ({lat}, {lon})...")
    print(f"      Rango: {fecha_inicio} a {fecha_fin}")

    # Conectar a Planetary Computer
    catalog = pystac_client.Client.open(
        "https://planetarycomputer.microsoft.com/api/stac/v1",
        modifier=planetary_computer.sign_inplace
    )

    search = catalog.search(
        collections=["sentinel-2-l2a"],
        bbox=bbox,
        datetime=f"{fecha_inicio}/{fecha_fin}",
        query={"eo:cloud_cover": {"lte": 100}},
        limit=6
    )

    items = list(search.items())
    items.sort(key=lambda x: x.datetime, reverse=True)
    items = items[:4]  # 4 items: [0]=mask, [1:4]=stack

    if len(items) < 4:
        print(f"   ⚠️  Solo {len(items)} imágenes disponibles (se necesitan 4)")
        return None

    print(f"   ✅ {len(items)} imágenes encontradas")

    # ---- STACK (3 timestamps × 5 canales = 15 bandas) ----
    items_stack = items[1:]
    bandas_stack = []

    for i, item in enumerate(items_stack):
        print(f"      Descargando timestamp {i+1}/3: {item.id[:30]}...")
        
        ds = stac_load(
            [item],
            bands=["red", "nir", "swir16", "SCL"],
            bbox=bbox,
            resolution=10,
            chunks={},
            dtype="uint16"
        ).isel(time=0)

        red = ds["red"].values.astype("float32")
        nir = ds["nir"].values.astype("float32")
        swir = ds["swir16"].values.astype("float32")
        scl = ds["SCL"].values.astype("float32")

        ndvi = idx(nir, red)
        nbr = idx(nir, swir)
        ndbi = idx(swir, nir)
        nubes = np.isin(scl, [8, 9, 10]).astype("float32")

        fecha_img = item.datetime
        dia_del_anio = fecha_img.timetuple().tm_yday
        dias_en_anio = 366 if (fecha_img.year % 4 == 0 and (fecha_img.year % 100 != 0 or fecha_img.year % 400 == 0)) else 365
        fecha_norm = (dia_del_anio - 1) / (dias_en_anio - 1)
        fecha_band = np.full(ndvi.shape, fecha_norm, dtype="float32")

        bandas_stack.extend([ndvi, nbr, ndbi, nubes, fecha_band])

    if len(bandas_stack) != 15:
        print(f"   ⚠️  Stack incompleto: {len(bandas_stack)} bandas")
        return None

    stack = np.stack(bandas_stack)  # (15, H, W)

    # ---- MASK (usando item[0]) ----
    item_mask = items[0]
    print(f"      Generando máscara de incendio...")
    
    ds_mask = stac_load(
        [item_mask],
        bands=["nir", "swir16"],
        bbox=bbox,
        resolution=10,
        chunks={},
        dtype="uint16"
    ).isel(time=0)

    nir_mask = ds_mask["nir"].values.astype("float32")
    swir_mask = ds_mask["swir16"].values.astype("float32")
    nbr_mask = idx(nir_mask, swir_mask)
    mask = (nbr_mask < 0.1).astype("float32")

    fire_pct = mask.mean() * 100
    print(f"   🔥 Máscara generada: {fire_pct:.1f}% pixeles con fuego potencial")
    print(f"      Tamaño imagen: {stack.shape[1]}×{stack.shape[2]} px")

    return stack, mask


# ==================================================
# PREPARAR DATOS PARA XGBOOST
# ==================================================
def preparar_datos(escenas):
    """Convierte las escenas descargadas en arrays X, y para XGBoost"""
    all_X = []
    all_y = []
    
    for stack, mask in escenas:
        T, C = 3, 5
        H, W = stack.shape[1], stack.shape[2]
        
        # (15, H, W) -> (3, 5, H, W)
        x = stack.reshape(T, C, H, W)
        
        # Normalizar
        x_min = x.min()
        x_max = x.max()
        x = (x - x_min) / (x_max - x_min + 1e-6)
        
        # Flatten: cada pixel = 1 fila con 15 features
        x_flat = x.transpose(2, 3, 0, 1).reshape(H * W, T * C)
        y_flat = mask.reshape(H * W)
        y_flat = (y_flat > 0.5).astype(np.float32)
        
        # Subsamplear
        if len(x_flat) > MAX_SAMPLES_PER_IMG:
            indices = np.random.choice(len(x_flat), MAX_SAMPLES_PER_IMG, replace=False)
            x_flat = x_flat[indices]
            y_flat = y_flat[indices]
        
        all_X.append(x_flat)
        all_y.append(y_flat)
    
    return np.concatenate(all_X, axis=0), np.concatenate(all_y, axis=0)


# ==================================================
# ENTRENAR XGBOOST
# ==================================================
def entrenar_xgboost(X_train, y_train, X_test, y_test):
    """Entrena XGBoost y muestra progreso"""
    import xgboost as xgb
    
    print(f"\n🚀 Entrenando XGBoost...")
    print(f"   n_estimators=100, max_depth=6, learning_rate=0.1")
    print(f"   Train: {len(X_train):,} muestras | Test: {len(X_test):,} muestras")
    
    t0 = time.time()
    
    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        eval_metric='logloss',
        use_label_encoder=False,
        verbosity=1
    )
    
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=True
    )
    
    print(f"\n⏱️  Tiempo de entrenamiento: {time.time() - t0:.1f}s")
    return model


# ==================================================
# EVALUAR
# ==================================================
def evaluar(model, X, y, nombre=""):
    """Calcula métricas (mismas que usa el modelador del SPDI)"""
    y_pred = model.predict(X)
    y_proba = model.predict_proba(X)[:, 1]
    
    TP = ((y_pred == 1) & (y == 1)).sum()
    TN = ((y_pred == 0) & (y == 0)).sum()
    FP = ((y_pred == 1) & (y == 0)).sum()
    FN = ((y_pred == 0) & (y == 1)).sum()
    
    accuracy  = (TP + TN) / (TP + TN + FP + FN + 1e-8)
    precision = TP / (TP + FP + 1e-8)
    recall    = TP / (TP + FN + 1e-8)
    f1        = 2 * precision * recall / (precision + recall + 1e-8)
    iou       = TP / (TP + FP + FN + 1e-8)
    dice      = 2 * TP / (2 * TP + FP + FN + 1e-8)
    
    print(f"\n{'='*50}")
    print(f"📊 MÉTRICAS {nombre}")
    print(f"{'='*50}")
    print(f"  Accuracy:   {accuracy:.4f}")
    print(f"  Precision:  {precision:.4f}")
    print(f"  Recall:     {recall:.4f}")
    print(f"  F1 Score:   {f1:.4f}")
    print(f"  IoU:        {iou:.4f}")
    print(f"  Dice:       {dice:.4f}")
    print(f"  Pred mean:  {np.mean(y_proba):.4f}")
    print(f"  Pred min:   {np.min(y_proba):.4f}")
    print(f"  Pred max:   {np.max(y_proba):.4f}")
    print(f"{'='*50}")
    print(f"  TP={TP:,}  FP={FP:,}")
    print(f"  FN={FN:,}  TN={TN:,}")
    print(f"{'='*50}")
    return {"f1": f1, "accuracy": accuracy}


# ==================================================
# FEATURE IMPORTANCE
# ==================================================
def mostrar_features(model):
    """Muestra importancia de cada feature"""
    names = []
    for t in range(3):
        for n in ["NDVI", "NBR", "NDBI", "Nubes", "Fecha"]:
            names.append(f"T{t}_{n}")
    
    imp = model.feature_importances_
    order = np.argsort(imp)[::-1]
    
    print(f"\n🔍 Feature Importance:")
    print(f"{'─'*40}")
    for i in range(len(order)):
        j = order[i]
        bar = "█" * int(imp[j] * 50)
        print(f"  {names[j]:<12} {imp[j]:.4f} {bar}")


# ==================================================
# MAIN
# ==================================================
def main():
    print("=" * 60)
    print("🔥 SPDI - XGBoost con datos REALES de Sentinel-2")
    print("=" * 60)
    
    np.random.seed(42)
    
    # ---- Descargar datos ----
    print(f"\n📡 Descargando {N_MUESTRAS} escenas de Microsoft Planetary Computer...")
    print(f"   (Sentinel-2 L2A, resolución 10m)\n")
    
    escenas = []
    for i in range(N_MUESTRAS):
        dia, lat, lon, desc = INCENDIOS[i]
        print(f"\n[{i+1}/{N_MUESTRAS}] {desc}")
        try:
            resultado = descargar_escena(dia, lat, lon, desc)
            if resultado is not None:
                escenas.append(resultado)
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    if len(escenas) < 2:
        print("\n❌ No se pudieron descargar suficientes escenas (mínimo 2)")
        sys.exit(1)
    
    print(f"\n✅ {len(escenas)} escenas descargadas exitosamente")
    
    # ---- Preparar datos ----
    print(f"\n📊 Preparando dataset...")
    X, y = preparar_datos(escenas)
    
    print(f"   Total muestras: {X.shape[0]:,}")
    print(f"   Features: {X.shape[1]}")
    print(f"   Clase 0 (no fuego): {(y == 0).sum():,}")
    print(f"   Clase 1 (fuego): {(y == 1).sum():,}")
    print(f"   % fuego: {y.mean()*100:.2f}%")
    
    # ---- Split ----
    n = len(X)
    idx_perm = np.random.permutation(n)
    split = int(0.8 * n)
    X_train, X_test = X[idx_perm[:split]], X[idx_perm[split:]]
    y_train, y_test = y[idx_perm[:split]], y[idx_perm[split:]]
    
    # ---- Entrenar ----
    model = entrenar_xgboost(X_train, y_train, X_test, y_test)
    
    # ---- Evaluar ----
    evaluar(model, X_train, y_train, "(TRAIN)")
    test_metrics = evaluar(model, X_test, y_test, "(TEST)")
    
    # ---- Features ----
    mostrar_features(model)
    
    # ---- Guardar ----
    model_path = os.path.join(BASE_DIR, "xgb_test_model.json")
    model.save_model(model_path)
    print(f"\n💾 Modelo guardado: {model_path}")
    
    # ---- Resumen ----
    print(f"\n{'='*60}")
    print(f"✅ RESULTADO FINAL")
    print(f"{'='*60}")
    print(f"  Escenas reales usadas: {len(escenas)}")
    print(f"  F1 Score (test):   {test_metrics['f1']:.4f}")
    print(f"  Accuracy (test):   {test_metrics['accuracy']:.4f}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
