"""Clasificaciones de productos: Lall (2000), clasificación tecnológica de las exportaciones (QEH Working Paper 44, 145 KB).

La lista de códigos solo está en el PDF (Anexo, Tabla 1); `src/puentes/clasificacion_lall.py` la lee y la lleva a HS4.
"""
from .comun import descargar

URL = "https://www.qeh.ox.ac.uk/sites/default/files/pdf_docs/qehwps44.pdf"


def main() -> None:
    descargar(URL, "clasificaciones_producto", "lall/qehwps44.pdf")


if __name__ == "__main__":
    main()
