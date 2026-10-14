"""Robustez HS4 contra HS6 (prueba A de la declaración del 2026-10-14 en docs/supuestos.md): el backtest nacional con productos de 6 dígitos.

Mismo esquema que `backtest_nacional.py` (D2 a, pruebas 2005, 2010 y 2015, h = 5, D7, D8, D13, φ y densidad con datos ≤ t0), pero la columna de producto (`hs4` en el código) lleva el HS6 de BACI,
la tabla de exportaciones sale de `comercio_depurado.parquet` con el alcance (a) de D6 (sin los pares con `reexportacion_aplicada` y sin la energía HS 271600) y los requisitos son los de
`requisitos_producto_hs6.parquet` (NBER-CES vía el puente NAICS → HS). Los productos sin requisito completo no entran, igual que con HS4.

Uso: uv run python -m src.modelos.robustez_hs6
"""
from __future__ import annotations

import duckdb
import pandas as pd

from src.limpieza.depuracion import HS6_ENERGIA, SALIDA
from src.modelos import backtest_nacional as bt
from src.modelos.logit_nacional import CLEAN, MODELO


def exportaciones_hs6_depuradas(ruta=SALIDA) -> pd.DataFrame:
    """`anio, iso3, hs4, x` con el HS6 en `hs4`: exportaciones sin los pares marcados (alcance a) ni la energía binacional."""
    return duckdb.connect().execute(f"""
        SELECT anio, iso3, hs6 AS hs4, SUM(x) AS x FROM read_parquet('{ruta.as_posix()}')
        WHERE NOT reexportacion_aplicada AND iso3 IS NOT NULL AND hs6 <> '{HS6_ENERGIA}' GROUP BY 1, 2, 3""").df()


def requisitos_hs6() -> pd.DataFrame:
    """Requisitos por HS6 con el nombre de columna que espera el modelo (`hs4`)."""
    r = pd.read_parquet(CLEAN / "requisitos_producto_hs6.parquet")
    return r.rename(columns={"hs92": "hs4"}).astype({"hs4": str})


def main() -> None:
    expo, req = exportaciones_hs6_depuradas(), requisitos_hs6()
    print(f"HS6: {len(expo):,} filas de exportación, {expo.hs4.nunique():,} productos, {expo.iso3.nunique()} países; con requisito completo: {req.dropna(subset=['energia', 'capital', 'habilidades', 'valor_peso_usd_kg']).hs4.nunique():,}")
    bt.correr(expo, req, str(MODELO / "backtest_resultados_hs6.csv"))


if __name__ == "__main__":
    main()
