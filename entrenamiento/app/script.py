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
#def run(dia_de_la_imagen="20260318", izquierda=-58.745420, derecha=-58.738993, abajo=-34.631716, arriba=-34.628794, orden_id=None):
def run(dia_de_la_imagen, lat, lon, orden_id=None):



    client_id = os.getenv("client_id")
    client_secret = os.getenv("client_secret")
    email_user = os.getenv("email_user")
    email_password = os.getenv("email_password")

    fecha_base = datetime.strptime(dia_de_la_imagen, "%Y%m%d").replace(tzinfo=UTC)




    start_date = (fecha_base - timedelta(days=40)).strftime("%Y-%m-%dT00:00:00.000Z")
    end_date = fecha_base.strftime("%Y-%m-%dT00:00:00.000Z")
    #start_date = (fecha_base - timedelta(days=40)).strftime("%Y-%m-%dT00:00:00Z")
    #end_date = fecha_base.strftime("%Y-%m-%dT00:00:00Z")

    # bounding box chico
    lat_buffer = 0.009
    lon_buffer = 0.011

    izquierda = lon - lon_buffer
    derecha = lon + lon_buffer
    abajo = lat - lat_buffer
    arriba = lat + lat_buffer

    poligono = f"{izquierda} {abajo},{izquierda} {arriba},{derecha} {arriba},{derecha} {abajo},{izquierda} {abajo}"

    poligono_geojson = {
            "type": "Polygon",
            "coordinates": [[
                [izquierda, arriba],
                [derecha, arriba],
                [derecha, abajo],
                [izquierda, abajo],
                [izquierda, arriba]
                ]]
            }

    # ================= TOKEN =================
    token_url = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"

    response = requests.post(token_url, data={
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
        })
    #access_token = ""
    access_token = response.json()["access_token"]
    print("A")
    #if (access_token == ""):
    #    print("No hay respuesta")
    #print(access_token)
    headers = {"Authorization": f"Bearer {access_token}"}

    # ================= BUSQUEDA =================
    url = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"

    #params = {
           # "$filter": (
             #   "Collection/Name eq 'SENTINEL-2' "
            #    "and Attributes/OData.CSC.StringAttribute/any(a: a/Name eq 'productType' and a/Value eq 'S2MSI2A') "
           #     f"and ContentDate/Start gt {start_date} "
          #      f"and ContentDate/Start lt {end_date} "
         #       "and OData.CSC.Intersects(area=geography'SRID=4326;"
        #        f"POLYGON(({poligono}))') "
       #         ),
      #      "$top": 5,
     #       "$orderby": "ContentDate/Start desc"
    #        }
    
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
    print("STATUS:", response.status_code)
    print("URL FINAL:", response.url)
    #print("TEXT:")
    #print(response.text[:3000])
    products = response.json().get("value", [])

    if len(products) == 0:
        print("Sin imágenes")
        return None, None

    # ================= LOGIN DESCARGA =================
    response = requests.get(token_url, data={
        "grant_type": "password",
        "client_id": "cdse-public",
        "username": email_user,
        "password": email_password
        })
    print("B")
    access_token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    os.makedirs("descargas", exist_ok=True)
    os.makedirs("data", exist_ok=True)

    rutas_safe = []
    fechas = []

    # ================= DESCARGA =================
    for p in products:
        product_id = p["Id"]
        name = p["Name"]
        fecha_img = datetime.fromisoformat(p["ContentDate"]["Start"].replace("Z", "+00:00"))

        fechas.append(fecha_img)

        zip_path = f"descargas/{name}.zip"

        if not os.path.exists(zip_path):
            url = f"https://download.dataspace.copernicus.eu/odata/v1/Products({product_id})/$value"
            with requests.get(url, headers=headers, stream=True) as r:
                with open(zip_path, "wb") as f:
                    for chunk in r.iter_content(8192):
                        f.write(chunk)

        # extraer
        with zipfile.ZipFile(zip_path, 'r') as z:
            z.extractall("data")

    # ================= NORMALIZACION FECHA =================
    fecha_min = min(fechas)
    fecha_max = max(fechas)

    def norm_fecha(f):
        if fecha_max == fecha_min:
            return 0
        return (f - fecha_min).total_seconds() / (fecha_max - fecha_min).total_seconds()

    bandas_stack = []

    # ================= PROCESAMIENTO POR IMAGEN =================
    for idx, p in enumerate(products):

        fecha_img = datetime.fromisoformat(p["ContentDate"]["Start"].replace("Z", "+00:00"))
        fecha_norm = norm_fecha(fecha_img)

        # buscar bandas dentro de SAFE
        B04 = None
        B08 = None
        B11 = None
        SCL = None

        for root, _, files in os.walk("data"):
            for f in files:
                if p["Name"] in root and f.endswith(".jp2"):
                    if "B04_10m" in f:
                        B04 = os.path.join(root, f)
                    if "B08_10m" in f:
                        B08 = os.path.join(root, f)
                    if "B11_20m" in f:
                        B11 = os.path.join(root, f)
                    if "SCL_20m" in f:
                        SCL = os.path.join(root, f)

        if not all([B04, B08, B11, SCL]):
            continue

        # abrir
        with rasterio.open(B08) as nir:
            nir_data = nir.read(1).astype("float32")
            profile = nir.profile

        with rasterio.open(B04) as red:
            red_data = red.read(1).astype("float32")

        with rasterio.open(B11) as swir:
            swir_data = swir.read(
                    1,
                    out_shape=nir_data.shape,
                    resampling=Resampling.bilinear
                    ).astype("float32")

        with rasterio.open(SCL) as scl:
            scl_data = scl.read(
                    1,
                    out_shape=nir_data.shape,
                    resampling=Resampling.nearest
                    )

        def idx(a, b):
            return np.divide(a - b, a + b, out=np.zeros_like(a), where=(a + b) != 0)

        ndvi = idx(nir_data, red_data)
        nbr = idx(nir_data, swir_data)
        ndbi = idx(swir_data, nir_data)

        # máscara de nubes
        nubes = np.isin(scl_data, [8, 9, 10]).astype("float32")

        fecha_band = np.full(ndvi.shape, fecha_norm, dtype="float32")

        bandas_stack.extend([
            ndvi, nbr, ndbi, nubes, fecha_band
            ])

    if len(bandas_stack) < 25:
        print("No hay suficientes imágenes útiles")
        return None, None

    # ================= STACK FINAL =================
    profile.update(count=25, dtype="float32")

    os.makedirs("dataset/train/inputs", exist_ok=True)
    os.makedirs("dataset/train/masks", exist_ok=True)

    ruta_stack = f"dataset/train/inputs/escena_{orden_id}.tif"

    with rasterio.open(ruta_stack, "w", **profile) as dst:
        for i in range(25):
            dst.write(bandas_stack[i], i + 1)

    # ================= MASK (INCENDIO PROXY) =================
    nbr_last = bandas_stack[-5 + 1]  # NBR de última imagen
    incendio = (nbr_last < 0.1).astype("uint8")

    profile.update(count=1, dtype="uint8")

    ruta_mask = f"dataset/train/masks/escena_{orden_id}.tif"

    with rasterio.open(ruta_mask, "w", **profile) as dst:
        dst.write(incendio, 1)

    print("Dataset generado OK")

    return ruta_stack, ruta_mask

# ==================================================
# PARA EJECUTAR SOLO (modo prueba)
# ==================================================
if __name__ == "__main__":
    ruta_safe, ruta_stack = run()
    print(f"Ruta SAFE: {ruta_safe}")
    print(f"Ruta Stack: {ruta_stack}")
