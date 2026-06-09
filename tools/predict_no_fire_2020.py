#!/usr/bin/env python3
"""Predicción de zona no incendiada (ejemplo negativo) usando el modelo XGBoost entrenado.
Ejemplo de uso:
    python3 tools/predict_no_fire_2020.py
"""

import os, sys
import numpy as np
from datetime import datetime, timedelta, timezone

# -------------------------------------------------------------------
# Parámetros de un caso negativo: ciudad de Buenos Aires, sin incendios reportados en enero 2020.
FECHA_PRE = "20200115"  # 15 de enero 2020 (fecha previa al foco de incendio, aunque no hubo incendio ahí)
LAT = -34.6037   # latitud Buenos Aires
LON = -58.3816   # longitud Buenos Aires
DESCRIPCION = "Buenos Aires 2020 (sin incendio)"

# -------------------------------------------------------------------
# Funciones auxiliares (índice NDVI, NBR, etc.) – idénticas a test_xgboost_local.py
def idx(a, b):
    """Índice normalizado (a‑b)/(a+b)"""
    return np.divide(
        a - b,
        a + b,
        out=np.zeros_like(a),
        where=(a + b) != 0
    )

# -------------------------------------------------------------------
# Descarga de escena (stack) usando Planetary Computer
def descargar_escena(dia_str, lat, lon, descripcion):
    import planetary_computer
    import pystac_client
    from odc.stac import stac_load

    fecha_base = datetime.strptime(dia_str, "%Y%m%d").replace(tzinfo=timezone.utc)
    # Ventana de 40 días antes del día solicitado (para evitar cualquier posible foco reciente)
    fecha_inicio = (fecha_base - timedelta(days=40)).strftime("%Y-%m-%d")
    fecha_fin = fecha_base.strftime("%Y-%m-%d")

    lat_buffer = 0.009
    lon_buffer = 0.011
    bbox = [lon - lon_buffer, lat - lat_buffer, lon + lon_buffer, lat + lon_buffer]

    print(f"   📡 Buscando imágenes para {descripcion} ({lat}, {lon})…")
    print(f"      Rango: {fecha_inicio} a {fecha_fin}")

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
    items = items[:4]
    if len(items) < 4:
        print(f"⚠️  Sólo {len(items)} imágenes encontradas, se necesitan 4")
        return None
    print(f"✅ {len(items)} imágenes encontradas")

    processed_data = []
    for i, item in enumerate(items[1:]):
        print(f"  Descargando timestamp {i+1}/3: {item.id[:30]}…")
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
        processed_data.append([ndvi, nbr, ndbi, nubes, fecha_band])

    # Determinar la menor dimensión espacial entre los timestamps y recortar
    min_h = min(d[0].shape[0] for d in processed_data)
    min_w = min(d[0].shape[1] for d in processed_data)
    bandas_stack = []
    for p in processed_data:
        for band in p:
            bandas_stack.append(band[:min_h, :min_w])

    if len(bandas_stack) != 15:
        print(f"⚠️  Stack incompleto: {len(bandas_stack)} bandas")
        return None
    stack = np.stack(bandas_stack)  # (15, H, W)
    return stack

# -------------------------------------------------------------------
def cargar_modelo(model_path):
    import xgboost as xgb
    model = xgb.XGBClassifier()
    model.load_model(model_path)
    return model

def predecir(model, stack):
    # Normalizar al mismo rango usado en entrenamiento (0‑1)
    x_min = stack.min()
    x_max = stack.max()
    stack_norm = (stack - x_min) / (x_max - x_min + 1e-6)
    T, C, H, W = 3, 5, stack_norm.shape[1], stack_norm.shape[2]
    x = stack_norm.reshape(T, C, H, W)
    x_flat = x.transpose(2, 3, 0, 1).reshape(H * W, T * C)
    proba = model.predict_proba(x_flat)[:, 1]
    mask = (proba > 0.5).astype("float32")
    fire_pct = mask.mean() * 100
    return fire_pct, mask.reshape(H, W)

def main():
    print("=" * 60)
    print("🔥 Predicción de zona sin incendio (caso negativo) usando XGBoost entrenado (2024‑2025)")
    print("=" * 60)
    stack = descargar_escena(FECHA_PRE, LAT, LON, DESCRIPCION)
    if stack is None:
        sys.exit(1)
    model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "xgb_test_model.json")
    if not os.path.exists(model_path):
        print(f"❌ Modelo no encontrado: {model_path}")
        sys.exit(1)
    model = cargar_modelo(model_path)
    fire_pct, _ = predecir(model, stack)
    print(f"\n🔎 Predicción de zona incendiable: {fire_pct:.1f}% de los píxeles")
    print("✅ Predicción completada")

if __name__ == "__main__":
    main()
