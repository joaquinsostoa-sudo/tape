"""Rutas nacionales y fronteras del mapa MIC (pestaña B).

Fuente: data/raw/mic_mapa/rutas_fronteras_mic_2026-10-09.json. Las 22 rutas nacionales (PY01 a PY22) vienen como
hitos kilométricos (un punto por km, 9.107 en total) con departamento y zona; las fronteras como un punto por km
(1.455 de frontera seca y 2.578 de ríos). La geometría de las rutas es la secuencia de hitos, no un trazado fino.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
JSON_RUTAS = RAIZ / "data" / "raw" / "mic_mapa" / "rutas_fronteras_mic_2026-10-09.json"
CLEAN = RAIZ / "data" / "clean"


def _sin_codificar(s: pd.Series) -> pd.Series:
    return s.str.replace("&hyp;", "-", regex=False).str.strip()


def rutas_km(datos: dict) -> pd.DataFrame:
    df = pd.DataFrame(datos["rutas_km"])
    df.insert(0, "ruta_codigo", df.ruta.str[:4])
    return df


def hitos(datos: dict) -> pd.DataFrame:
    """Hitos kilométricos de las rutas: ruta, km del hito, coordenadas, departamento y zona."""
    df = pd.DataFrame(datos["hitos"])
    df.insert(0, "ruta_codigo", df.ruta.str[:4])
    df["km_hito"] = df.hito.str.extract(r"KM\s*(\d+)", expand=False).astype(int)
    df["departamento"] = _sin_codificar(df.departamento)
    return df


def fronteras(datos: dict) -> pd.DataFrame:
    df = pd.DataFrame(datos["fronteras"])
    df["limite_entre"] = _sin_codificar(df.limite_entre)
    return df


def main() -> None:
    datos = json.loads(JSON_RUTAS.read_text(encoding="utf-8"))
    r, h, f = rutas_km(datos), hitos(datos), fronteras(datos)
    r.to_csv(CLEAN / "mic_rutas_km.csv", index=False, encoding="utf-8")
    h.to_parquet(CLEAN / "mic_rutas_hitos.parquet", index=False)
    f.to_parquet(CLEAN / "mic_fronteras_puntos.parquet", index=False)
    print(f"{len(r)} rutas ({int(r.km.sum()):,} km); {len(h)} hitos; {len(f)} puntos de frontera "
          f"({f.tipo.value_counts().to_dict()})")


if __name__ == "__main__":
    main()
