import time
import requests

DIA = 20211125
lat = -34.249801
lon = -58.880148
data = {
    "dia": DIA,
    "lat": lat,
    "lon": lon
}
# Crear orden
r = requests.post(
    "http://localhost:8000/api/v1/orden",
    json=data
)
print("POST:", r.status_code, r.text)
if r.status_code != 200:
    raise Exception("Error al crear la orden")
respuesta = r.json()

orden_id = respuesta["id"]
estado = respuesta["status"]

print(f"Orden {orden_id} creada. Estado: {estado}")

# Consultar estado cada 1 segundo
while True:
    r = requests.get(
        f"http://localhost:8000/api/v1/orden/{orden_id}"
    )
    if r.status_code != 200:
        print("Error consultando estado:", r.status_code)
        break
    print(r.json())
    time.sleep(1)

print("Ejecución terminada")
