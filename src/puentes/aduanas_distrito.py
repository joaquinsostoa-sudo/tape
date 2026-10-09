"""Asigna distrito y departamento a los 35 puntos aduaneros del mapa MIC (límites de 2012, misma regla que las industrias)."""
from __future__ import annotations

import geopandas as gpd
import pandas as pd

from .geoprocesar_industrias import ADM1, ADM2, asignar
from .taxonomia_tape import RAIZ

ENTRADA = RAIZ / "data" / "clean" / "mic_aduanas_mapa.csv"
SALIDA = RAIZ / "data" / "clean" / "mic_aduanas_mapa_localizadas.csv"


def localizar(pts: pd.DataFrame) -> pd.DataFrame:
    g = gpd.GeoDataFrame(pts, geometry=gpd.points_from_xy(pts.lon, pts.lat), crs="EPSG:4326")
    d = asignar(g, gpd.read_file(ADM1), "departamento")
    s = asignar(g, gpd.read_file(ADM2), "distrito")
    return pd.concat([pts, d, s], axis=1)


def main() -> None:
    df = localizar(pd.read_csv(ENTRADA))
    df.to_csv(SALIDA, index=False, encoding="utf-8")
    print(df.groupby(["departamento_asignacion", "distrito_asignacion"]).size())


if __name__ == "__main__":
    main()
