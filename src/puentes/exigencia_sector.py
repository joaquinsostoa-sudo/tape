"""¿Qué sectores de manufactura exigen formación específica? (D28).

Requisito de habilidades del NBER-CES (proporción de trabajadores que no son de producción, 2012-2018) por producto HS4 (`requisitos_producto_hs4.csv`), llevado a
sector TAPE con los pesos de D1 (media ponderada por el comercio mundial de cada HS4; D37 corrigió el código, que no multiplicaba por el valor mundial). Un sector exige formación específica si su valor es ≥ 0,28 (la mediana de los
productos con dato). Solo manufactura (S09 a S44): el NBER no cubre agro, minería ni servicios; esos sectores quedan sin clasificar en exigencia y no se imputan.

Salida: `data/clean/exigencia_formacion_sector.csv`. Uso: uv run python -m src.puentes.exigencia_sector
"""
from __future__ import annotations

import pandas as pd

from ..modelos.candidatos_sector import pesos_comercio
from .taxonomia_tape import RAIZ

REQUISITOS = RAIZ / "data" / "clean" / "requisitos_producto_hs4.csv"
PUENTE_HS = RAIZ / "data" / "clean" / "puente_hs92_sector.csv"
TAXONOMIA = RAIZ / "data" / "clean" / "taxonomia_sectores_tape.csv"
SALIDA = RAIZ / "data" / "clean" / "exigencia_formacion_sector.csv"
MANUFACTURA = [f"S{i:02d}" for i in range(9, 45)]
CORTE = 0.28
CERCA = 0.03
MIN_ALTA = 10
MIN_MEDIA = 3


def confianza(productos: int) -> str:
    """Confianza según cuántos productos del sector tienen dato del NBER: 10 o más alta, de 3 a 9 media, 1 o 2 baja."""
    return "alta" if productos >= MIN_ALTA else "media" if productos >= MIN_MEDIA else "baja"


def exigencia_por_sector(req: pd.DataFrame, pesos: pd.DataFrame, taxonomia: pd.DataFrame, corte: float = CORTE) -> pd.DataFrame:
    """Una fila por sector TAPE con el requisito medio de habilidades, cuántos productos tienen dato y si exige formación específica.

    `req` trae hs4 y habilidades; `pesos` trae hs4, sector_id y w (D37: fracción del HS4 asignada al sector por el valor mundial del HS4).
    """
    x = pesos.merge(req.dropna(subset=["habilidades"])[["hs4", "habilidades"]], on="hs4")
    x = x[x["sector_id"].isin(MANUFACTURA) & (x["w"] > 0)]
    x = x.assign(hw=x["habilidades"] * x["w"])
    g = x.groupby("sector_id").agg(hw=("hw", "sum"), w=("w", "sum"), productos_con_dato=("hs4", "nunique"))
    g["habilidades"] = g["hw"] / g["w"]
    out = taxonomia[["sector_id", "nombre"]].merge(g[["habilidades", "productos_con_dato"]], on="sector_id", how="left")
    con_dato = out["habilidades"].notna()
    out["productos_con_dato"] = out["productos_con_dato"].fillna(0).astype(int)
    out["exige_formacion"] = ""
    out.loc[con_dato, "exige_formacion"] = (out.loc[con_dato, "habilidades"] >= corte).map({True: "si", False: "no"})
    out["confianza"] = ""
    out.loc[con_dato, "confianza"] = out.loc[con_dato, "productos_con_dato"].map(confianza)
    out["cerca_del_corte"] = con_dato & ((out["habilidades"] - corte).abs() <= CERCA)
    out["fuente"] = "NBER-CES"
    out.loc[~con_dato, "fuente"] = "sin dato (el NBER cubre solo manufactura)"
    out["habilidades"] = out["habilidades"].round(3)
    return out


def main() -> None:
    pu = pd.read_csv(PUENTE_HS, dtype={"hs92": str})
    for c in ("peso", "valor_mundial"):
        pu[c] = pd.to_numeric(pu[c], errors="coerce")
    req = pd.read_csv(REQUISITOS, dtype={"hs4": str})
    out = exigencia_por_sector(req, pesos_comercio(pu), pd.read_csv(TAXONOMIA))
    out.to_csv(SALIDA, index=False, encoding="utf-8")
    d = out[out["sector_id"].isin(MANUFACTURA)]
    print(f"mediana de los productos: {req['habilidades'].median():.3f} | corte {CORTE}")
    print(f"manufactura: {int(d['habilidades'].notna().sum())} de {len(d)} sectores con dato; exigen formación específica: {int((d['exige_formacion'] == 'si').sum())}")
    print("cerca del corte (±0,03):", d.loc[d["cerca_del_corte"], "sector_id"].tolist())
    print(d.sort_values("habilidades", ascending=False)[["sector_id", "habilidades", "productos_con_dato", "exige_formacion", "confianza"]].to_string(index=False))


if __name__ == "__main__":
    main()
