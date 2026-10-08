"""Correspondencias oficiales: UNSD (HS<->CPC 2.1, CPC 2.1<->CIIU 4) y WITS (HS entre revisiones, HS-CIIU 3).

Las conversiones HS con pesos del Atlas se bajan en `atlas.py` (carpeta atlas_conversion_hs/).
WITS no publica HS->CIIU Rev.4; el camino a CIIU 4 es HS -> CPC 2.1 -> CIIU 4.
"""
from .comun import descargar

UNSD = "https://unstats.un.org/unsd/classifications/Econ/tables"
WITS = "https://wits.worldbank.org/data/public/concordance"

ARCHIVOS = [
    (f"{UNSD}/CPC/CPCv21_HS2017/CPC21-HS2017.csv", "unsd/CPC21-HS2017.csv"),
    (f"{UNSD}/CPC/CPCv21_HS12/cpc21-hs2012.txt", "unsd/cpc21-hs2012.txt"),
    (f"{UNSD}/CPC/CPCv21_ISIC4/cpc21-isic4.txt", "unsd/cpc21-isic4.txt"),
    (f"{UNSD}/ISIC/ISIC4_CPCv21/isic4-cpc21.txt", "unsd/isic4-cpc21.txt"),
    (f"{WITS}/Concordance_H0_to_I3.zip", "wits/Concordance_H0_to_I3.zip"),
    (f"{WITS}/Concordance_H4_to_H0.zip", "wits/Concordance_H4_to_H0.zip"),
    (f"{WITS}/Concordance_H5_to_H0.zip", "wits/Concordance_H5_to_H0.zip"),
]


def main() -> None:
    for url, nombre in ARCHIVOS:
        descargar(url, "concordancias", nombre)


if __name__ == "__main__":
    main()
