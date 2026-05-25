# imports
from dotenv import load_dotenv

import os
import zipfile
import numpy as np
import rasterio
from rasterio.enums import Resampling
from datetime import datetime, timedelta, UTC

import planetary_computer
import pystac_client
from odc.stac import stac_load

from minio import Minio

from app.db import SessionLocal
from app.models import Descargas

load_dotenv()
print("imports cargados...!")


def AlmacenarDescarga(nombre, dia):
    db = SessionLocal()

    nuevoArchivo = Descargas(
        nombre_imagen=nombre,
        dia_de_la_imagen=dia
    )

    db.add(nuevoArchivo)
    db.commit()
    db.close()

    client = Minio(
        "localhost:9000",
        access_key=os.getenv("DB_MINIO_USER"),
        secret_key=os.getenv("DB_MINIO_PASS"),
        secure=False
    )

    bucket_name = "imagenes"

    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)
        print("Bucket para las imagenes creado")

    client.fput_object(
        "imagenes",
        f"{nombre}.zip",
        f"tmp/descargas/{nombre}.zip"
    )

    print(f"Archivo {nombre} subido")


def ConsultarDescargas():
    db = SessionLocal()

    productos_descargados = db.query(Descargas).all()
    lista = {x.nombre_imagen for x in productos_descargados}

    db.commit()
    db.close()

    return lista


def TraerDeMiniO(nombre):
    client = Minio(
        "localhost:9000",
        access_key=os.getenv("DB_MINIO_USER"),
        secret_key=os.getenv("DB_MINIO_PASS"),
        secure=False
    )

    client.fget_object(
        "imagenes",
        f"{nombre}.zip",
        f"tmp/descargas/{nombre}.zip"
    )

    print("Archivo descargado")


# ==================================================
# FUNCIÓN PRINCIPAL
# ==================================================
def run(dia_de_la_imagen, lat, lon, orden_id):

    fecha_base = datetime.strptime(dia_de_la_imagen, "%Y%m%d").replace(tzinfo=UTC)

    fecha_inicio = (fecha_base - timedelta(days=40)).strftime("%Y-%m-%d")
    fecha_fin = fecha_base.strftime("%Y-%m-%d")

    os.makedirs("tmp/descargas", exist_ok=True)
    os.makedirs("tmp/data", exist_ok=True)
    os.makedirs("ordenes/inputs", exist_ok=True)

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
        limit=5
    )

    items = list(search.items())
    print("lista")
    print(items)
    # ordenar por fecha descendente
    items.sort(
        key=lambda x: x.datetime,
        reverse=True
    )

    items = items[:5]

    if len(items) == 0:
        print("Sin imágenes")
        # Esto tendria que devolver un error o 
        # intentar mas tarde debido a la api 
        return None

    print(f"Hay {len(items)} imagenes")

    fechas = []
    bandas_stack = []

    # ==================================================
    # CACHE / MINIO
    # ==================================================
    listaProductosDescargados = ConsultarDescargas()

    print(f"Se consulto la db, hay {len(listaProductosDescargados)} elementos")

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
        # NORMALIZACION FECHA
        # ==================================================
        fecha_min = min([x.datetime for x in items])
        fecha_max = max([x.datetime for x in items])

        if fecha_max == fecha_min:
            fecha_norm = 0
        else:
            fecha_norm = (
                (fecha_img - fecha_min).total_seconds()
                / (fecha_max - fecha_min).total_seconds()
            )

        fecha_band = np.full(
            ndvi.shape,
            fecha_norm,
            dtype="float32"
        )

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

    if len(bandas_stack) == 0:
        print("No hay datos válidos")
        return None

    # ==================================================
    # GUARDAR STACK
    # ==================================================
    ruta_stack = f"ordenes/inputs/{orden_id}.tif"

    profile["count"] = len(bandas_stack)

    with rasterio.open(ruta_stack, "w", **profile) as dst:

        for i in range(len(bandas_stack)):
            dst.write(bandas_stack[i], i + 1)

    print("Input generado OK")

    return ruta_stack
