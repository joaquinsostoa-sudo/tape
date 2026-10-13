"""Requisito revelado (paso 2 del plan de las capas): cuánto le falta a un país, capa por capa, para la dotación de quienes ya
exportan el producto con ventaja.

Para cada producto p y capa k, la referencia R_pk es la mediana de la dotación a_ck de los países con presencia en p (D13, datos hasta
t0; el propio país queda fuera de su referencia). El *faltante* es max(0, R_pk − a_ck): estar por encima del nivel típico de los
productores no perjudica. Las cuatro dotaciones están definidas con «más es mejor», así que no hay ambigüedad de signo y la hipótesis
es una sola: a más faltante, menor probabilidad de entrada (θ < 0). Se agrega el faltante de ingreso (log del PIB per cápita) como
control de desarrollo. Sin referencia (menos de `minimo` productores con dato) el faltante queda vacío y la fila se excluye.

Sensibilidades (no cuentan para el criterio de éxito): referencia con media o percentil 25 (`fmedia_`, `fp25_`) y distancia absoluta
(`fdist_`). Columnas: `f_<capa>` (principal), con capas = energia, capital_humano, capital_fisico, logistica, pib.
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

from src.modelos.logit_nacional import CAPAS_PRINCIPALES

CAPAS_REVELADAS = [*CAPAS_PRINCIPALES, "pib"]
MINIMO_PRODUCTORES = 5  # igual que el umbral de la proximidad


def _estadisticos(x: np.ndarray) -> dict[str, np.ndarray]:
    """Mediana, media y percentil 25 por columna, ignorando vacíos."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        return {"mediana": np.nanmedian(x, axis=0), "media": np.nanmean(x, axis=0), "p25": np.nanpercentile(x, 25, axis=0)}


def faltantes(pres: pd.DataFrame, a: pd.DataFrame, grilla: pd.DataFrame, minimo: int = MINIMO_PRODUCTORES) -> pd.DataFrame:
    """Faltantes por capa para cada par (iso3, hs4) de `grilla`.

    `pres`: (iso3, hs4) con presencia. `a`: una fila por país con columnas `a_<capa>` (estandarizadas en la ventana)."""
    capas = [c for c in CAPAS_REVELADAS if f"a_{c}" in a.columns]
    mat = a.set_index("iso3")[[f"a_{c}" for c in capas]]
    idx = {iso: i for i, iso in enumerate(mat.index)}
    valores = mat.to_numpy(dtype=float)
    productores = pres[pres.iso3.isin(idx)].groupby("hs4").iso3.apply(lambda s: np.array([idx[i] for i in s]))
    salida = {f"{pref}_{c}": np.full(len(grilla), np.nan) for pref in ("f", "fmedia", "fp25", "fdist") for c in capas}
    pos = grilla.reset_index(drop=True)
    for hs4, filas in pos.groupby("hs4").indices.items():
        prod = productores.get(hs4)
        if prod is None or len(prod) < minimo:
            continue
        ref_todos = _estadisticos(valores[prod])
        n_todos = (~np.isnan(valores[prod])).sum(axis=0)
        for r in filas:
            c = idx.get(pos.iso3.iat[r])
            if c is None:
                continue
            if c in prod:  # el propio país sale de su referencia
                otros = prod[prod != c]
                ref, n = _estadisticos(valores[otros]), (~np.isnan(valores[otros])).sum(axis=0)
            else:
                ref, n = ref_todos, n_todos
            ac, ok = valores[c], n >= minimo
            for k, capa in enumerate(capas):
                if not ok[k] or np.isnan(ac[k]):
                    continue
                salida[f"f_{capa}"][r] = max(0.0, ref["mediana"][k] - ac[k])
                salida[f"fmedia_{capa}"][r] = max(0.0, ref["media"][k] - ac[k])
                salida[f"fp25_{capa}"][r] = max(0.0, ref["p25"][k] - ac[k])
                salida[f"fdist_{capa}"][r] = abs(ref["mediana"][k] - ac[k])
    return pd.concat([pos[["iso3", "hs4"]], pd.DataFrame(salida)], axis=1)
