"""Establecimientos de salud del mapa MIC (pestaña E): 212 servicios del IPS y del Ministerio de Salud.

Fuente: data/raw/mic_mapa/salud_mic_2026-10-09.json. Solo trae nombre, prestador, ciudad, departamento y
coordenadas (cinco sin ubicación válida): no hay camas, nivel de complejidad ni personal. El visor tampoco
declara si la lista es completa; 74 del MSPBS es una cifra baja para la red pública del país, así que se usa
como indicador de presencia y no como inventario.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
JSON_SALUD = RAIZ / "data" / "raw" / "mic_mapa" / "salud_mic_2026-10-09.json"
SALIDA = RAIZ / "data" / "clean" / "mic_salud_establecimientos.csv"


def establecimientos(datos: dict) -> pd.DataFrame:
    df = pd.DataFrame(datos["establecimientos"])
    df.insert(0, "establecimiento_id", range(1, len(df) + 1))
    df["dep_codigo"] = df.departamento.str[:3].astype(int) - 100
    sin = df.lat.isna() | df.lon.isna() | ((df.lat == 0) & (df.lon == 0))
    df.loc[sin, ["lat", "lon"]] = np.nan  # el visor guarda 0 o vacío cuando falta la ubicación
    return df


def main() -> None:
    df = establecimientos(json.loads(JSON_SALUD.read_text(encoding="utf-8")))
    df.to_csv(SALIDA, index=False, encoding="utf-8")
    print(f"{len(df)} establecimientos ({df.institucion.value_counts().to_dict()}); sin coordenadas: "
          f"{int(df.lat.isna().sum())}")


if __name__ == "__main__":
    main()
