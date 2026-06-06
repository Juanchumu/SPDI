# generate_dataset_from_shapes.py
import os
import glob
import json
import numpy as np
import rasterio
from rasterio import features
import shapefile
from shapely.geometry import shape, box
from datetime import datetime, timedelta, timezone
from pyproj import Transformer
from shapely.ops import transform as shapely_transform

import planetary_computer
import pystac_client
from odc.stac import stac_load

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "services"))
from worker.app.osm_utils import get_osm_distances

DATASET_ROOT = "tmp/dataset"
INPUTS_DIR = os.path.join(DATASET_ROOT, "inputs")
MASKS_DIR = os.path.join(DATASET_ROOT, "masks")
RAW_SHAPEFILES_DIR = "data/raw"

def ensure_dirs():
    os.makedirs(INPUTS_DIR, exist_ok=True)
    os.makedirs(MASKS_DIR, exist_ok=True)

def idx(a, b):
    return np.divide(
        a - b,
        a + b,
        out=np.zeros_like(a),
        where=(a + b) != 0
    )

def parse_date(val):
    if not val:
        return None
    if isinstance(val, (datetime, timezone)):
        return val.date()
    if hasattr(val, "year") and hasattr(val, "month") and hasattr(val, "day"):
        return val
    if isinstance(val, str):
        for fmt in ("%Y-%m-%d", "%Y%m%d", "%d/%m/%Y"):
            try:
                return datetime.strptime(val, fmt).date()
            except:
                pass
    return None

def reproject_geometry(geom, from_crs, to_crs):
    transformer = Transformer.from_crs(from_crs, to_crs, always_xy=True)
    return shapely_transform(transformer.transform, geom)

