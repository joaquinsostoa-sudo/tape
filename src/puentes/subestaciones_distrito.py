"""Asigna distrito y departamento a cada subestación del mapa MIC (misma regla que las industrias).

Los límites son los de geoBoundaries (2012): las subestaciones de distritos creados después quedan en el distrito
de origen o sin asignar; la columna `*_asignacion` dice cómo se resolvió cada una.
"""
from __future__ import annotations

import geopandas as gpd
import pandas as pd

from .geoprocesar_industrias import ADM1, ADM2, asignar
from .taxonomia_tape import RAIZ

ENTRADA = RAIZ / "data" / "clean" / "mic_subestaciones.csv"
SALIDA = RAIZ / "data" / "clean" / "mic_subestaciones_localizadas.csv"


def localizar(sub: pd.DataFrame) -> pd.DataFrame:
    pts = gpd.GeoDataFrame(sub, geometry=gpd.points_from_xy(sub.lon, sub.lat), crs="EPSG:4326")
    d = asignar(pts, gpd.read_file(ADM1), "departamento")
    s = asignar(pts, gpd.read_file(ADM2), "distrito")
    return pd.concat([sub, d, s], axis=1)


def main() -> None:
    df = localizar(pd.read_csv(ENTRADA))
    df.to_csv(SALIDA, index=False, encoding="utf-8")
    print(df.groupby(["departamento_asignacion", "distrito_asignacion"]).size())


if __name__ == "__main__":
    main()
