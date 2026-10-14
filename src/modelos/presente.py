"""Prueba de corte transversal: ¿las dotaciones explican lo que se produce hoy? (declarada el 2026-10-13, ver `docs/supuestos.md`).

Resultado: presencia en t = 1[RCA_t ≥ 1] para todos los pares país × producto HS4 (incluidos los de RCA = 0), años 2000, 2005, 2010 y 2015.
Modelo: logit con efectos fijos de país-año y producto-año, errores agrupados por país (D2 c). Dos bloques:
- M (manufactura): productos con requisitos de NBER-CES; términos r × a de las cuatro capas vigentes.
- R (recursos naturales): todos los productos; indicador «producto basado en tierra» × tierra cultivable por persona (WDI, log, estandarizada).
Se informa el signo y la significancia de cada coeficiente (hipótesis: todos positivos) y la mejora de la log-verosimilitud sobre el modelo de
solo efectos fijos. Sensibilidades: año por año, control r × PIB per cápita y faltantes revelados (parcialmente circulares).

Uso: uv run python -m src.modelos.presente
"""
from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

from src.modelos.logit_disperso import LogitEfectosFijos
from src.modelos.logit_nacional import CLEAN, MODELO, VENTANAS, construir_datos, sin_variacion, z

CAPITULOS_TIERRA = {"01", "02", "04", *(f"{c:02d}" for c in range(6, 16)), "17", "18", "23", "24", "52"}
FE = ["pais_ventana", "producto_ventana"]
CAPAS_M = ["energia", "capital_humano", "capital_fisico", "logistica"]
COLS_M = [f"ra_{c}" for c in CAPAS_M]
COLS_M_CONTROL = [*COLS_M, *(f"rpib_{c}" for c in CAPAS_M)]
COLS_F = [f"f_{c}" for c in (*CAPAS_M, "pib")]


def es_de_tierra(hs4: pd.Series) -> pd.Series:
    """Producto basado en tierra: capítulos HS de animales, carne, lácteos, plantas, cereales, oleaginosas, azúcar, cacao, forraje, tabaco y algodón."""
    return hs4.str[:2].isin(CAPITULOS_TIERRA)


def agregar_tierra(df: pd.DataFrame, dot: pd.DataFrame) -> pd.DataFrame:
    """Agrega a_tierra (log de tierra cultivable por persona, estandarizada entre los países de la muestra de cada año) y los términos de tierra."""
    d = df.merge(dot[["iso3", "anio", "log_tierra"]], on=["iso3", "anio"], how="left")
    paises = d.drop_duplicates(["anio", "iso3"])[["anio", "iso3", "log_tierra"]]
    paises["a_tierra"] = paises.groupby("anio").log_tierra.transform(z)
    d = d.drop(columns="log_tierra").merge(paises[["anio", "iso3", "a_tierra"]], on=["anio", "iso3"], how="left")
    d["tierra"] = es_de_tierra(d.hs4).astype(float)
    d["ra_tierra"] = d.tierra * d.a_tierra
    d["rpib_tierra"] = d.tierra * d.a_pib
    return d


def _ll(y: np.ndarray, p: np.ndarray) -> float:
    p = np.clip(p, 1e-12, 1 - 1e-12)
    return float(np.sum(y * np.log(p) + (1 - y) * np.log(1 - p)))


def ajustar_con_ll(df: pd.DataFrame, columnas: list[str]) -> tuple[pd.DataFrame, dict]:
    """Coeficientes con errores agrupados por país y mejora de la log-verosimilitud sobre el modelo de solo efectos fijos (mismas filas)."""
    d = sin_variacion(df.dropna(subset=columnas), "E", FE)
    y = d.E.to_numpy(dtype=float)
    m = LogitEfectosFijos(columnas, FE, C=None).ajustar(d, "E")
    base = LogitEfectosFijos([], FE, C=None).ajustar(d, "E")
    ll1, ll0 = _ll(y, m.predecir(d)), _ll(y, base.predecir(d))
    info = {"filas": len(d), "presencias": int(y.sum()), "paises": d.iso3.nunique(), "productos": d.hs4.nunique(),
            "mejora_ll_por_mil": 1000 * (ll1 - ll0) / len(d), "lr": 2 * (ll1 - ll0)}
    return m.errores_agrupados(d, "E", "iso3"), info


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--expo", default=str(MODELO / "exportaciones_hs4.parquet"))
    ap.add_argument("--salida", default=str(MODELO / "presente_resultados.csv"))
    args = ap.parse_args(argv)
    dot = pd.read_parquet(CLEAN / "dotaciones.parquet")
    df = construir_datos(pd.read_parquet(args.expo), dot, pd.read_csv(CLEAN / "requisitos_producto_hs4.csv", dtype={"hs4": str}),
                         pd.read_csv(CLEAN / "poblacion_pais.csv"), ventanas=VENTANAS, h=0, inicio_max=np.inf,
                         revelados=True, solo_con_requisitos=False)
    df = agregar_tierra(df, dot)
    print(f"tabla: {len(df):,} filas, {int(df.E.sum()):,} presencias ({100 * df.E.mean():.1f} %), {df.iso3.nunique()} países, {df.hs4.nunique()} productos; "
          f"productos de tierra: {df[df.tierra == 1].hs4.nunique()}")
    con_req = df[df.r_energia.notna()]
    modelos = {  # nombre -> (tabla, columnas)
        "M_manufactura": (con_req, COLS_M),
        "R_tierra": (df, ["ra_tierra"]),
        "M_con_control_pib": (con_req, COLS_M_CONTROL),
        "R_con_control_pib": (df, ["ra_tierra", "rpib_tierra"]),
        "faltantes_revelados": (df, COLS_F),
    }
    filas = []
    for nombre, (d, cols) in modelos.items():
        for periodo, sub in [("agrupado", d), *[(str(t), d[d.anio == t]) for t in VENTANAS]]:
            if nombre.endswith("control_pib") and periodo != "agrupado":
                continue
            tabla, info = ajustar_con_ll(sub, cols)
            print(f"\n== {nombre} · {periodo}: {info['filas']:,} filas, {info['presencias']:,} presencias, {info['paises']} países, "
                  f"mejora de log-verosimilitud {info['mejora_ll_por_mil']:.2f} por mil obs. (LR = {info['lr']:.0f})")
            print(tabla.round(4).to_string())
            filas.append(tabla.reset_index(names="variable").assign(modelo=nombre, periodo=periodo, **info))
    pd.concat(filas).to_csv(args.salida, index=False)
    print(f"\n-> {args.salida}")


if __name__ == "__main__":
    main()
