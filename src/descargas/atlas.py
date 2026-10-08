"""Atlas de Complejidad Económica (Growth Lab) vía Harvard Dataverse. Licencia CC0.

No se bajan los archivos bilaterales por año (~14 GB): BACI cubre lo bilateral.
"""
from .comun import descargar_dataverse

HS92 = "doi:10.7910/DVN/T4CHWJ"
CLASIFICACIONES = "doi:10.7910/DVN/3BAL1O"
CONVERSIONES = "doi:10.7910/DVN/6AADMR"  # HS entre revisiones y SITC, con pesos
ESPACIO_PRODUCTO = "doi:10.7910/DVN/FCDZBN"
RANKINGS = "doi:10.7910/DVN/XTAQMC"

HS92_ARCHIVOS = [
    "hs92_country_product_year_4.csv", "hs92_country_product_year_6.csv",
    "hs92_product_year_4.csv", "hs92_product_year_6.csv",
    "hs92_country_year.csv", "hs92_data_dictionary.csv",
]


def main() -> None:
    descargar_dataverse(HS92, "atlas", solo=HS92_ARCHIVOS)
    descargar_dataverse(CLASIFICACIONES, "atlas", "clasificaciones/")
    descargar_dataverse(ESPACIO_PRODUCTO, "atlas", "espacio_producto/")
    descargar_dataverse(RANKINGS, "atlas", "rankings/")
    descargar_dataverse(CONVERSIONES, "concordancias", "atlas_conversion_hs/")


if __name__ == "__main__":
    main()
