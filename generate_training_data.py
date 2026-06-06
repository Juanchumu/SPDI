# generate_training_data.py
"""Generate training dataset from fire incident shapefiles.

The raw shapefiles are located in `data/raw` and contain polygon (or point) geometries
representing fire occurrences. This script rasterizes those geometries to create mask
images that align with the satellite input rasters already present in
`tmp/dataset/inputs`.

Expected directory layout:

```
data/raw/*.shp          # fire incident shapefiles
tmp/dataset/inputs/    # folder with input raster files (GeoTIFF)
tmp/dataset/masks/     # folder where mask rasters will be written
```

The script:
1. Scans `tmp/dataset/inputs` for `.tif` files.
2. For each input raster, loads its spatial transform and shape.
3. Finds all fire geometries that intersect the raster extent.
4. Rasterizes the geometries to a binary mask (1 = fire, 0 = no fire).
5. Saves the mask with the same filename in `tmp/dataset/masks`.

Dependencies: `rasterio`, `fiona`, `shapely` (all already available in the base image).
"""

import os
import glob
import rasterio
from rasterio import features
import shapefile
from shapely.geometry import shape, box

DATASET_ROOT = "tmp/dataset"
INPUTS_DIR = os.path.join(DATASET_ROOT, "inputs")
MASKS_DIR = os.path.join(DATASET_ROOT, "masks")
RAW_SHAPEFILES_DIR = "data/raw"

def ensure_dirs():
    os.makedirs(INPUTS_DIR, exist_ok=True)
    os.makedirs(MASKS_DIR, exist_ok=True)

def load_shapefiles():
    shapefile_paths = glob.glob(os.path.join(RAW_SHAPEFILES_DIR, "*.shp"))
    geometries = []
    for shp_path in shapefile_paths:
        print(f"Loading shapefile: {shp_path}")
        with shapefile.Reader(shp_path) as sf:
            for sr in sf.shapeRecords():
                if sr.shape.shapeType == 0:  # Null shape
                    continue
                geom_dict = sr.shape.__geo_interface__
                geom = shape(geom_dict).buffer(0)  # clean geometry
                geometries.append(geom)
    print(f"Loaded {len(geometries)} geometries from shapefiles.")
    return geometries

def rasterize_mask(raster_path, geometries):
    with rasterio.open(raster_path) as src:
        out_shape = (src.height, src.width)
        transform = src.transform
        # Filter geometries that intersect the raster bounds for efficiency
        raster_bounds = box(*src.bounds)
        intersecting = [geom for geom in geometries if geom.intersects(raster_bounds)]
        if not intersecting:
            # No fire geometry in this tile → mask of zeros
            mask = rasterio.io.MemoryFile().open(driver="GTiff", height=src.height,
                                                width=src.width, count=1,
                                                dtype=rasterio.uint8).read(1) * 0
        else:
            mask = features.rasterize(
                [(geom, 1) for geom in intersecting],
                out_shape=out_shape,
                transform=transform,
                fill=0,
                dtype=rasterio.uint8,
            )
        return mask

def main():
    ensure_dirs()
    geometries = load_shapefiles()
    if not geometries:
        print("No geometries found in shapefiles. Exiting.")
        return
    input_files = sorted(glob.glob(os.path.join(INPUTS_DIR, "*.tif")))
    if not input_files:
        print(f"No input TIFF files found in {INPUTS_DIR}. Exiting.")
        return
    for tif_path in input_files:
        mask = rasterize_mask(tif_path, geometries)
        fname = os.path.basename(tif_path)
        mask_path = os.path.join(MASKS_DIR, fname)
        # Write mask as a single‑band uint8 GeoTIFF using the same metadata as the input
        with rasterio.open(tif_path) as src:
            meta = src.meta.copy()
            meta.update({"count": 1, "dtype": rasterio.uint8})
            with rasterio.open(mask_path, "w", **meta) as dst:
                dst.write(mask, 1)
        print(f"Mask written: {mask_path}")

if __name__ == "__main__":
    main()
