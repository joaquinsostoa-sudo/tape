"""Densidad territorial por distrito y sector TAPE (D34, D26 de `supuestos_fase2.md`).

φ entre sectores sale del comercio de otros países, con la misma maquinaria de la Fase 1 tratando al sector como producto: exportaciones HS4 depuradas pasadas a sectores TAPE con el puente de D1,
RCA, presencia D13 en la muestra D8 y φ = mínimo de las dos probabilidades condicionales, **solo con datos ≤ año de corte (D3)**. Los distritos no participan: no hay fuga.

dens(d, s) = Σ_{s'≠s} φ(s, s') · pres(d, s') / Σ_{s'≠s} φ(s, s')
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.modelos.backtest_sector import exportaciones_sector, pesos_hs4_sector
from src.modelos.logit_nacional import CLEAN, MODELO
from src.modelos.oportunidades import PAIS, matriz_de_proximidad


def phi_sectores(corte: int, sectores: list[str]) -> pd.DataFrame:
    """Matriz φ entre los sectores pedidos con datos ≤ corte (filas y columnas en el orden de `sectores`; los sectores sin presencia internacional quedan con φ = 0)."""
    expo = pd.read_parquet(MODELO / "exportaciones_hs4_depurado.parquet")
    pesos = pesos_hs4_sector(pd.read_csv(CLEAN / "puente_hs92_sector.csv", dtype=str))
    sec = exportaciones_sector(expo, pesos).rename(columns={"sector_id": "hs4"})
    phi, productos, _ = matriz_de_proximidad(sec, pd.read_csv(CLEAN / "poblacion_pais.csv"), PAIS, corte)
    m = pd.DataFrame(np.nan_to_num(phi), index=productos, columns=productos)
    return m.reindex(index=sectores, columns=sectores).fillna(0.0)


def densidad(pres: pd.DataFrame, phi: pd.DataFrame) -> pd.DataFrame:
    """Densidad de cada celda distrito × sector. `pres` es booleana (distritos × sectores) y `phi` cuadrada con los mismos sectores; la diagonal no cuenta (el sector no se predice a sí mismo)."""
    f = phi.reindex(index=pres.columns, columns=pres.columns).fillna(0.0).to_numpy(dtype=float).copy()
    np.fill_diagonal(f, 0.0)
    den = f.sum(axis=1)
    num = pres.to_numpy(dtype=float) @ f.T
    d = np.divide(num, den[None, :], out=np.zeros_like(num), where=den[None, :] > 0)
    return pd.DataFrame(d, index=pres.index, columns=pres.columns)
