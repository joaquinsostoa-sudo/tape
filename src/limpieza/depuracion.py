"""Depuración del comercio (tarea 1.2, decisión D6): marca de reexportaciones y exclusión de la energía binacional, sin borrar nada.

Regla (declarada en `docs/supuestos.md` antes de correr): para cada país, producto HS6 y año con exportación X > 0 y la importación M del mismo producto, año y país (BACI),
`reexportacion = (X ≥ MIN_X) y (M ≥ THETA · X)` con THETA = 0,5 y MIN_X = 100 (miles de USD); sensibilidad con 0,25 (`reexp_025`) y 1,0 (`reexp_100`). Se aplica a todos los países. La energía
(HS 271600, Itaipú y Yacyretá) se marca `excluido_energia`. Entra solo información del mismo año.

**Alcance de la depuración (decisión del equipo, 2026-10-14):** la marca se calcula para todos los países (columna informativa), pero solo se **aplica** (`reexportacion_aplicada`, la que usa el «RCA depurado»)
a Paraguay y a una lista explícita de centros de reexportación (`PAISES_DEPURADOS`: Hong Kong, Singapur, Países Bajos y Bélgica). En el resto la razón M/X marca comercio intraindustrial genuino
(EE. UU. 72 %, Alemania 62 %) y se usan las exportaciones brutas.

Salidas en `data/clean/` (no versionadas):
- `comercio_depurado.parquet`: `anio, codigo_baci, iso3, hs6, x, m, razon_m_x, reexportacion, reexp_025, reexp_100, excluido_energia, reexportacion_aplicada` (una fila por país-producto-año con exportación).
- `exportaciones_hs4_depurado.parquet`: `anio, iso3, hs4, x`, con la suma por HS4 de los HS6 que no tienen `reexportacion_aplicada` (el «RCA depurado» de D13 se calcula sobre esta tabla, sin la energía HS4 2716).
Uso: uv run python -m src.limpieza.depuracion
"""
from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
CLEAN = RAIZ / "data" / "clean"
EXPO = CLEAN / "comercio_exportaciones_hs6.parquet"
IMPO = CLEAN / "comercio_importaciones_hs6.parquet"
PUENTE = CLEAN / "puente_paises_baci.csv"
SALIDA = CLEAN / "comercio_depurado.parquet"
SALIDA_HS4 = RAIZ / "data" / "model" / "exportaciones_hs4_depurado.parquet"
THETA = 0.5
MIN_X = 100.0  # miles de USD
HS6_ENERGIA = "271600"
PAISES_DEPURADOS = ("PRY", "HKG", "SGP", "NLD", "BEL")  # Paraguay y centros de reexportación; el resto usa exportaciones brutas


def depurar(expo: Path = EXPO, impo: Path = IMPO, puente: Path = PUENTE, salida: Path = SALIDA, salida_hs4: Path = SALIDA_HS4,
            theta: float = THETA, min_x: float = MIN_X, paises: tuple[str, ...] = PAISES_DEPURADOS) -> duckdb.DuckDBPyConnection:
    """Arma las dos tablas y devuelve la conexión (con la vista `depurado`) para consultar el resumen."""
    con = duckdb.connect()
    lista = ", ".join(f"'{p}'" for p in paises)
    con.execute(f"""
        COPY (
          SELECT e.anio, e.codigo_baci, p.iso3, e.hs6, e.valor_miles_usd AS x, COALESCE(m.valor_miles_usd, 0.0) AS m,
                 COALESCE(m.valor_miles_usd, 0.0) / e.valor_miles_usd AS razon_m_x,
                 (e.valor_miles_usd >= {min_x} AND COALESCE(m.valor_miles_usd, 0.0) >= {theta} * e.valor_miles_usd) AS reexportacion,
                 (e.valor_miles_usd >= {min_x} AND COALESCE(m.valor_miles_usd, 0.0) >= 0.25 * e.valor_miles_usd) AS reexp_025,
                 (e.valor_miles_usd >= {min_x} AND COALESCE(m.valor_miles_usd, 0.0) >= 1.0 * e.valor_miles_usd) AS reexp_100,
                 (e.hs6 = '{HS6_ENERGIA}') AS excluido_energia,
                 (p.iso3 IN ({lista}) AND e.valor_miles_usd >= {min_x} AND COALESCE(m.valor_miles_usd, 0.0) >= {theta} * e.valor_miles_usd) AS reexportacion_aplicada
          FROM read_parquet('{expo.as_posix()}') e
          LEFT JOIN read_parquet('{impo.as_posix()}') m USING (anio, codigo_baci, hs6)
          LEFT JOIN read_csv_auto('{puente.as_posix()}') p ON p.codigo_baci = e.codigo_baci
          WHERE e.valor_miles_usd > 0
        ) TO '{salida.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)""")
    con.execute(f"CREATE VIEW depurado AS SELECT * FROM read_parquet('{salida.as_posix()}')")
    con.execute(f"""
        COPY (SELECT anio, iso3, substr(hs6, 1, 4) AS hs4, SUM(x) AS x FROM depurado WHERE NOT reexportacion_aplicada AND iso3 IS NOT NULL GROUP BY 1, 2, 3)
        TO '{salida_hs4.as_posix()}' (FORMAT PARQUET)""")
    return con


