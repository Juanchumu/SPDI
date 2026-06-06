import requests
import pyproj
import numpy as np
import scipy.ndimage
import rasterio
from shapely.geometry import LineString, Point
from shapely.ops import transform as shapely_transform
from rasterio.features import rasterize

def get_osm_distances(bounds, crs, shape, transform, degree_buffer=0.05, max_distance=10000.0):
    """
    Downloads OSM road and campsite data, projects to local UTM, 
    calculates distance grids on an extended grid, and crops to target shape.
    
    bounds: rasterio bounds object (left, bottom, right, top) or list/tuple
    crs: rasterio.crs.CRS or pyproj.CRS of the local UTM zone
    shape: tuple (H, W) for target output
    transform: rasterio.Affine transform of target output
    degree_buffer: float buffer in degrees around WGS84 center (~5.5km)
    max_distance: float default value for distances beyond buffer
    
    Returns: (road_dist, camping_dist) as HxW numpy arrays
    """
    H, W = shape
    left, bottom, right, top = bounds.left, bounds.bottom, bounds.right, bounds.top
    
    # Project target center to WGS84
    transformer_to_wgs84 = pyproj.Transformer.from_crs(crs, "EPSG:4326", always_xy=True)
    center_x = (left + right) / 2
    center_y = (bottom + top) / 2
    center_lon, center_lat = transformer_to_wgs84.transform(center_x, center_y)
    
    # Calculate buffered WGS84 bbox for Overpass
    south = center_lat - degree_buffer
    north = center_lat + degree_buffer
    west = center_lon - degree_buffer
    east = center_lon + degree_buffer
    
    # Build query
    query = f"""[out:json][timeout:30];
    (
      way["highway"~"motorway|trunk|primary|secondary|tertiary|unclassified|residential"]({south},{west},{north},{east});
      node["tourism"="camp_site"]({south},{west},{north},{east});
      way["tourism"="camp_site"]({south},{west},{north},{east});
    );
    out geom;"""
    
    url = "https://overpass-api.de/api/interpreter"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json'
    }
    
    try:
        response = requests.get(url, params={"data": query}, headers=headers, timeout=30)
        response.raise_for_status()
        osm_data = response.json()
        elements = osm_data.get("elements", [])
    except Exception as e:
        print(f"Error querying OSM Overpass: {e}. Using default max distance.")
        elements = []
        
    # Parse geometries and project to UTM
    transformer_to_utm = pyproj.Transformer.from_crs("EPSG:4326", crs, always_xy=True)
    
    road_geoms = []
    camping_geoms = []
    
    for el in elements:
        tags = el.get("tags", {})
        is_highway = "highway" in tags
        is_camping = tags.get("tourism") == "camp_site"
        
        if is_highway and el.get("type") == "way" and "geometry" in el:
            coords = [(pt["lon"], pt["lat"]) for pt in el["geometry"]]
            if len(coords) >= 2:
                line_utm = shapely_transform(transformer_to_utm.transform, LineString(coords))
                road_geoms.append(line_utm)
        elif is_camping:
            if el.get("type") == "node":
                pt_utm = shapely_transform(transformer_to_utm.transform, Point(el["lon"], el["lat"]))
                camping_geoms.append(pt_utm)
            elif el.get("type") == "way" and "geometry" in el:
                coords = [(pt["lon"], pt["lat"]) for pt in el["geometry"]]
                if len(coords) >= 1:
                    pt_utm = shapely_transform(transformer_to_utm.transform, Point(coords[0]))
                    camping_geoms.append(pt_utm)
                    
    # Setup extended grid (5km = 5000m buffer)
    buffer_m = 5000
    offset_px = int(buffer_m / 10) # 10m pixel resolution
    
    extend_left = left - buffer_m
    extend_top = top + buffer_m
    extend_w = W + 2 * offset_px
    extend_h = H + 2 * offset_px
    extend_transform = rasterio.Affine(10.0, 0.0, extend_left, 0.0, -10.0, extend_top)
    
    # Rasterize and compute EDT
    if road_geoms:
        road_mask = rasterize(
            [(geom, 1) for geom in road_geoms],
            out_shape=(extend_h, extend_w),
            transform=extend_transform,
            fill=0,
            all_touched=True,
            dtype=np.uint8
        )
        road_dist_ext = scipy.ndimage.distance_transform_edt(road_mask == 0) * 10.0
    else:
        road_dist_ext = np.full((extend_h, extend_w), max_distance, dtype=np.float32)
        
    if camping_geoms:
        camping_mask = rasterize(
            [(geom, 1) for geom in camping_geoms],
            out_shape=(extend_h, extend_w),
            transform=extend_transform,
            fill=0,
            all_touched=True,
            dtype=np.uint8
        )
        camping_dist_ext = scipy.ndimage.distance_transform_edt(camping_mask == 0) * 10.0
    else:
        camping_dist_ext = np.full((extend_h, extend_w), max_distance, dtype=np.float32)
        
    # Crop to target shape
    road_dist = road_dist_ext[offset_px : offset_px + H, offset_px : offset_px + W]
    camping_dist = camping_dist_ext[offset_px : offset_px + H, offset_px : offset_px + W]
    
    # Cap maximum distance
    road_dist = np.clip(road_dist, 0.0, max_distance)
    camping_dist = np.clip(camping_dist, 0.0, max_distance)
    
    return road_dist.astype(np.float32), camping_dist.astype(np.float32)
