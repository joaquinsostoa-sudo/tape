"""NBER-CES Manufacturing Industry Database (versión 2021, 1958-2018, NAICS 2012): intensidades por industria.

Insumo de la decisión D4: intensidad energética, de capital y de mano de obra de la manufactura de EE. UU.,
que se lleva a productos HS con una tabla NAICS -> HS (aparte). Dominio público (NBER y Census); citar a Becker,
Gray y Marvakov (2021). Supone la misma tecnología en todos los países.
"""
from .comun import descargar

BASE = "https://data.nber.org/nberces/nberces5818v1"
ARCHIVOS = [
    "nberces5818v1_n2012.csv",
    "naics_names_2012.txt",
    "nberces5818v1_technical_notes_Mar2021.pdf",
]


def main() -> None:
    for nombre in ARCHIVOS:
        descargar(f"{BASE}/{nombre}", "intensidades", f"nberces/{nombre}")


if __name__ == "__main__":
    main()
