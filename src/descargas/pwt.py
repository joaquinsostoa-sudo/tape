"""Penn World Table 11.0 (GGDC). Si el servidor rechaza la descarga automática, hay que bajarla a mano."""
from .comun import descargar

URL = "https://dataverse.nl/api/access/datafile/554105"  # Excel, DOI 10.34894/FABVLR


def main() -> None:
    descargar(URL, "pwt", "pwt110.xlsx")


if __name__ == "__main__":
    main()
