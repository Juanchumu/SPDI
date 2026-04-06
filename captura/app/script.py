# imports
from dotenv import load_dotenv

load_dotenv()

#print(f"Email user: {os.getenv('email_user')}")
#print(f"Email password: {'*' * len(os.getenv('email_password', ''))}")

import requests
from datetime import datetime, timedelta, UTC
import os
import zipfile

import rasterio
from rasterio.merge import merge
from rasterio.mask import mask

import matplotlib.pyplot as plt
from rasterio.enums import Resampling
import numpy as np
import pyproj
from shapely.geometry import shape
from shapely.ops import transform

print("imports cargados...!")

# ==================================================
# FUNCIÓN PRINCIPAL que recibe los 5 argumentos
# ==================================================
#def run(dia_de_la_imagen="20260318", izquierda=-58.745420, derecha=-58.738993, abajo=-34.631716, arriba=-34.628794, orden_id=None):
def run(dia_de_la_imagen, izquierda, derecha, abajo, arriba, orden_id):

    """
    Recibe 5 argumentos:
    - dia_de_la_imagen: str con formato YYYYMMDD
    - izquierda: float (longitud oeste)
    - derecha: float (longitud este)
    - abajo: float (latitud sur)
    - arriba: float (latitud norte)
    - orden_id: int (opcional, para asociar las rutas)
    
    Devuelve: (ruta_safe, ruta_stack)
    """
    
    # Credenciales (levantadas del .env)
    client_id = os.getenv("client_id")
    client_secret = os.getenv("client_secret")
    email_user = os.getenv("email_user")
    email_password = os.getenv("email_password")
    
    # Convertir string a datetime
    fecha_base = datetime.strptime(dia_de_la_imagen, "%Y%m%d").replace(tzinfo=UTC)
    start_date = (fecha_base - timedelta(days=10)).strftime("%Y-%m-%dT00:00:00Z")
    end_date = (fecha_base + timedelta(days=5)).strftime("%Y-%m-%dT00:00:00Z")
    
    # Polígono
    poligono = f"{izquierda} {abajo},{izquierda} {arriba},{derecha} {arriba},{derecha} {abajo},{izquierda} {abajo}"
    
    poligono2 = {
        "type": "Polygon",
        "coordinates": [[
            [izquierda, arriba],
            [derecha, arriba],
            [derecha, abajo],
            [izquierda, abajo],
            [izquierda, arriba]
        ]]
    }
    
    # Obtener tokens
    token_url = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
    
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }
    
    response = requests.post(token_url, data=data)
    access_token = response.json()["access_token"]
    
    print("TOKEN OK")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    url = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
    params = {
        "$filter": (
            "Collection/Name eq 'SENTINEL-2' "
            "and Attributes/OData.CSC.StringAttribute/any(a: a/Name eq 'productType' and a/Value eq 'S2MSI2A') "
            f"and ContentDate/Start gt {start_date} "
            f"and ContentDate/Start lt {end_date} "
            "and OData.CSC.Intersects(area=geography'SRID=4326;"
            f"POLYGON(({poligono}))') "
            "and Attributes/OData.CSC.DoubleAttribute/any(a: a/Name eq 'cloudCover' and a/Value le 20)"
        ),
        "$top": 5,
        "$orderby": "ContentDate/Start desc"
    }
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code != 200:
        print("Error:", response.status_code, response.text)
        raise SystemExit
    
    products = response.json().get("value", [])
    
    if len(products) == 0:
        print("No hay imagenes disponibles en el area")
        return None, None
    
    print("Imagenes Disponibles en el area.")
    
    for p in products:
        product_id = p["Id"]
        name = p["Name"]
        fecha = p["ContentDate"]["Start"]
        print(product_id, name)
    
    # Token para descarga
    data = {
        "grant_type": "password",
        "client_id": "cdse-public",
        "username": email_user,
        "password": email_password
    }
    
    response = requests.post(token_url, data=data)
    token = response.json()["access_token"]
    access_token = token
    
    # Descarga
    output_dir = "descargas"
    os.makedirs(output_dir, exist_ok=True)
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    ruta_safe = None
    
    for p in products:
        product_id = p["Id"]
        name = p["Name"] 
        filepath = os.path.join(output_dir, name + ".zip")
        if os.path.exists(filepath):
            print(f"Archivo ya existe: {name}")
        else:
            hora = datetime.now().strftime('%H:%M:%S')
            print(f"La descarga empezó a las {hora}")
            print(f"Descargando: {name}")
            url = f"https://download.dataspace.copernicus.eu/odata/v1/Products({product_id})/$value"
            with requests.get(url, headers=headers, stream=True) as r:
                if r.status_code != 200:
                    print("Error:", r.status_code, r.text)
                    continue
                
                with open(filepath, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            
            print(f"OK: {filepath}")
            print(f"La descarga Termino a las {datetime.now().strftime('%H:%M:%S')}")
        
    # Descomprimir archivos
    print(f"Descomprimir archivos {datetime.now().strftime('%H:%M:%S')}")
    zip_dir = "descargas"
    extract_dir = "data"    
    os.makedirs(extract_dir, exist_ok=True)    
    for file in os.listdir(zip_dir):
        if file.endswith(".zip"):
            path = os.path.join(zip_dir, file)
            print("Extrayendo:", file)
                
            with zipfile.ZipFile(path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
                
            # Buscar la carpeta .SAFE
            for root, dirs, files in os.walk(extract_dir):
                for d in dirs:
                    if d.endswith(".SAFE"):
                        ruta_safe = os.path.join(root, d)
                        print(f"Carpeta SAFE encontrada: {ruta_safe}")
    
    print(f"Procesamiento de bandas {datetime.now().strftime('%H:%M:%S')}")
    bandas = ["B04_10m", "B08_10m", "B11_20m"]
    rutas = []
    
    for root, dirs, files in os.walk(extract_dir):
        for file in files:
            if file.endswith(".jp2") and dia_de_la_imagen in file and any(b in file for b in bandas):
                ruta = os.path.join(root, file)
                rutas.append(ruta)
                print("Archivo seleccionado:", ruta)
    
    for ruta in rutas:
        banda_actual = next(b for b in bandas if b in ruta)
        
        with rasterio.open(ruta) as src:
            project = pyproj.Transformer.from_crs(
                "EPSG:4326",
                src.crs,
                always_xy=True
            ).transform
            
            poly_proj = transform(project, shape(poligono2))
            
            out_image, out_transform = rasterio.mask.mask(src, [poly_proj], crop=True)
            
            out_meta = src.meta.copy()
            out_meta.update({
                "height": out_image.shape[1],
                "width": out_image.shape[2],
                "transform": out_transform
            })
        
        output_path = f"{dia_de_la_imagen}-{banda_actual}.tif"
        with rasterio.open(output_path, "w", **out_meta) as dest:
            dest.write(out_image)
        
        print("Guardado:", output_path)
    
    print(f"Encontrar archivos de banda {datetime.now().strftime('%H:%M:%S')}")
    def find_band_files(base_dir, band):
        paths = []
        for root, dirs, files in os.walk(base_dir):
            for f in files:
                if band in f and f.endswith(".tif"):
                    paths.append(os.path.join(root, f))
        return paths
    
    b4_files = find_band_files(".", "B04")
    b8_files = find_band_files(".", "B08")
    b11_files = find_band_files(".", "B11")
    
    # Mosaico
    def mosaic(files, output):
        if not files:
            print(f"No hay archivos para {output}")
            return
        
        if len(files) == 1:
            with rasterio.open(files[0]) as src:
                data = src.read(1)
                profile = src.profile.copy()
                profile.pop("blockxsize", None)
                profile.pop("blockysize", None)
                profile.pop("tiled", None)
                profile.update({
                    "count": 1,
                    "driver": "GTiff"
                })
                
                with rasterio.open(output, "w", **profile) as dst:
                    dst.write(data, 1)
            
            print(f"Copiado directo: {output}")
            return
        
        srcs = [rasterio.open(f) for f in files]
        mosaic_data, transform = merge(srcs, indexes=1)
        
        profile = srcs[0].profile.copy()
        profile.update({
            "height": mosaic_data.shape[1],
            "width": mosaic_data.shape[2],
            "transform": transform,
            "count": 1
        })
        
        with rasterio.open(output, "w", **profile) as dst:
            dst.write(mosaic_data[0], 1)
        
        for src in srcs:
            src.close()
        
        print(f"Mosaico creado: {output}")
    
    # Filtrar por fecha
    b4_files = [f for f in b4_files if dia_de_la_imagen in f]
    b8_files = [f for f in b8_files if dia_de_la_imagen in f]
    b11_files = [f for f in b11_files if dia_de_la_imagen in f]
    
    mosaic(b4_files, "B4_mosaic.tif")
    mosaic(b8_files, "B8_mosaic.tif")
    mosaic(b11_files, "B11_mosaic.tif")
    
    MMO_tipo = 'float64'
    
    with rasterio.open("B8_mosaic.tif") as nir:
        nir_data = nir.read(1).astype(MMO_tipo)
        profile = nir.profile.copy()
        
        with rasterio.open("B11_mosaic.tif") as swir:
            swir_resampled = swir.read(
                1,
                out_shape=nir.shape,
                resampling=Resampling.bilinear
            ).astype(MMO_tipo)
    
    with rasterio.open("B4_mosaic.tif") as red:
        red_data = red.read(1).astype(MMO_tipo)
    
    def safe_index(a, b):
        denom = a + b
        return np.divide(
            (a - b),
            denom,
            out=np.zeros_like(a, dtype=float),
            where=denom != 0
        )
    
    ndvi = safe_index(nir_data, red_data)
    nbr = safe_index(nir_data, swir_resampled)
    ndbi = safe_index(swir_resampled, nir_data)
    
    profile.update(dtype=rasterio.float64, count=1)
    
    with rasterio.open(f"{dia_de_la_imagen}-nbr.tif", "w", **profile) as dst:
        dst.write(nbr.astype(rasterio.float64), 1)
    
    with rasterio.open(f"{dia_de_la_imagen}-ndvi.tif", "w", **profile) as dst:
        dst.write(ndvi.astype(rasterio.float64), 1)
    
    with rasterio.open(f"{dia_de_la_imagen}-ndbi.tif", "w", **profile) as dst:
        dst.write(ndbi.astype(rasterio.float64), 1)
    
    critical = nbr < 0.1
    
    with rasterio.open("B8_mosaic.tif") as src:
        profile_crit = src.profile
    
    profile_crit.update(dtype=rasterio.uint8)
    
    with rasterio.open(f"{dia_de_la_imagen}-zonas_criticas.tif", "w", **profile_crit) as dst:
        dst.write(critical.astype(rasterio.uint8), 1)
    
    # Stack final
    with rasterio.open(f"{dia_de_la_imagen}-ndvi.tif") as ndvi_src, \
         rasterio.open(f"{dia_de_la_imagen}-nbr.tif") as nbr_src, \
         rasterio.open(f"{dia_de_la_imagen}-ndbi.tif") as ndbi_src:
        
        ndvi_data = ndvi_src.read(1)
        nbr_data = nbr_src.read(1)
        ndbi_data = ndbi_src.read(1)
        
        profile_stack = ndvi_src.profile.copy()
        profile_stack.update(count=3)
        
        #ruta_stack = f"{dia_de_la_imagen}-{order_id}-stack.tif"
        ruta_stack = os.path.join("data", f"{dia_de_la_imagen}-{orden_id}-stack.tif")
        with rasterio.open(ruta_stack, "w", **profile_stack) as dst:
            dst.write(ndvi_data, 1)
            dst.write(nbr_data, 2)
            dst.write(ndbi_data, 3)
    
    print(f"Stack generado: {ruta_stack}")
    
    return ruta_safe, ruta_stack


# ==================================================
# PARA EJECUTAR SOLO (modo prueba)
# ==================================================
if __name__ == "__main__":
    ruta_safe, ruta_stack = run()
    print(f"Ruta SAFE: {ruta_safe}")
    print(f"Ruta Stack: {ruta_stack}")
