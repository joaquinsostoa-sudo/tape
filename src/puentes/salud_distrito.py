"""Asigna distrito a los establecimientos de salud del mapa MIC y cuenta servicios por distrito.

Los que no tienen coordenadas toman las de su ciudad (tabla de ciudades del mapa MIC); la columna `ubicacion` lo
registra. Los distritos son los de los límites de 2012.
"""
from __future__ import annotations

import geopandas as gpd
import pandas as pd

from .geoprocesar_industrias import ADM1, ADM2, asignar
from .taxonomia_tape import RAIZ

ENTRADA = RAIZ / "data" / "clean" / "mic_salud_establecimientos.csv"
CIUDADES = RAIZ / "data" / "clean" / "ciudades_mic.csv"
SALIDA = RAIZ / "data" / "clean" / "mic_salud_localizados.csv"


def con_ubicacion(df: pd.DataFrame, ciudades: pd.DataFrame) -> pd.DataFrame:
    c = ciudades[["dep_codigo", "ciudad", "lat", "lon"]].rename(columns={"lat": "lat_c", "lon": "lon_c"})
    m = df.merge(c, on=["dep_codigo", "ciudad"], how="left")
    m["ubicacion"] = m.lat.notna().map({True: "propia", False: ""})
    ciudad = m.lat.isna() & m.lat_c.notna()
    m.loc[ciudad, ["lat", "lon"]] = m.loc[ciudad, ["lat_c", "lon_c"]].to_numpy()
    m.loc[ciudad, "ubicacion"] = "ciudad"
    m.loc[m.ubicacion == "", "ubicacion"] = "sin_ubicacion"
    return m.drop(columns=["lat_c", "lon_c"])


def localizar(df: pd.DataFrame, ciudades: pd.DataFrame) -> pd.DataFrame:
    m = con_ubicacion(df, ciudades)
    ok = m[m.lat.notna()]
    g = gpd.GeoDataFrame(ok, geometry=gpd.points_from_xy(ok.lon, ok.lat), crs="EPSG:4326")
    d = asignar(g, gpd.read_file(ADM1), "departamento_geo")
    s = asignar(g, gpd.read_file(ADM2), "distrito")
    return pd.concat([m, pd.concat([d, s], axis=1)], axis=1)


def main() -> None:
    df = localizar(pd.read_csv(ENTRADA), pd.read_csv(CIUDADES))
    df.to_csv(SALIDA, index=False, encoding="utf-8")
    print(df.ubicacion.value_counts().to_dict(), "| con distrito:", int(df.distrito.notna().sum()))


if __name__ == "__main__":
    main()
