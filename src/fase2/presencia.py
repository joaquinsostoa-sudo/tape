"""Matrices de presencia manufacturera por unidad del Censo 2011 y sector TAPE: Censo Económico 2011 (año de datos 2010) y mapa MIC 2026 (D34).

Cada fila es una de las unidades (distritos) del Censo 2011; cada columna, un sector de manufactura S09 a S43 (S44 no tiene comercio internacional). Los establecimientos del mapa MIC (distritos de 2022)
se llevan a la unidad de 2011 con los pesos de `puente_distritos_2022.csv`. La presencia es el cociente de localización de establecimientos (LQ) mayor a 1,5, calculado **dentro de manufactura de cada fuente**
(las dos fuentes no cubren igual los demás rubros); la alternativa es al menos una unidad.

LQ(d, s) = (e_ds / Σ_s e_ds) / (Σ_d e_ds / Σ_ds e_ds).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.puentes import base_capital_humano as bc
from src.puentes.taxonomia_tape import RAIZ

C = RAIZ / "data" / "clean"
SECTORES = [f"S{i:02d}" for i in range(9, 44)]
UMBRAL_LQ = 1.5


def lq(e: pd.DataFrame) -> pd.DataFrame:
    """Cociente de localización de establecimientos dentro de la manufactura de la fuente; las filas sin establecimientos quedan en NaN."""
    part = e.div(e.sum(axis=1).replace(0, np.nan), axis=0)
    nac = e.sum(axis=0) / e.values.sum()
    return part.div(nac.replace(0, np.nan), axis=1)


def presencia_lq(e: pd.DataFrame, umbral: float = UMBRAL_LQ) -> pd.DataFrame:
    """Presencia = LQ mayor al umbral (principal: 1,5)."""
    return (lq(e) > umbral).fillna(False).astype(bool)


def presencia_alterna(e: pd.DataFrame, minimo: float = 1.0) -> pd.DataFrame:
    """Presencia alternativa (robustez): al menos `minimo` establecimientos (censo: 1; MIC ponderado: 0,5)."""
    return (e >= minimo).astype(bool)


def establecimientos_censo(sectores: list[str] = SECTORES) -> pd.DataFrame:
    """Unidades económicas manufactureras del Censo 2011 por unidad (departamento, clave) y sector."""
    c = pd.read_csv(C / "censo2011_distrito_sector_tape.csv")
    c = c[c["sector_id"].isin(sectores)]
    e = c.groupby(["departamento", "distrito", "sector_id"])["ue"].sum().unstack(fill_value=0.0).reindex(columns=sectores, fill_value=0.0)
    e.index = pd.MultiIndex.from_tuples([(bc.departamento(a), bc.llave(b)) for a, b in e.index], names=["dep", "u"])
    return e


def establecimientos_mic(sectores: list[str] = SECTORES) -> pd.DataFrame:
    """Industrias manufactureras del mapa MIC por unidad de 2011 (con los pesos del puente de distritos) y sector."""
    p = pd.read_csv(C / "puente_distritos_2022.csv")
    p["dep"] = [bc.departamento(v) for v in p["departamento"]]
    p["clave"] = [bc.llave(v) for v in p["distrito_2022"].fillna(p["distrito_2012"])]
    m = bc.a_clave_base(pd.read_parquet(C / "industrias_distrito_sector_tape.parquet"), "departamento", "distrito", bc.distritos_base())
    m = m[m["sector_id"].isin(sectores)].groupby(["dep", "clave", "sector_id"])["n_industrias"].sum().reset_index()
    mm = m.merge(p[["dep", "clave", "unidad_2011", "peso"]], on=["dep", "clave"], how="left").dropna(subset=["unidad_2011"])
    mm["n"] = mm["n_industrias"] * mm["peso"].fillna(1.0)
    mm["u"] = [bc.llave(v) for v in mm["unidad_2011"]]
    e = mm.groupby(["dep", "u", "sector_id"])["n"].sum().unstack(fill_value=0.0).reindex(columns=sectores, fill_value=0.0)
    return e


def fuentes_comunes(sectores: list[str] = SECTORES) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Las dos matrices restringidas a las unidades que tienen manufactura en ambas fuentes."""
    a, b = establecimientos_censo(sectores), establecimientos_mic(sectores)
    a = a[a.sum(axis=1) > 0]
    b = b[b.sum(axis=1) > 0]
    comunes = a.index.intersection(b.index)
    return a.loc[comunes], b.loc[comunes]
