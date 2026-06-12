# imports
from app.osm_utils import get_osm_distances
from rasterio.coords import BoundingBox
import os
import zipfile
import numpy as np
import rasterio
from rasterio.enums import Resampling
from datetime import datetime, timedelta, UTC
import urllib3

import planetary_computer
import pystac_client
from odc.stac import stac_load

from minio import Minio

from db.db import SessionLocal
from db.models import Descargas

print("imports cargados...!")

# ==================================================
# MINIO
# ==================================================
DB_MINIO_USER = os.getenv("DB_MINIO_USER")
DB_MINIO_PASS = os.getenv("DB_MINIO_PASS")
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
def AlmacenarOrdenLista(nro_orden):
    client = get_minio_client()
    bucket_name = "ordenes-x"
    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)
        print("Bucket para las ordenes creado")
    client.fput_object(
        bucket_name,
        f"escena_{nro_orden}.tif",
        f"/app/ordenes/inputs/escena_{nro_orden}.tif"
    )
    print(f"Archivo escena_{nro_orden}.tif subido")


def update_status(db, orden, msg):
    if db and orden:
        orden.status = msg
        db.commit()

# ==================================================
# FUNCIÓN PRINCIPAL
# ==================================================
def run(dia_de_la_imagen, lat, lon, orden_id, db=None, orden=None):

    update_status(db, orden, "Calculando fechas y coordenadas...")
    fecha_base = datetime.strptime(dia_de_la_imagen, "%Y%m%d").replace(tzinfo=UTC)

    fecha_inicio = (fecha_base - timedelta(days=40)).strftime("%Y-%m-%d")
    fecha_fin = fecha_base.strftime("%Y-%m-%d")

    #os.makedirs("/tmp/descargas", exist_ok=True)
    #os.makedirs("tmp/data", exist_ok=True)
    os.makedirs("/app/ordenes/inputs", exist_ok=True)

    # ==================================================
    # BBOX
    # ==================================================
    lat_buffer = 0.009
    lon_buffer = 0.011

    izquierda = lon - lon_buffer
    derecha = lon + lon_buffer
    abajo = lat - lat_buffer
    arriba = lat + lat_buffer

    bbox = [izquierda, abajo, derecha, arriba]

    # ==================================================
    # STAC CLIENT
    # ==================================================
    update_status(db, orden, "Buscando imágenes en el catálogo espacial de Microsoft...")
    catalog = pystac_client.Client.open(
        "https://planetarycomputer.microsoft.com/api/stac/v1",
        modifier=planetary_computer.sign_inplace
    )

    search = catalog.search(
        collections=["sentinel-2-l2a"],
        bbox=bbox,
        datetime=f"{fecha_inicio}/{fecha_fin}",
        query={
            "eo:cloud_cover": {
                "lte": 100
            }
        },
        limit=3
    )

    items = list(search.items())
    #Nota: No importa que tanto para atras se pregunte en el tiempo
    #Siempre devuelve 4 elementos 
    print("lista")
    print(items)
    # ordenar por fecha descendente
    items.sort(
        key=lambda x: x.datetime,
        reverse=True
    )
    #Por eso, solamente se piden 3 elementos para hacer el stack 
    items = items[:3]

    if len(items) == 0:
        print("Sin imágenes")
        # Esto tendria que devolver un error o 
        # intentar mas tarde debido a la api 
        return 1

    print(f"Hay {len(items)} imagenes")

    fechas = []
    bandas_stack = []

    # ==================================================
    # PROCESAMIENTO
    # ==================================================
    for item in items:

        product_id = item.id
        fecha_img = item.datetime

        fechas.append(fecha_img)

        print(f"Procesando: {product_id}")

        # ==================================================
        # CARGAR BANDAS
        # ==================================================
        update_status(db, orden, "Descargando bandas espectrales del satélite Sentinel-2...")
        ds = stac_load(
            [item],
            bands=["red", "nir", "swir16", "SCL"],
            bbox=bbox,
            resolution=10,
            chunks={},
            dtype="uint16"
        ).isel(time=0)

        red_data = ds["red"].values.astype("float32")
        nir_data = ds["nir"].values.astype("float32")

        swir_data = ds["swir16"].values.astype("float32")

        scl_data = ds["SCL"].values.astype("float32")

        # ==================================================
        # INDICES
        # ==================================================
        update_status(db, orden, "Procesando tensores geoespaciales...")
        def idx(a, b):
            return np.divide(
                a - b,
                a + b,
                out=np.zeros_like(a),
                where=(a + b) != 0
            )

        ndvi = idx(nir_data, red_data)

        nbr = idx(nir_data, swir_data)

        ndbi = idx(swir_data, nir_data)

        nubes = np.isin(scl_data, [8, 9, 10]).astype("float32")
        # ==================================================
        # NORMALIZACION FECHA (DIA DEL AÑO)
        # ==================================================
        dia_del_anio = fecha_img.timetuple().tm_yday
        dias_en_el_anio = 366 if (
                fecha_img.year % 4 == 0 and 
                (fecha_img.year % 100 != 0 or fecha_img.year % 400 == 0)
                ) else 365
        fecha_norm = (dia_del_anio - 1) / (dias_en_el_anio - 1)
        fecha_band = np.full(
                ndvi.shape,
                fecha_norm,
                dtype="float32")
       

        bandas_stack.extend([
            ndvi,
            nbr,
            ndbi,
            nubes,
            fecha_band
        ])

        # ==================================================
        # PERFIL GEO
        # ==================================================
        transform = ds.odc.geobox.transform

        profile = {
            "driver": "GTiff",
            "height": ndvi.shape[0],
            "width": ndvi.shape[1],
            "count": len(bandas_stack),
            "dtype": "float32",
            "crs": ds.odc.crs,
            "transform": transform
        }

    if len(bandas_stack) == 15:
        try:
            update_status(db, orden, "Calculando distancias a rutas y campings...")
            left, bottom, right, top = rasterio.transform.array_bounds(profile["height"], profile["width"], profile["transform"])
            bounds = BoundingBox(left, bottom, right, top)
            road_dist, camping_dist = get_osm_distances(
                bounds, 
                profile["crs"], 
                (profile["height"], profile["width"]), 
                profile["transform"]
            )
            bandas_stack.extend([road_dist, camping_dist])
        except Exception as e:
            print(f"Error calculating OSM distances in worker: {e}")
            road_dist = np.full((profile["height"], profile["width"]), 10000.0, dtype=np.float32)
            camping_dist = np.full((profile["height"], profile["width"]), 10000.0, dtype=np.float32)
            bandas_stack.extend([road_dist, camping_dist])

    if len(bandas_stack) == 0:
        print("No hay datos válidos")
        return 1

    # ==================================================
    # GUARDAR STACK
    # ==================================================
    update_status(db, orden, "Guardando escena multitemporal...")
    ruta_stack = f"/app/ordenes/inputs/escena_{orden_id}.tif"

    profile["count"] = len(bandas_stack)

    with rasterio.open(ruta_stack, "w", **profile) as dst:

        for i in range(len(bandas_stack)):
            dst.write(bandas_stack[i], i + 1)

    update_status(db, orden, "Enviando imagen a MinIO para predicción...")
    AlmacenarOrdenLista(orden_id)

    print("Input generado OK")

    return 0
