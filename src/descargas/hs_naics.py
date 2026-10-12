"""Concordancia HS (10 dígitos de EE. UU.) -> SIC / SITC / NAICS, 1989-2017, de Pierce y Schott (Universidad de Yale).

Une las intensidades de NBER-CES (por industria NAICS) con los productos HS (decisión D4). Citar: Pierce, J. y
Schott, P. (2009), "A Concordance Between Ten-Digit U.S. Harmonized System Codes and SIC/NAICS Product Classes and
Industries", y su actualización de 2018. La página no declara licencia; los datos provienen de publicaciones del Census.
"""
from .comun import descargar

BASE = "https://spinup-000d1a-wp-offload-media.s3.amazonaws.com/faculty/wp-content/uploads/sites/47/2019/06"
ARCHIVOS = ["hssicnaics_20181015.zip", "hs_sic_38.pdf"]


def main() -> None:
    for nombre in ARCHIVOS:
        descargar(f"{BASE}/{nombre}", "concordancias", f"hs_naics_schott/{nombre}")


if __name__ == "__main__":
    main()
