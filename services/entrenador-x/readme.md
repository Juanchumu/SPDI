Nota: Para evitar que se pise con el otro worker, se puede hacer que arranque uno u otro 
unicamente cambiando el estado final.

# Esto Genera:

Indice A es ndvi
Indice B es nbr
Indice C es ndbi

dataset/
├── train/
│   ├── inputs/
│   │   ├── escena_001.tif   (25 bandas)
│   │   └── ...
│   └── masks/
│       ├── escena_001.tif   (1 banda)
│       └── ...

masks/escena_001.tif
└── banda 1 → imagen 1 incendio (0/1)


inputs/escena_001.tif
├── banda 1 → imagen 2 índice A
├── banda 2 → imagen 2 índice B
├── banda 3 → imagen 2 índice C
├── banda 4 → imagen 2 máscara de nubes
├── banda 5 → imagen 2 fecha normalizada
├── banda 6 → imagen 3 índice A
├── banda 7 → imagen 3 índice B
├── banda 8 → imagen 3 índice C
├── banda 9 → imagen 3 máscara de nubes
├── banda 10 → imagen 3 fecha normalizada
├── banda 11 → imagen 4 índice A
├── banda 12 → imagen 4 índice B
├── banda 13 → imagen 4 índice C
├── banda 14 → imagen 4 máscara de nubes
└── banda 15 → imagen 4 fecha normalizada



