import random
import json
from datetime import datetime, timedelta
import os
import psycopg2

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")

# ==========================================
# CONEXIÓN
# ==========================================

conn = psycopg2.connect(
    host=DB_HOST,
    #port=5432,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD
)

cur = conn.cursor()


# ==========================================
# DATOS ALEATORIOS
# ==========================================

estados = ["Pendiente", "Procesando", "Predicha"]

modelos = [
    "fire_model_ver_4",
    "fire_model_ver_5",
    "fire_model_ver_6"
]

for _ in range(10):

    # Coordenadas aproximadas en Buenos Aires
    lat = round(random.uniform(-35.0, -34.0), 6)
    lon = round(random.uniform(-59.5, -58.0), 6)

    dia = str(random.randint(20200101, 20241231))

    args = {
        "dia_de_la_imagen": dia,
        "lat": lat,
        "lon": lon
    }

    status = random.choice(estados)
    modelo = random.choice(modelos)

    if status == "Predicha":
        prediccion = {
            "riesgo": random.choice(["bajo", "medio", "alto"]),
            "porcentaje_area_riesgo": round(random.uniform(0, 100), 2),
            "zonas_criticas": [
                {
                    "x1": random.randint(0, 100),
                    "y1": random.randint(0, 100),
                    "x2": random.randint(101, 256),
                    "y2": random.randint(101, 256),
                    "pixels": random.randint(1000, 50000)
                }
            ],
            "archivo_prediccion": f"pred_{random.randint(1,999)}.tif"
        }
    else:
        prediccion = None

    created_at = datetime.now() - timedelta(
        days=random.randint(0, 30),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59)
    )

    updated_at = created_at + timedelta(
        minutes=random.randint(1, 120)
    )

    cur.execute(
        """
        INSERT INTO ordenes (
            args,
            status,
            prediccion,
            modelo_utilizado,
            created_at,
            updated_at
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (
            json.dumps(args),
            status,
            json.dumps(prediccion) if prediccion else None,
            modelo,
            created_at,
            updated_at
        )
    )

conn.commit()
cur.close()
conn.close()

print("Se insertaron 10 órdenes.")
