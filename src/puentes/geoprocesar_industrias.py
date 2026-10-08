"""Asigna distrito y departamento a cada industria del mapa MIC cruzando sus coordenadas con los límites.

Regla: un punto dentro de un polígono toma ese polígono. Un punto fuera (por la generalización de los
límites de 2012 o por coordenadas en el borde) toma el polígono más cercano si está a menos de
`MAX_CERCANO_M` metros; si no, queda sin asignar. Siempre se guarda cómo se asignó.
"""
from __future__ import annotations

import geopandas as gpd
import pandas as pd

from .taxonomia_tape import RAIZ

CRS_METRICO = "EPSG:32721"  # UTM zona 21 Sur: sirve para distancias en Paraguay
MAX_CERCANO_M = 5_000.0
ADM1 = RAIZ / "data" / "raw" / "limites_admin" / "geoBoundaries-PRY-ADM1.geojson"
ADM2 = RAIZ / "data" / "raw" / "limites_admin" / "geoBoundaries-PRY-ADM2.geojson"
PUNTOS = RAIZ / "data" / "clean" / "industrias_mic_puntos.parquet"
SALIDA = RAIZ / "data" / "clean" / "industrias_mic_localizadas.parquet"
SALIDA_DISTRITO = RAIZ / "data" / "clean" / "industrias_distrito_sector.parquet"


def asignar(puntos: gpd.GeoDataFrame, poligonos: gpd.GeoDataFrame, campo: str,
            max_m: float = MAX_CERCANO_M) -> pd.DataFrame:
    """Para cada punto: nombre del polígono, cómo se asignó y distancia (m) si fue por cercanía."""
    p = puntos[["geometry"]].to_crs(CRS_METRICO)
    z = poligonos[["shapeName", "shapeID", "geometry"]].to_crs(CRS_METRICO)
    dentro = gpd.sjoin(p, z, how="left", predicate="within")
    dentro = dentro[~dentro.index.duplicated(keep="first")]
    res = pd.DataFrame({campo: dentro.shapeName, f"{campo}_id": dentro.shapeID}, index=p.index)
    res[f"{campo}_asignacion"] = res[campo].notna().map({True: "dentro", False: ""})
    res[f"{campo}_dist_m"] = 0.0
    fuera = p[res[campo].isna()]
    if len(fuera):
        cerca = gpd.sjoin_nearest(fuera, z, how="left", max_distance=max_m, distance_col="d")
        cerca = cerca[~cerca.index.duplicated(keep="first")]
        ok = cerca.shapeName.notna()
        res.loc[cerca.index[ok], campo] = cerca.loc[ok, "shapeName"]
        res.loc[cerca.index[ok], f"{campo}_id"] = cerca.loc[ok, "shapeID"]
        res.loc[cerca.index[ok], f"{campo}_asignacion"] = "cercano"
        res.loc[cerca.index[ok], f"{campo}_dist_m"] = cerca.loc[ok, "d"]
        sin = res.index.difference(cerca.index[ok]).intersection(fuera.index)
        res.loc[sin, f"{campo}_asignacion"] = "sin_asignar"
    return res


def localizar() -> pd.DataFrame:
    df = pd.read_parquet(PUNTOS)
    pts = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.lon, df.lat), crs="EPSG:4326")
    d = asignar(pts, gpd.read_file(ADM1), "departamento")
    s = asignar(pts, gpd.read_file(ADM2), "distrito")
    return pd.concat([df, d, s], axis=1)


def main() -> None:
    df = localizar()
    df.to_parquet(SALIDA, index=False)
    tabla = (df.dropna(subset=["distrito"]).groupby(["departamento", "distrito", "sector", "subsector"])
             .size().rename("n_industrias").reset_index())
    tabla.to_parquet(SALIDA_DISTRITO, index=False)
    print(df.groupby(["departamento_asignacion", "distrito_asignacion"]).size())


if __name__ == "__main__":
    main()
