import csv
import time
import requests

DIA = 20211125
i = 0
with open("20211124.csv") as f:
    reader = csv.DictReader(f)
    for row in reader:
        data = {
            "dia": DIA,
            "lat": float(row["lat"]),
            "lon": float(row["lon"])
        }
        i = i + 1
        if i < 14:
            r = requests.post("http://localhost:8000/api/v1/generar_datos", json=data)
            print(r.status_code, data, r.json())
            time.sleep(1000)
