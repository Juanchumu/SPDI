import csv
import requests

DIA = 20211125

with open("a2.csv") as f:
    reader = csv.DictReader(f)
    for row in reader:
        data = {
            "dia": DIA,
            "lat": float(row["lat"]),
            "lon": float(row["lon"])
        }
        r = requests.post("http://10.11.11.20:8001/api/v1/generar_datos", json=data)
        print(r.status_code, data)
