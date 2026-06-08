import requests
import fitz
import pandas as pd
import re
import time
import json

URL_CSV = 'https://docs.google.com/spreadsheets/d/16a46lWfOAgNoOn13433JpL6b3GvIY5neCtRSJEclEfM/export?format=csv'
API_URL = 'http://localhost:8000/api/v1/orden'
VALID_PROVINCES = ['BUENOS AIRES', 'CÓRDOBA', 'CORDOBA', 'LA PAMPA', 'ENTRE RÍOS', 'ENTRE RIOS', 'SANTA FE', 'CORRIENTES', 'MISIONES', 'RÍO NEGRO', 'RIO NEGRO', 'CHUBUT']

def dms_to_decimal(degrees, minutes, seconds):
    minutes = float(minutes.replace(',', '.'))
    seconds = float(seconds.replace(',', '.'))
    return -(float(degrees) + minutes/60 + seconds/3600)

def main():
    print("Descargando indice de reportes...")
    df = pd.read_csv(URL_CSV)
    
    fires = []
    
    # Expresiones regulares para Lat/Lon
    # Ej: Latitud: 27º 50,76´ 00´´
    regex_lat = re.compile(r'Latitud:\s*(\d+)[º°]\s*(\d+(?:,\d+)?)´\s*(\d+(?:,\d+)?)´´')
    regex_lon = re.compile(r'Longitud:\s*(\d+)[º°]\s*(\d+(?:,\d+)?)´\s*(\d+(?:,\d+)?)´´')
    
    # Iterate backwards to get newer reports or randomly
    for idx, row in df.iterrows():
        if len(fires) >= 5:
            break
            
        pdf_url = row.get('btn-descargar') or row.get('Reporte')
        fecha_str = str(row.get('ver-fecha') or row.get('Fecha'))
        
        if pd.isna(pdf_url) or not pdf_url.endswith('.pdf'):
            continue
            
        try:
            resp = requests.get(pdf_url, timeout=5)
            if resp.status_code != 200: continue
            
            doc = fitz.open(stream=resp.content, filetype='pdf')
            text = doc[0].get_text()
            
            if 'No se reportaron' in text: continue
            
            # Buscar coordenadas
            lat_match = regex_lat.search(text)
            lon_match = regex_lon.search(text)
            
            if lat_match and lon_match:
                lat = dms_to_decimal(*lat_match.groups())
                lon = dms_to_decimal(*lon_match.groups())
                
                # Intentar adivinar la provincia (suele estar arriba de la fecha)
                prov = "DESCONOCIDA"
                for p in VALID_PROVINCES:
                    if p in text.upper():
                        prov = p
                        break
                
                # Transformar fecha a YYYYMMDD para la API (ej "25 de octubre de 2018")
                # Un truco rápido es buscar la fecha en formato DD/MM/YYYY en el texto
                fecha_match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', text)
                if fecha_match:
                    d, m, y = fecha_match.groups()
                    dia_api = f"{y}{int(m):02d}{int(d):02d}"
                else:
                    dia_api = "20181025" # fallback
                
                print(f"Encontrado: {prov} - Lat: {lat:.4f}, Lon: {lon:.4f} - Fecha: {dia_api}")
                fires.append({
                    "provincia": prov,
                    "lat": lat,
                    "lon": lon,
                    "dia": int(dia_api),
                    "estado_real": "Fuego activo/contenido"
                })
        except Exception as e:
            continue

    print(f"\nGenerando predicciones para {len(fires)} incendios...")
    resultados = []
    
    for f in fires:
        # Enviar orden
        payload = {"dia": f["dia"], "lat": f["lat"], "lon": f["lon"]}
        try:
            r = requests.post(API_URL, json=payload)
            if r.status_code == 201:
                orden_id = r.json()["id"]
                # Esperar hasta que esté Predicha (timeout de 2 min)
                for _ in range(24): # 24 * 5s = 120s
                    time.sleep(5)
                    r_status = requests.get(f"{API_URL}/{orden_id}")
                    if r_status.status_code == 200:
                        data = r_status.json()
                        if isinstance(data, dict) and data.get("status") == "Predicha":
                            prediccion = data.get("prediccion")
                            f["prediccion_modelo"] = prediccion
                            print(f"Orden {orden_id} completada: Predicción = {prediccion}")
                            break
                if "prediccion_modelo" not in f:
                    f["prediccion_modelo"] = "TIMEOUT"
            else:
                f["prediccion_modelo"] = "ERROR_API"
        except Exception as e:
            f["prediccion_modelo"] = f"ERROR: {e}"
            
        resultados.append(f)
        
    # Escribir reporte markdown
    with open('reporte_evaluacion.md', 'w') as f:
        f.write("# Reporte de Evaluación de Incendios Históricos (SNMF)\n\n")
        f.write("| Provincia | Fecha (YYYYMMDD) | Latitud | Longitud | Predicción Modelo |\n")
        f.write("|---|---|---|---|---|\n")
        for r in resultados:
            pred = r.get("prediccion_modelo", "N/A")
            f.write(f"| {r['provincia']} | {r['dia']} | {r['lat']:.4f} | {r['lon']:.4f} | {pred} |\n")
            
    print("\nProceso terminado. Reporte guardado en reporte_evaluacion.md")

if __name__ == '__main__':
    main()
