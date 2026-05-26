# ==================================================
# IMPORTS
# ==================================================

import os
import numpy as np
import rasterio

from datetime import datetime, timedelta, UTC

import planetary_computer
import pystac_client

from odc.stac import stac_load

from minio import Minio

from db.db import SessionLocal
from db.models import Descargas


print("imports cargados...!")


# ==================================================
# ALMACENAR DESCARGA
# ==================================================
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
        f"{nombre}.tif",
        f"/app/dataset/train/inputs/{nombre}.tif"
    )

    print(f"Archivo {nombre} subido")


# ==================================================
# FUNCION AUXILIAR
# ==================================================
def idx(a, b):

    return np.divide(
        a - b,
        a + b,
        out=np.zeros_like(a),
        where=(a + b) != 0
    )


# ==================================================
# FUNCION PRINCIPAL
# ==================================================
def run(dia_de_la_imagen, lat, lon, orden_id):

    fecha_base = datetime.strptime(
        dia_de_la_imagen,
        "%Y%m%d"
    ).replace(tzinfo=UTC)

    fecha_inicio = (
        fecha_base - timedelta(days=40)
    ).strftime("%Y-%m-%d")

    fecha_fin = fecha_base.strftime("%Y-%m-%d")

    # ==================================================
    # DIRECTORIOS
    # ==================================================
    os.makedirs("/app/dataset/train/inputs", exist_ok=True)
    os.makedirs("/app/dataset/train/masks", exist_ok=True)

    # ==================================================
    # BBOX
    # ==================================================
    lat_buffer = 0.009
    lon_buffer = 0.011

    izquierda = lon - lon_buffer
    derecha = lon + lon_buffer
    abajo = lat - lat_buffer
    arriba = lat + lat_buffer

    bbox = [
        izquierda,
        abajo,
        derecha,
        arriba
    ]

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
        limit=6
    )

    items = list(search.items())

    # ==================================================
    # ORDENAR POR FECHA DESCENDENTE
    # ==================================================
    items.sort(
        key=lambda x: x.datetime,
        reverse=True
    )

    # ==================================================
    # USAR SOLO 4
    # item[0] = mask
    # item[1:] = stack
    # ==================================================
    items = items[:4]

    if len(items) < 4:
        print("No hay suficientes imagenes")
        return 1

    print(f"Hay {len(items)} imagenes")

    # ==================================================
    # SEPARAR MASK Y STACK
    # ==================================================
    item_mask = items[0]

    items_stack = items[1:]

    bandas_stack = []

    profile = None

    # ==================================================
    # STACK
    # ==================================================
    for item in items_stack:

        product_id = item.id

        fecha_img = item.datetime

        print(f"Procesando stack: {product_id}")

        # ==================================================
        # CARGAR BANDAS
        # ==================================================
        ds = stac_load(
            [item],
            bands=[
                "red",
                "nir",
                "swir16",
                "SCL"
            ],
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
        ndvi = idx(nir_data, red_data)

        nbr = idx(nir_data, swir_data)

        ndbi = idx(swir_data, nir_data)

        nubes = np.isin(
            scl_data,
            [8, 9, 10]
        ).astype("float32")

        # ==================================================
        # FECHA NORMALIZADA
        # ==================================================
        dia_del_anio = fecha_img.timetuple().tm_yday

        dias_en_el_anio = (
            366
            if (
                fecha_img.year % 4 == 0
                and (
                    fecha_img.year % 100 != 0
                    or fecha_img.year % 400 == 0
                )
            )
            else 365
        )

        fecha_norm = (
            dia_del_anio - 1
        ) / (
            dias_en_el_anio - 1
        )

        fecha_band = np.full(
            ndvi.shape,
            fecha_norm,
            dtype="float32"
        )

        # ==================================================
        # AGREGAR BANDAS
        # ==================================================
        bandas_stack.extend([
            ndvi,
            nbr,
            ndbi,
            nubes,
            fecha_band
        ])

        # ==================================================
        # PERFIL
        # ==================================================
        transform = ds.odc.geobox.transform

        profile = {
            "driver": "GTiff",
            "height": ndvi.shape[0],
            "width": ndvi.shape[1],
            "count": 15,
            "dtype": "float32",
            "crs": ds.odc.crs,
            "transform": transform
        }

    # ==================================================
    # VALIDAR STACK
    # ==================================================
    if len(bandas_stack) != 15:
        print("Stack incompleto")
        return 1

    # ==================================================
    # GUARDAR STACK
    # ==================================================
    ruta_stack = (
        f"/app/dataset/train/inputs/"
        f"escena_{orden_id}.tif"
    )

    with rasterio.open(
        ruta_stack,
        "w",
        **profile
    ) as dst:

        for i in range(len(bandas_stack)):
            dst.write(
                bandas_stack[i],
                i + 1
            )

    print("Stack generado OK")

    # ==================================================
    # GENERAR MASK
    # ==================================================
    print(f"Procesando mask: {item_mask.id}")

    ds = stac_load(
        [item_mask],
        bands=[
            "nir",
            "swir16"
        ],
        bbox=bbox,
        resolution=10,
        chunks={},
        dtype="uint16"
    ).isel(time=0)

    nir_data = ds["nir"].values.astype("float32")

    swir_data = ds["swir16"].values.astype("float32")

    # ==================================================
    # NBR MASK
    # ==================================================
    nbr_mask = idx(
        nir_data,
        swir_data
    )

    incendio = (
        nbr_mask < 0.1
    ).astype("uint8")

    # ==================================================
    # PERFIL MASK
    # ==================================================
    transform = ds.odc.geobox.transform

    profile_mask = {
        "driver": "GTiff",
        "height": incendio.shape[0],
        "width": incendio.shape[1],
        "count": 1,
        "dtype": "uint8",
        "crs": ds.odc.crs,
        "transform": transform
    }

    # ==================================================
    # GUARDAR MASK
    # ==================================================
    ruta_mask = (
        f"/app/dataset/train/masks/"
        f"escena_{orden_id}.tif"
    )

    with rasterio.open(
        ruta_mask,
        "w",
        **profile_mask
    ) as dst:

        dst.write(
            incendio,
            1
        )

    print("Mask generada OK")

    # ==================================================
    # DB + MINIO
    # ==================================================
    #AlmacenarDescarga(f"escena_{orden_id}",dia_de_la_imagen)

    print("Dataset generado OK")

    return 0