def get_candidates():
    candidates = []
    shapefile_paths = sorted(glob.glob(os.path.join(RAW_SHAPEFILES_DIR, "Superficies*.shp")))
    
    # Load argentina.geojson provinces
    geojson_path = "services/validador/app/argentina.geojson"
    provinces = []
    if os.path.exists(geojson_path):
        print(f"Loading province geometries from: {geojson_path}")
        with open(geojson_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for feature in data["features"]:
            try:
                p_geom = shape(feature["geometry"])
                p_name = feature["properties"].get("nombre", "Unknown")
                provinces.append((p_name, p_geom))
            except Exception as e:
                print(f"Error loading a province geometry: {e}")
                
    TARGET_PROVINCES = [
        "Buenos Aires", "Córdoba", "Santa Fe", "Entre Ríos", "La Pampa", 
        "San Luis", "Santiago del Estero", "Chaco", "Corrientes", "Formosa", 
        "Tucumán", "Misiones"
    ]
    print(f"Targeting agricultural & production provinces: {TARGET_PROVINCES}")
    
    for shp_path in shapefile_paths:
        year_str = "".join(filter(str.isdigit, os.path.basename(shp_path)))
        if not year_str:
            continue
        year = int(year_str)
        print(f"Reading candidates from: {shp_path}")
        
        with shapefile.Reader(shp_path) as sf:
            # Find index of fields
            fields = [f[0].lower() for f in sf.fields[1:]]
            inicio_idx = fields.index("inicio") if "inicio" in fields else -1
            hectareas_idx = fields.index("hectáreas") if "hectáreas" in fields else (fields.index("hectareas") if "hectareas" in fields else -1)
            
            for idx_rec, sr in enumerate(sf.shapeRecords()):
                if sr.shape.shapeType == 0:  # Null shape
                    continue
                
                rec = sr.record
                inicio_val = rec[inicio_idx] if inicio_idx != -1 else None
                inicio_date = parse_date(inicio_val)
                if not inicio_date:
                    continue
                
                hec_val = rec[hectareas_idx] if hectareas_idx != -1 else 0.0
                try:
                    hectareas = float(hec_val)
                except:
                    hectareas = 0.0
                
                # Filter reasonably sized fires
                if hectareas < 50.0 or hectareas > 5000.0:
                    continue
                
                try:
                    geom = shape(sr.shape.__geo_interface__)
                    centroid = geom.centroid
                    
                    # Filter by target provinces
                    prov_name = "Unknown"
                    for name, p_geom in provinces:
                        if p_geom.contains(centroid):
                            prov_name = name
                            break
                            
                    if prov_name not in TARGET_PROVINCES:
                        continue
                        
                    candidates.append({
                        "id": f"{year}_{idx_rec}",
                        "year": year,
                        "date": inicio_date,
                        "lat": centroid.y,
                        "lon": centroid.x,
                        "hectareas": hectareas,
                        "geom": geom,
                        "shp_path": shp_path,
                        "province": prov_name
                    })
                except Exception as e:
                    print(f"Error parsing geometry {idx_rec} in {shp_path}: {e}")
                    
    print(f"Total candidate fires in target provinces: {len(candidates)}")
    return candidates

def download_and_generate():
    ensure_dirs()
    candidates = get_candidates()
    if not candidates:
        print("No candidates found.")
        return
        
    # Group candidates by year and select top 15 largest per year
    by_year = {}
    for c in candidates:
        by_year.setdefault(c["year"], []).append(c)
        
    selected = []
    for year, list_c in by_year.items():
        list_c.sort(key=lambda x: x["hectareas"], reverse=True)
        selected.extend(list_c[:15]) # take 15 per year
        
    # Predefined control scenes to prevent false positives in urban, water, and bare soil areas
    control_scenes = [
        {"id": "control_buenos_aires", "hectareas": 0.0, "date": datetime(2024, 1, 15).date(), "lat": -34.6037, "lon": -58.3816, "geom": None},
        {"id": "control_cordoba", "hectareas": 0.0, "date": datetime(2024, 1, 15).date(), "lat": -31.4167, "lon": -64.1833, "geom": None},
        {"id": "control_lago_nahuel", "hectareas": 0.0, "date": datetime(2024, 1, 15).date(), "lat": -41.05, "lon": -71.45, "geom": None},
        {"id": "control_mar_chiquita", "hectareas": 0.0, "date": datetime(2024, 1, 15).date(), "lat": -30.6, "lon": -62.6, "geom": None},
        {"id": "control_campo_arado", "hectareas": 0.0, "date": datetime(2024, 1, 15).date(), "lat": -33.0, "lon": -61.0, "geom": None}
    ]
    selected.extend(control_scenes)
        
    print(f"Selected {len(selected)} fires and control scenes for dataset generation.")
    
    catalog = pystac_client.Client.open(
        "https://planetarycomputer.microsoft.com/api/stac/v1",
        modifier=planetary_computer.sign_inplace
    )
    
    success_count = 0
    for idx_sel, c in enumerate(selected):
        print(f"\n[{idx_sel+1}/{len(selected)}] Processing fire {c['id']} ({c['hectareas']:.1f} ha) on {c['date']}")
        
        # Bbox
        lat_buffer = 0.0105
        lon_buffer = 0.0135
        bbox = [c["lon"] - lon_buffer, c["lat"] - lat_buffer, c["lon"] + lon_buffer, c["lat"] + lat_buffer]
        
        fecha_inicio = (c["date"] - timedelta(days=45)).strftime("%Y-%m-%d")
        fecha_fin = c["date"].strftime("%Y-%m-%d")
        
        try:
            search = catalog.search(
                collections=["sentinel-2-l2a"],
                bbox=bbox,
                datetime=f"{fecha_inicio}/{fecha_fin}",
                query={"eo:cloud_cover": {"lte": 80}},
                limit=10
            )
            items = list(search.items())
            items.sort(key=lambda x: x.datetime, reverse=True)
            
            # We need at least 4 images: 1 post-fire/on-fire to get the CRS and transform grid, and 3 pre-fire for the stack
            if len(items) < 4:
                print(f"  -> Skipping: only found {len(items)} images (need 4)")
                continue
                
            item_mask = items[0]
            items_stack = items[1:4]
            
            print(f"  Downloading 3 pre-fire stack images...")
            bandas_stack = []
            profile = None
            
            for item in items_stack:
                ds = stac_load(
                    [item],
                    bands=["red", "nir", "swir16", "SCL"],
                    bbox=bbox,
                    resolution=10,
                    chunks={},
                    dtype="uint16"
                ).isel(time=0)
                
                red = ds["red"].values.astype("float32")
                nir = ds["nir"].values.astype("float32")
                swir = ds["swir16"].values.astype("float32")
                scl = ds["SCL"].values.astype("float32")
                
                # Indices
                ndvi = idx(nir, red)
                nbr = idx(nir, swir)
                ndbi = idx(swir, nir)
                nubes = np.isin(scl, [8, 9, 10]).astype("float32")
                
                dia_del_anio = item.datetime.timetuple().tm_yday
                dias_en_el_anio = 366 if item.datetime.year % 4 == 0 and (item.datetime.year % 100 != 0 or item.datetime.year % 400 == 0) else 365
                fecha_norm = (dia_del_anio - 1) / (dias_en_el_anio - 1)
                fecha_band = np.full(ndvi.shape, fecha_norm, dtype="float32")
                
                bandas_stack.extend([ndvi, nbr, ndbi, nubes, fecha_band])
                
                profile = {
                    "driver": "GTiff",
                    "height": ndvi.shape[0],
                    "width": ndvi.shape[1],
                    "count": 15,
                    "dtype": "float32",
                    "crs": ds.odc.crs,
                    "transform": ds.odc.geobox.transform
                }
                
            if len(bandas_stack) != 15:
                print("  -> Stack generation failed (wrong band count)")
                continue
            
            # Get OSM distances
            from rasterio.coords import BoundingBox
            left, bottom, right, top = rasterio.transform.array_bounds(profile["height"], profile["width"], profile["transform"])
            bounds = BoundingBox(left, bottom, right, top)
            
            try:
                print("  Calculating OSM distances (roads & campings)...")
                road_dist, camping_dist = get_osm_distances(bounds, profile["crs"], (profile["height"], profile["width"]), profile["transform"])
                bandas_stack.extend([road_dist, camping_dist])
                profile["count"] = 17
            except Exception as e:
                print(f"  -> Failed to calculate OSM distances: {e}")
                continue
                
            if len(bandas_stack) != 17:
                print("  -> Stack generation failed (wrong final band count)")
                continue
                
            if c["id"].startswith("control_"):
                # For control scenes, the mask is all zeros
                mask = np.zeros((profile["height"], profile["width"]), dtype=np.uint8)
            else:
                # Get raster bounding box and CRS
                raster_crs = str(profile["crs"])
                
                # Reproject fire geometry to raster CRS
                projected_geom = reproject_geometry(c["geom"], "EPSG:4326", raster_crs)
                
                # Rasterize
                mask = features.rasterize(
                    [(projected_geom, 1)],
                    out_shape=(profile["height"], profile["width"]),
                    transform=profile["transform"],
                    fill=0,
                    dtype=rasterio.uint8
                )
            
            # Save files
            id_num = success_count + 1
            input_path = os.path.join(INPUTS_DIR, f"escena_{id_num}.tif")
            mask_path = os.path.join(MASKS_DIR, f"escena_{id_num}.tif")
            
            with rasterio.open(input_path, "w", **profile) as dst:
                for i in range(17):
                    dst.write(bandas_stack[i], i + 1)
                    
            mask_profile = profile.copy()
            mask_profile.update({"count": 1, "dtype": "uint8"})
            with rasterio.open(mask_path, "w", **mask_profile) as dst:
                dst.write(mask, 1)
                
            print(f"  -> Successfully generated Scene {id_num}:")
            print(f"     Input: {input_path}")
            print(f"     Mask: {mask_path} (fire pixels: {np.sum(mask == 1)})")
            success_count += 1
            
        except Exception as e:
            print(f"  -> Error downloading/processing {c['id']}: {e}")
            
    print(f"\nDone! Generated {success_count} training scenes in {DATASET_ROOT}")

if __name__ == "__main__":
    download_and_generate()
