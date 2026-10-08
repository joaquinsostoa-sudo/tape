"""Límites administrativos de Paraguay (geoBoundaries gbOpen, CC BY 4.0; fuente original DGEEC, 2012).

ADM1 = 18 departamentos (incluye Capital); ADM2 = 247 distritos. Los distritos creados después de
2012 no figuran: el mapa MIC habla de 263 ciudades.
"""
from .comun import descargar

BASE = "https://github.com/wmgeolab/geoBoundaries/raw"
ARCHIVOS = [
    (f"{BASE}/9469f09/releaseData/gbOpen/PRY/ADM1/geoBoundaries-PRY-ADM1.geojson", "geoBoundaries-PRY-ADM1.geojson"),
    (f"{BASE}/f549eab/releaseData/gbOpen/PRY/ADM2/geoBoundaries-PRY-ADM2.geojson", "geoBoundaries-PRY-ADM2.geojson"),
]


def main() -> None:
    for url, nombre in ARCHIVOS:
        descargar(url, "limites_admin", nombre)


if __name__ == "__main__":
    main()
