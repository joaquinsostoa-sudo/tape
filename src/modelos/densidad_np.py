"""Proximidad (φ) y densidad por ventana, calculadas en memoria con numpy (misma definición que `densidad.py`).

La versión en SQL (`densidad.py`) une la tabla de proximidad (≈ 2.000 vecinos por producto) con cada par país-producto
(≈ 600.000) y recién después suma: genera del orden de mil millones de filas por ventana. Acá la densidad es un producto
de matrices pequeñas:

    C = Mᵀ M                      (conteo de países con ambos productos; M = presencia país × producto)
    φ_ij = min(C_ij / C_ii, C_ij / C_jj)   si C_ij ≥ umbral, i ≠ j; 0 en otro caso
    densidad_cp = Σ_j φ_pj M_cj / Σ_j φ_pj

Con ~230 países y ~5.000 productos, M ocupa 5 MB y φ 100 MB (float32): corre en segundos y no usa disco.
Definición (D3): la presencia de la ventana [ini, fin] se usa para predecir desde fin + 1, sin datos posteriores.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

UMBRAL_BOTH = 5  # mínimo de países con ambos productos para que exista proximidad (igual que densidad.py)


def matriz_presencia(pres: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(M, paises, productos): M[c, p] = 1 si el país c tiene presencia en el producto p. `pres` trae country, product."""
    paises = np.sort(pres.country.unique())
    productos = np.sort(pres["product"].unique())
    ci = np.searchsorted(paises, pres.country.to_numpy())
    pi = np.searchsorted(productos, pres["product"].to_numpy())
    m = np.zeros((len(paises), len(productos)), dtype=np.float32)
    m[ci, pi] = 1.0
    return m, paises, productos


def proximidad(m: np.ndarray, umbral: int = UMBRAL_BOTH) -> np.ndarray:
    """Matriz simétrica φ (productos × productos), float32. φ_ij = min(P(i|j), P(j|i)) con ≥ `umbral` países en común."""
    c = m.T @ m  # float32: conteos exactos mientras haya menos de 16 millones de países
    total = np.diag(c).copy()
    with np.errstate(divide="ignore", invalid="ignore"):
        phi = np.minimum(c / total[:, None], c / total[None, :])
    phi[c < umbral] = 0.0
    np.fill_diagonal(phi, 0.0)
    return np.nan_to_num(phi, copy=False)


def densidad(m: np.ndarray, phi: np.ndarray, m_base: np.ndarray | None = None) -> np.ndarray:
    """d_cp = Σ_j φ_pj M_cj / Σ_j φ_pj; vale 0 donde un producto no tiene ningún vecino (como en la versión SQL).

    `m_base` es la presencia con la que se mide la densidad de cada país (por defecto, la misma `m`)."""
    base = m if m_base is None else m_base
    suma = phi.sum(axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        d = (base @ phi.T) / suma[None, :]
    return np.nan_to_num(d, nan=0.0, posinf=0.0, neginf=0.0)


def main(argv: list[str] | None = None) -> None:
    """Reemplaza `densidad.py`: lee `presencia_{ini}_{fin}` y `rca_matrix` de la base DuckDB y escribe `densidad_{ini}_{fin}`
    (mismo nombre y columnas que usa `backtest.py`). No crea las tablas `phi_*`: en SQL eran la parte más pesada.

    Uso: uv run python -m src.modelos.densidad_np --db RUTA_A_LA_BASE.duckdb [--phi-dir CARPETA]"""
    import argparse
    import time

    import duckdb

    from .densidad import VENTANAS  # las mismas ventanas que la versión SQL

    ap = argparse.ArgumentParser(description=main.__doc__)
    ap.add_argument("--db", required=True, help="ruta de la base DuckDB con presencia_* y rca_matrix")
    ap.add_argument("--phi-dir", help="si se da, guarda φ de cada ventana en parquet (float32) en esa carpeta")
    args = ap.parse_args(argv)
    con = duckdb.connect(args.db)
    for ini, fin in VENTANAS:
        t0 = time.time()
        pres = con.execute(f"SELECT country, product FROM presencia_{ini}_{fin}").df()
        base = con.execute(f"SELECT DISTINCT country, product FROM rca_matrix WHERE year = {fin}").df()
        m, _paises, productos = matriz_presencia(pres)
        phi = proximidad(m)
        d = densidad_df(pres, base)
        con.register("tmp_dens", d)
        con.execute(f"CREATE OR REPLACE TABLE densidad_{ini}_{fin} AS SELECT country, product, densidad FROM tmp_dens")
        con.unregister("tmp_dens")
        if args.phi_dir:
            from pathlib import Path

            carpeta = Path(args.phi_dir)
            carpeta.mkdir(parents=True, exist_ok=True)
            i, j = np.nonzero(np.triu(phi))
            pd.DataFrame({"p1": productos[i], "p2": productos[j], "proximity": phi[i, j]}).to_parquet(
                carpeta / f"phi_{ini}_{fin}.parquet", index=False)
        print(f"ventana {ini}-{fin}: {len(pres):,} presencias, {int((phi > 0).sum()) // 2:,} pares φ, "
              f"{len(d):,} filas de densidad en {time.time() - t0:.1f} s")
    con.close()


def densidad_df(pres: pd.DataFrame, base: pd.DataFrame, umbral: int = UMBRAL_BOTH) -> pd.DataFrame:
    """Densidad para cada par (country, product) de `base`, con la presencia `pres` de la ventana.

    Pares cuyo país o producto no figura en la presencia: densidad 0.0, igual que la versión SQL."""
    m, paises, productos = matriz_presencia(pres)
    d = densidad(m, proximidad(m, umbral))
    out = base[["country", "product"]].drop_duplicates().copy()
    ci = np.searchsorted(paises, out.country.to_numpy())
    pi = np.searchsorted(productos, out["product"].to_numpy())
    ok = (ci < len(paises)) & (pi < len(productos))
    ok &= paises[np.minimum(ci, len(paises) - 1)] == out.country.to_numpy()
    ok &= productos[np.minimum(pi, len(productos) - 1)] == out["product"].to_numpy()
    out["densidad"] = 0.0
    out.loc[ok, "densidad"] = d[ci[ok], pi[ok]].astype(float)
    return out.reset_index(drop=True)


if __name__ == "__main__":
    main()
