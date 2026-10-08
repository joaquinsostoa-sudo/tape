"""BACI (CEPII), revisión HS92. Se deja el zip tal cual: la limpieza lee sus miembros sin extraer."""
from .comun import descargar

VERSION = "V202601"
URL = f"https://www.cepii.fr/DATA_DOWNLOAD/baci/data/BACI_HS92_{VERSION}.zip"


def main() -> None:
    descargar(URL, "baci", f"BACI_HS92_{VERSION}.zip")


if __name__ == "__main__":
    main()
