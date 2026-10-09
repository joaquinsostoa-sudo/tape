"""Comercio exterior por aduana del mapa MIC (pestaña H): importaciones y exportaciones por red aduanera.

Fuente: data/raw/mic_mapa/aduanas_mic_2026-10-09.json. **El visor no indica el año ni el período** de las cifras.
Tres vistas del mismo dato, con diferencias que se conservan sin corregir:
- `detalle` (tabla H3): 42 redes aduaneras con importaciones (USD CIF, kg) y exportaciones (USD FOB, kg); 9 filas
  vienen sin ningún valor (sin operaciones registradas, no cero).
- `mapa` (H1): 35 puntos con coordenadas; las exportaciones están en USD CIF (más altas que las FOB) y algunas
  aduanas del detalle quedan agrupadas en un solo punto.
- `ranking` (H2): 35 aduanas con la clave de la DNA y sus importaciones y exportaciones (USD CIF).
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
JSON_ADUANAS = RAIZ / "data" / "raw" / "mic_mapa" / "aduanas_mic_2026-10-09.json"
CLEAN = RAIZ / "data" / "clean"


def detalle(datos: dict) -> pd.DataFrame:
    df = pd.DataFrame(datos["detalle"])
    partes = df.red_aduanera.str.split(" - ", n=1, expand=True)
    df.insert(1, "ciudad_aduana", partes[0].str.strip())
    df.insert(2, "punto", partes[1].str.strip())
    df["con_operaciones"] = df.imp_usd_cif.notna() | df.exp_usd.notna()
    return df


def mapa(datos: dict) -> pd.DataFrame:
    df = pd.DataFrame(datos["mapa"])
    df.insert(0, "punto_id", range(1, len(df) + 1))
    return df


def ranking(datos: dict) -> pd.DataFrame:
    imp = pd.DataFrame(datos["ranking"]["Total Import (USD CIF)"], columns=["aduana_dna", "imp_usd_cif"])
    exp = pd.DataFrame(datos["ranking"]["Total Export (USD CIF)"], columns=["aduana_dna", "exp_usd_cif"])
    return imp.merge(exp, on="aduana_dna", how="outer", validate="1:1")


def unir_coordenadas(det: pd.DataFrame, pts: pd.DataFrame) -> pd.DataFrame:
    """Pega al detalle las coordenadas del punto del mapa con las mismas importaciones (USD y kg), si existe y es
    único. Las aduanas agrupadas en un punto o sin operaciones quedan sin coordenadas (`union_mapa` lo dice)."""
    llave = ["imp_usd_cif", "imp_kg"]
    p = pts.assign(imp_usd_cif=pts.imp_usd_cif.round(0), imp_kg=pts.imp_kg.round(2))
    unicos = p[~p.duplicated(llave, keep=False)][[*llave, "tipo", "lat", "lon"]]
    d = det.assign(imp_usd_cif=det.imp_usd_cif.round(0), imp_kg=det.imp_kg.round(2))
    m = d.merge(unicos, on=llave, how="left").assign(imp_usd_cif=det.imp_usd_cif, imp_kg=det.imp_kg)
    m["union_mapa"] = "sin_coordenadas"
    m.loc[m.lat.notna(), "union_mapa"] = "exacta"
    return m


def main() -> None:
    datos = json.loads(JSON_ADUANAS.read_text(encoding="utf-8"))
    det, pts, rk = detalle(datos), mapa(datos), ranking(datos)
    union = unir_coordenadas(det, pts)
    union.to_csv(CLEAN / "mic_aduanas_detalle.csv", index=False, encoding="utf-8")
    pts.to_csv(CLEAN / "mic_aduanas_mapa.csv", index=False, encoding="utf-8")
    rk.to_csv(CLEAN / "mic_aduanas_ranking.csv", index=False, encoding="utf-8")
    print(f"{len(det)} redes aduaneras ({int(det.con_operaciones.sum())} con operaciones); {len(pts)} puntos; "
          f"{len(rk)} en el ranking; unión: {union.union_mapa.value_counts().to_dict()}")


if __name__ == "__main__":
    main()
