"""Industrias del mapa logístico MIC (pestaña F, mapa F1): puntos con coordenadas, sector y subsector.

La fuente es la respuesta del gráfico de mapa del visor (ver data/raw/mic_mapa/README.md). No trae
ciudad ni departamento: se asignan en `src/puentes/geoprocesar_industrias.py` con los límites oficiales.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
JSON_PUNTOS = RAIZ / "data" / "raw" / "mic_mapa" / "industrias_mapa_mic_2026-10-08.json"
RESUMEN = RAIZ / "data" / "raw" / "mic_mapa" / "industrias_sector_subsector_2026-10-08.csv"
SALIDA = RAIZ / "data" / "clean" / "industrias_mic_puntos.parquet"
# Rectángulo que contiene a Paraguay (con margen): descarta coordenadas mal cargadas.
CAJA = {"lat": (-27.7, -19.2), "lon": (-62.7, -54.2)}


def cargar(ruta: Path = JSON_PUNTOS) -> pd.DataFrame:
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    df = pd.DataFrame(datos["filas"])
    df.insert(0, "industria_id", range(1, len(df) + 1))
    df["en_paraguay_caja"] = df.lat.between(*CAJA["lat"]) & df.lon.between(*CAJA["lon"])
    return df


def main() -> None:
    df = cargar()
    df.to_parquet(SALIDA, index=False)
    print(f"{len(df)} industrias; fuera de la caja de Paraguay: {int((~df.en_paraguay_caja).sum())}")


if __name__ == "__main__":
    main()