def resumen_global(con: duckdb.DuckDBPyConnection, anio: int) -> dict[str, float]:
    """Totales del año: exportaciones, energía, marcado con cada umbral (miles de USD) y cuántos pares país-producto."""
    r = con.execute(f"""SELECT SUM(x), SUM(CASE WHEN excluido_energia THEN x ELSE 0 END), SUM(CASE WHEN reexportacion THEN x ELSE 0 END), SUM(CASE WHEN reexp_025 THEN x ELSE 0 END),
                               SUM(CASE WHEN reexp_100 THEN x ELSE 0 END), COUNT(*), SUM(CASE WHEN reexportacion THEN 1 ELSE 0 END)
                        FROM depurado WHERE anio = {anio}""").fetchone()
    return dict(zip(["x", "energia", "marcado_05", "marcado_025", "marcado_100", "pares", "pares_marcados_05"], r, strict=True))


def proporcion_por_pais(con: duckdb.DuckDBPyConnection, anio: int, minimo: float = 1e7) -> pd.DataFrame:
    """Por país con exportaciones sin energía de al menos `minimo` (miles de USD): valor marcado y su proporción, con los tres umbrales."""
    return con.execute(f"""
        SELECT iso3, SUM(x) AS x,
               SUM(CASE WHEN reexportacion THEN x ELSE 0 END) / SUM(x) AS prop_05,
               SUM(CASE WHEN reexp_025 THEN x ELSE 0 END) / SUM(x) AS prop_025,
               SUM(CASE WHEN reexp_100 THEN x ELSE 0 END) / SUM(x) AS prop_100
        FROM depurado WHERE anio = {anio} AND NOT excluido_energia AND iso3 IS NOT NULL GROUP BY 1 HAVING SUM(x) >= {minimo} ORDER BY prop_05 DESC""").df()


def paraguay(con: duckdb.DuckDBPyConnection, anio: int, iso3: str = "PRY", n: int = 20) -> tuple[dict[str, float], pd.DataFrame]:
    """Antes y después para un país: totales y sus `n` principales productos HS6 con razón M/X y marcas."""
    tot = con.execute(f"""SELECT SUM(x), SUM(CASE WHEN excluido_energia THEN x ELSE 0 END), SUM(CASE WHEN reexportacion AND NOT excluido_energia THEN x ELSE 0 END)
                          FROM depurado WHERE anio = {anio} AND iso3 = '{iso3}'""").fetchone()
    top = con.execute(f"""SELECT hs6, x, m, razon_m_x, reexportacion, reexp_025, reexp_100, excluido_energia FROM depurado WHERE anio = {anio} AND iso3 = '{iso3}'
                          ORDER BY x DESC LIMIT {n}""").df()
    return dict(zip(["total", "energia", "reexportado_sin_energia"], tot, strict=True)), top


def main() -> None:
    import sys

    sys.stdout.reconfigure(encoding="utf-8")
    con = depurar()
    g = resumen_global(con, 2019)
    print(f"2019 mundo: {g['x'] / 1e9:.2f} billones; energía binacional {100 * g['energia'] / g['x']:.2f} %; marcado (θ=0,5) {100 * g['marcado_05'] / g['x']:.1f} % "
          f"(θ=0,25: {100 * g['marcado_025'] / g['x']:.1f} %; θ=1: {100 * g['marcado_100'] / g['x']:.1f} %); pares marcados {int(g['pares_marcados_05']):,} de {int(g['pares']):,}")
    pp = proporcion_por_pais(con, 2019)
    print("\nMayor proporción marcada 2019 (θ=0,5, países con > USD 10 mil millones sin energía):")
    print(pp.head(12).round(3).to_string(index=False))
    t, top = paraguay(con, 2019)
    print(f"\nParaguay 2019: total {t['total'] / 1e6:.2f} mil millones; energía {t['energia'] / 1e6:.2f}; reexportado (sin energía) {t['reexportado_sin_energia'] / 1e6:.2f}")
    print(top.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
