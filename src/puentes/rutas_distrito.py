"""Kilómetros de ruta nacional por distrito: cada hito kilométrico se asigna a un distrito (límites de 2012).

Un hito = 1 km de ruta, así que el conteo de hitos por distrito es la longitud de ruta nacional que lo cruza.
Es una medida gruesa de accesibilidad vial (solo rutas nacionales PY01 a PY22; no incluye caminos vecinales).
"""
from __future__ import annotations

import geopandas as gpd
import pandas as pd

from .geoprocesar_industrias import ADM1, ADM2, asignar
from .taxonomia_tape import RAIZ

ENTRADA = RAIZ / "data" / "clean" / "mic_rutas_hitos.parquet"
SALIDA = RAIZ / "data" / "clean" / "mic_rutas_km_distrito.csv"


def km_por_distrito(hitos: pd.DataFrame) -> pd.DataFrame:
    pts = gpd.GeoDataFrame(hitos, geometry=gpd.points_from_xy(hitos.lon, hitos.lat), crs="EPSG:4326")
    d = asignar(pts, gpd.read_file(ADM1), "departamento_geo")
    s = asignar(pts, gpd.read_file(ADM2), "distrito")
    h = pd.concat([hitos, d, s], axis=1)
    tabla = (h.dropna(subset=["distrito"]).groupby(["departamento_geo", "distrito", "ruta_codigo"]).size()
             .rename("km_ruta").reset_index())
    return tabla


def main() -> None:
    tabla = km_por_distrito(pd.read_parquet(ENTRADA))
    tabla.to_csv(SALIDA, index=False, encoding="utf-8")
    print(f"{tabla.km_ruta.sum():,} km asignados a {tabla.distrito.nunique()} distritos")


if __name__ == "__main__":
    main()
