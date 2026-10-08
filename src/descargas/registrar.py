"""Vuelca los MANIFEST.json de data/raw/<fuente>/ a data/fuentes.csv (fecha de descarga y estado)."""
from __future__ import annotations

import csv
import json
from pathlib import Path

from .comun import RAIZ, RAW

FUENTES = RAIZ / "data" / "fuentes.csv"
# carpeta de raw -> ids de fuentes.csv que cubre
DESTINOS = {"baci": ["baci"], "atlas": ["atlas"], "pwt": ["pwt"], "concordancias": ["concordancias"],
            "wdi": ["wdi", "lpi"]}


def fecha_y_peso(carpeta: Path) -> tuple[str, float] | None:
    """(fecha más reciente, MB totales) según el manifiesto, o None si no hay descargas."""
    ruta = carpeta / "MANIFEST.json"
    if not ruta.exists():
        return None
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    if not datos:
        return None
    return max(d["fecha_utc"] for d in datos.values()), sum(d["bytes"] for d in datos.values()) / 1e6


def registrar() -> None:
    with FUENTES.open(newline="", encoding="utf-8") as f:
        filas = list(csv.reader(f))
    cab = filas[0]
    i_id, i_fecha, i_notas = cab.index("id"), cab.index("fecha de descarga"), cab.index("notas")
    for carpeta, ids in DESTINOS.items():
        info = fecha_y_peso(RAW / carpeta)
        if info is None:
            continue
        fecha, mb = info
        for fila in filas[1:]:
            if fila[i_id] in ids:
                fila[i_fecha] = fecha
                nota = fila[i_notas].split(" Estado:")[0].split(" | Estado:")[0]
                fila[i_notas] = f"{nota} | Estado: descargada {fecha} ({mb:,.0f} MB); manifiesto en data/raw/{carpeta}/."
    with FUENTES.open("w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(filas)


if __name__ == "__main__":
    registrar()
