"""Penn World Table (GGDC). La descarga automática la bloquea una protección anti-bots: se baja a mano.

Fuente: https://dataverse.nl/dataset.xhtml?persistentId=doi:10.34894/FABVLR (pestaña Files).
Archivo esperado: data/raw/pwt/pwt1001.xlsx (versión 10.01, 1950-2019) o pwt110.xlsx (versión 11.0).
"""
from .comun import RAW, anotar, sha256_archivo

ARCHIVOS = ("pwt1001.xlsx", "pwt110.xlsx")
URL = "https://dataverse.nl/dataset.xhtml?persistentId=doi:10.34894/FABVLR"


def main() -> None:
    presentes = [RAW / "pwt" / n for n in ARCHIVOS if (RAW / "pwt" / n).exists()]
    if not presentes:
        print(f"Falta el archivo: bajar a mano desde {URL} y dejar en data/raw/pwt/ ({' o '.join(ARCHIVOS)})")
        return
    for ruta in presentes:
        anotar(ruta, f"{URL} (descarga manual)", ruta.stat().st_size, sha256_archivo(ruta))
        print(f"registrado: pwt/{ruta.name}")


if __name__ == "__main__":
    main()
