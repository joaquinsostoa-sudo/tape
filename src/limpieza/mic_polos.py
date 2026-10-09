"""Polos y Áreas de Fomento Industrial (AFI) y centros de formación del SNPP del mapa MIC (pestaña G).

Fuente: data/raw/mic_mapa/polos_afi_snpp_mic_2026-10-09.json. Las AFI vienen como 6.987 puntos con jerarquía
zona (5) > subregión (5) > polo (21) > nodo (42): cada punto es una muestra del área, no un vértice de polígono
(por confirmar). El filtro "Polo industrial" del visor no devuelve datos, así que solo hay AFI.
Los 53 centros del SNPP traen ciudad y departamento; 23 no tienen coordenadas y se ubican por la ciudad.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
JSON_POLOS = RAIZ / "data" / "raw" / "mic_mapa" / "polos_afi_snpp_mic_2026-10-09.json"
CIUDADES = RAIZ / "data" / "clean" / "ciudades_mic.csv"
CLEAN = RAIZ / "data" / "clean"


def afi(datos: dict) -> pd.DataFrame:
    df = pd.DataFrame(datos["afi"])
    df.insert(0, "afi_punto_id", range(1, len(df) + 1))
    return df


def jerarquia(df: pd.DataFrame) -> pd.DataFrame:
    """Una fila por nodo: su polo, subregión y zona y cuántos puntos de AFI lo componen."""
    g = df.groupby(["zona", "subregion", "polo", "nodo"]).agg(
        puntos=("lat", "size"), lat_centro=("lat", "mean"), lon_centro=("lon", "mean")).reset_index()
    return g


def snpp(datos: dict, ciudades: pd.DataFrame) -> pd.DataFrame:
    """Centros del SNPP. Sin coordenadas propias, toma las de la ciudad (marcado en `ubicacion`)."""
    df = pd.DataFrame(datos["snpp"])
    df["dep_codigo"] = df.departamento.str[:3].astype(int) - 100
    df = df.merge(ciudades[["dep_codigo", "ciudad", "lat", "lon"]].rename(columns={"lat": "lat_ciudad",
                                                                              "lon": "lon_ciudad"}),
                  on=["dep_codigo", "ciudad"], how="left")
    propia = df.lat.notna() & (df.lat != 0)
    df["ubicacion"] = propia.map({True: "propia", False: ""})
    ciudad = ~propia & df.lat_ciudad.notna()
    df.loc[ciudad, ["lat", "lon"]] = df.loc[ciudad, ["lat_ciudad", "lon_ciudad"]].to_numpy()
    df.loc[ciudad, "ubicacion"] = "ciudad"
    df.loc[df.ubicacion == "", "ubicacion"] = "sin_ubicacion"
    return df.drop(columns=["lat_ciudad", "lon_ciudad"])


def main() -> None:
    datos = json.loads(JSON_POLOS.read_text(encoding="utf-8"))
    a = afi(datos)
    j = jerarquia(a)
    s = snpp(datos, pd.read_csv(CIUDADES))
    a.to_parquet(CLEAN / "mic_afi_puntos.parquet", index=False)
    j.to_csv(CLEAN / "mic_afi_jerarquia.csv", index=False, encoding="utf-8")
    s.to_csv(CLEAN / "mic_snpp_centros.csv", index=False, encoding="utf-8")
    print(f"{len(a)} puntos AFI en {a.polo.nunique()} polos y {a.nodo.nunique()} nodos; {len(s)} centros SNPP "
          f"({s.ubicacion.value_counts().to_dict()})")


if __name__ == "__main__":
    main()
