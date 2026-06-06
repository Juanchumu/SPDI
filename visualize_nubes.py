import rasterio
import numpy as np
import matplotlib.pyplot as plt
import os

# Input GeoTIFF (copied to descargas)
input_path = '/home/bruno/descargas/escena_63.tif'
# Output PNG path
output_path = '/home/bruno/.gemini/antigravity/brain/10427bc1-93ec-43e1-875d-89b0b80acb98/artifacts/nubes_los_cardales.png'

with rasterio.open(input_path) as src:
    # Band 4 of T1 (cloud mask) corresponds to index 4 (1‑based)
    nubes = src.read(4)
    nubes = np.clip(nubes, 0, 1)

plt.figure(figsize=(8, 6))
plt.title('Los Cardales – Nubes (banda 4, T1)')
plt.imshow(nubes, cmap='gray')
plt.axis('off')
plt.tight_layout()
# Ensure directory exists
os.makedirs(os.path.dirname(output_path), exist_ok=True)
plt.savefig(output_path, dpi=150, bbox_inches='tight', pad_inches=0)
print('Saved cloud mask image to', output_path)
