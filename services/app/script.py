# imports
from dotenv import load_dotenv


import requests
import os
import zipfile
import numpy as np
import rasterio
from rasterio.merge import merge
from rasterio.mask import mask
from rasterio.enums import Resampling
from datetime import datetime, timedelta, UTC
import pyproj
from shapely.geometry import shape
from shapely.ops import transform

load_dotenv()
print("imports cargados...!")

# ==================================================
# FUNCIÓN PRINCIPAL que recibe los 5 argumentos
# ==================================================
def run(dia_de_la_imagen, lat, lon, orden_id):

    client_id = os.getenv("client_id")
    client_secret = os.getenv("client_secret")
    email_user = os.getenv("email_user")
    email_password = os.getenv("email_password")

    fecha_base = datetime.strptime(dia_de_la_imagen, "%Y%m%d").replace(tzinfo=UTC)

    start_date = (fecha_base - timedelta(days=40)).strftime("%Y-%m-%dT00:00:00.000Z")
    end_date = fecha_base.strftime("%Y-%m-%dT00:00:00.000Z")

    # bounding box
    lat_buffer = 0.009
    lon_buffer = 0.011

    izquierda = lon - lon_buffer
    derecha = lon + lon_buffer
    abajo = lat - lat_buffer
    arriba = lat + lat_buffer

    poligono = f"{izquierda} {abajo},{izquierda} {arriba},{derecha} {arriba},{derecha} {abajo},{izquierda} {abajo}"

    # ================= TOKEN (client credentials) =================
    token_url = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"

    response = requests.post(token_url, data={
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    })

    access_token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # ================= BUSQUEDA =================
    url = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"

    params = {
        "$filter": (
            "Collection/Name eq 'SENTINEL-2' "
            "and Attributes/OData.CSC.StringAttribute/any(a: a/Name eq 'productType' and a/Value eq 'S2MSI2A') "
            f"and ContentDate/Start gt {start_date} "
            f"and ContentDate/Start lt {end_date} "
            "and OData.CSC.Intersects(area=geography'SRID=4326;"
            f"POLYGON(({poligono}))') "
            "and Attributes/OData.CSC.DoubleAttribute/any(a: a/Name eq 'cloudCover' and a/Value le 100)"
        ),
        "$top": 5,
        "$orderby": "ContentDate/Start desc"
    }

    response = requests.get(url, headers=headers, params=params)
    products = response.json().get("value", [])

    if len(products) == 0:
        print("Sin imágenes")
        return None

    # ================= TOKEN DESCARGA =================
    response = requests.post(token_url, data={
        "grant_type": "password",
        "client_id": "cdse-public",
        "username": email_user,
        "password": email_password
    })

    access_token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    os.makedirs("tmp/descargas", exist_ok=True)
    os.makedirs("tmp/data", exist_ok=True)
    os.makedirs("ordenes/inputs", exist_ok=True)

    fechas = []
    bandas_stack = []

    # ================= DESCARGA =================
    for p in products:
        product_id = p["Id"]
        name = p["Name"]

        fecha_img = datetime.fromisoformat(p["ContentDate"]["Start"].replace("Z", "+00:00"))
        fechas.append(fecha_img)

        zip_path = f"tmp/descargas/{name}.zip"

        if not os.path.exists(zip_path):
            url = f"https://download.dataspace.copernicus.eu/odata/v1/Products({product_id})/$value"
            with requests.get(url, headers=headers, stream=True) as r:
                with open(zip_path, "wb") as f:
                    for chunk in r.iter_content(8192):
                        f.write(chunk)

        with zipfile.ZipFile(zip_path, 'r') as z:
            z.extractall("tmp/data")

    # ================= NORMALIZACION FECHA =================
    fecha_min = min(fechas)
    fecha_max = max(fechas)

    def norm_fecha(f):
        if fecha_max == fecha_min:
            return 0
        return (f - fecha_min).total_seconds() / (fecha_max - fecha_min).total_seconds()

    # ================= PROCESAMIENTO =================
    for p in products:

        fecha_img = datetime.fromisoformat(p["ContentDate"]["Start"].replace("Z", "+00:00"))
        fecha_norm = norm_fecha(fecha_img)

        B04 = B08 = B11 = SCL = None

        for root, _, files in os.walk("tmp/data"):
            for f in files:
                if p["Name"] in root and f.endswith(".jp2"):
                    if "B04_10m" in f: B04 = os.path.join(root, f)
                    if "B08_10m" in f: B08 = os.path.join(root, f)
                    if "B11_20m" in f: B11 = os.path.join(root, f)
                    if "SCL_20m" in f: SCL = os.path.join(root, f)

        if not all([B04, B08, B11, SCL]):
            continue

        with rasterio.open(B08) as nir:
            nir_data = nir.read(1).astype("float32")
            profile = nir.profile

        with rasterio.open(B04) as red:
            red_data = red.read(1).astype("float32")

        with rasterio.open(B11) as swir:
            swir_data = swir.read(1, out_shape=nir_data.shape, resampling=Resampling.bilinear).astype("float32")

        with rasterio.open(SCL) as scl:
            scl_data = scl.read(1, out_shape=nir_data.shape, resampling=Resampling.nearest)

        def idx(a, b):
            return np.divide(a - b, a + b, out=np.zeros_like(a), where=(a + b) != 0)

        ndvi = idx(nir_data, red_data)
        nbr = idx(nir_data, swir_data)
        ndbi = idx(swir_data, nir_data)
        nubes = np.isin(scl_data, [8, 9, 10]).astype("float32")
        fecha_band = np.full(ndvi.shape, fecha_norm, dtype="float32")

        bandas_stack.extend([ndvi, nbr, ndbi, nubes, fecha_band])

    if len(bandas_stack) == 0:
        print("No hay datos válidos")
        return None

    profile.update(count=len(bandas_stack), dtype="float32")

    ruta_stack = f"ordenes/inputs/{orden_id}.tif"

    with rasterio.open(ruta_stack, "w", **profile) as dst:
        for i in range(len(bandas_stack)):
            dst.write(bandas_stack[i], i + 1)

    print("Input generado OK")

    return ruta_stack
