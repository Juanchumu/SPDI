from datetime import datetime, timedelta, UTC
from shapely.geometry import box
import geopandas as gpd


# ==================================================
# FUNCIÓN PRINCIPAL
# ==================================================
def run(dia_de_la_imagen, lat, lon, orden_id):

    # ==================================================
    # Validar Fecha
    # ==================================================
    fecha_base = datetime.strptime(dia_de_la_imagen, "%Y%m%d").replace(tzinfo=UTC)

    # si la fecha es mayor a 5 días respecto al sistema
    fecha_limite = datetime.now(UTC) - timedelta(days=5)

    if fecha_base > fecha_limite:
        return 1

    # ==================================================
    # Validar Lat-Lon
    # ==================================================
    lat_buffer = 0.009
    lon_buffer = 0.011

    izquierda = lon - lon_buffer
    derecha = lon + lon_buffer
    abajo = lat - lat_buffer
    arriba = lat + lat_buffer

    bbox = [izquierda, abajo, derecha, arriba]

    # crear polígono bbox
    bbox_polygon = box(izquierda, abajo, derecha, arriba)

    # cargar polígono de Argentina
    argentina = gpd.read_file("/app/argentina.geojson")

    # unir todos los polígonos en uno solo
    argentina_polygon = argentina.union_all()

    # verificar si el bbox está completamente dentro de Argentina
    if not argentina_polygon.contains(bbox_polygon):
        return 2

    # si todo está bien
    return 0
