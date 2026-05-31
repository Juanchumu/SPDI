import os
import numpy as np
import rasterio
from rasterio.transform import from_origin
from scipy.ndimage import gaussian_filter
from tqdm import tqdm

# ======================
# CONFIG
# ======================
N = 15000
H, W = 100, 100

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

OUT_DIR = os.path.join(DATA_DIR, "dataset", "train")

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(os.path.join(OUT_DIR, "inputs"), exist_ok=True)
os.makedirs(os.path.join(OUT_DIR, "masks"), exist_ok=True)

# ======================
# GENERADORES
# ======================

def generar_indices():
    """
    Genera NDVI, NBR, NDBI con algo de estructura espacial
    """
    base = np.random.uniform(-1, 1, (H, W))

    ndvi = gaussian_filter(base + np.random.normal(0, 0.2, (H, W)), sigma=2)
    nbr  = gaussian_filter(base + np.random.normal(0, 0.2, (H, W)), sigma=2)
    ndbi = gaussian_filter(np.random.uniform(-1, 1, (H, W)), sigma=2)

    # Normalizar a [-1, 1]
    ndvi = np.clip(ndvi, -1, 1).astype("float32")
    nbr  = np.clip(nbr, -1, 1).astype("float32")
    ndbi = np.clip(ndbi, -1, 1).astype("float32")

    return ndvi, nbr, ndbi


def generar_mask_incendio(ndvi, nbr):
    """
    Incendio correlacionado:
    - NDVI bajo
    - NBR alto
    """
    prob = (ndvi < -0.2) & (nbr > 0.3)

    # ruido + expansión espacial
    ruido = np.random.rand(H, W) < 0.02
    mask = (prob | ruido).astype(float)

    # suavizar para generar clusters
    mask = gaussian_filter(mask, sigma=1.5)
    mask = (mask > 0.3).astype("float32")

    return mask


def generar_escena():
    bandas = []
    ndvi_list = []
    nbr_list = []

    for t in range(5):
        ndvi, nbr, ndbi = generar_indices()

        ndvi_list.append(ndvi)
        nbr_list.append(nbr)

        nubes = np.random.choice([0, 1], size=(H, W), p=[0.8, 0.2]).astype("float32")
        fecha = np.full((H, W), t / 4.0, dtype="float32")

        bandas.extend([ndvi, nbr, ndbi, nubes, fecha])

    escena = np.stack(bandas)  # (25, H, W)

    # usar última imagen para generar incendio (podés cambiar esto)
    mask = generar_mask_incendio(ndvi_list[-1], nbr_list[-1])
    mask = np.expand_dims(mask, axis=0)

    return escena, mask


# ======================
# EXPORT
# ======================

transform = from_origin(0, 0, 10, 10)

for i in tqdm(range(N)):
    escena, mask = generar_escena()

    input_path = f"{OUT_DIR}/inputs/escena_{i:05d}.tif"
    mask_path  = f"{OUT_DIR}/masks/escena_{i:05d}.tif"

    # INPUT (25 bandas)
    with rasterio.open(
        input_path,
        'w',
        driver='GTiff',
        height=H,
        width=W,
        count=25,
        dtype='float32',
        transform=transform
    ) as dst:
        for b in range(25):
            dst.write(escena[b], b + 1)

    # MASK (1 banda)
    with rasterio.open(
        mask_path,
        'w',
        driver='GTiff',
        height=H,
        width=W,
        count=1,
        dtype='float32',
        transform=transform
    ) as dst:
        dst.write(mask[0], 1)
