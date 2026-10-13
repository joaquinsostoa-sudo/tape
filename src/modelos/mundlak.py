"""Variante sin efectos fijos (D2 b, estilo Mundlak): ¿las capas aportan cuando no hay efectos de país y producto que las absorban?

En el logit del backtest, los efectos fijos de país y producto absorben las dotaciones y los requisitos por separado; solo las
interacciones r·a quedan libres. Acá se quitan los efectos fijos y se los reemplaza por sus aproximaciones de efectos
correlacionados (Mundlak): la densidad media del país y la densidad media del producto en la misma ventana (solo datos
de t0, sin etiquetas). Como no hay efectos por país, el modelo puede predecir países que no estaban en el entrenamiento.
Modelos (mismo esquema fuera de muestra y mismas filas que `backtest_nacional.py`):
- `mundlak_densidad`: densidad + densidad media del país + densidad media del producto.
- `mundlak_efectos`: + dotaciones del país (a_k) y requisitos del producto (r_k) por separado.
- `mundlak_capas`: + las interacciones r·a.

Uso: uv run python -m src.modelos.mundlak
"""
from __future__ import annotations

import argparse

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

from src.modelos import backtest_nacional as bt
from src.modelos.logit_nacional import (
    CAPAS_PRINCIPALES,
    CLEAN,
    MODELO,
    VENTANAS,
    H,
    construir_datos,
)

COLS_A = [f"a_{c}" for c in CAPAS_PRINCIPALES]
COLS_R = [f"r_{c}" for c in CAPAS_PRINCIPALES]
COLS_RA = [f"ra_{c}" for c in CAPAS_PRINCIPALES]
COLS_DENS = ["d_z", "dbar_pais", "dbar_prod"]
ESPECIFICACIONES = {
    "mundlak_densidad": COLS_DENS,
    "mundlak_efectos": COLS_DENS + COLS_A + COLS_R,
    "mundlak_capas": COLS_DENS + COLS_A + COLS_R + COLS_RA,
}


def agregar_medias(d: pd.DataFrame) -> pd.DataFrame:
    """Densidad media del país y del producto dentro de cada ventana (usa solo la densidad de t0, no las etiquetas)."""
    d = d.copy()
    d["dbar_pais"] = d.groupby(["anio", "iso3"]).d_z.transform("mean")
    d["dbar_prod"] = d.groupby(["anio", "hs4"]).d_z.transform("mean")
    return d


def estandarizar(ent: pd.DataFrame, pru: pd.DataFrame, cols: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Estandariza `cols` con la media y el desvío del entrenamiento (nada de la prueba entra en la escala)."""
    mu, sd = ent[cols].mean(), ent[cols].std().replace(0, 1.0)
    e, p = ent.copy(), pru.copy()
    e[cols], p[cols] = (ent[cols] - mu) / sd, (pru[cols] - mu) / sd
    return e, p


def evaluar_ventana_mundlak(df: pd.DataFrame, t_prueba: int, C: float = 1.0) -> dict:
    res = bt.evaluar_ventana(df, t_prueba)
    ent, pru = agregar_medias(res["entrenamiento"]), agregar_medias(res["prueba"])
    todas = sorted({c for cols in ESPECIFICACIONES.values() for c in cols})
    ent, pru = estandarizar(ent, pru, todas)
    p = res["puntajes"]
    res["puntajes"] = {"azar": p["azar"], "densidad_sola": p["densidad_sola"], "capas": p["capas"]}
    res["coeficientes"] = {}
    for nombre, cols in ESPECIFICACIONES.items():
        m = LogisticRegression(C=C, max_iter=2000).fit(ent[cols].to_numpy(), ent.E.to_numpy())
        res["puntajes"][nombre] = m.predict_proba(pru[cols].to_numpy())[:, 1]
        res["coeficientes"][nombre] = dict(zip(cols, np.round(m.coef_[0], 3), strict=True))
    return res


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--expo", default=str(MODELO / "exportaciones_hs4.parquet"))
    ap.add_argument("--salida", default=str(MODELO / "mundlak_resultados.csv"))
    args = ap.parse_args(argv)
    df = construir_datos(pd.read_parquet(args.expo), pd.read_parquet(CLEAN / "dotaciones.parquet"),
                         pd.read_csv(CLEAN / "requisitos_producto_hs4.csv", dtype={"hs4": str}),
                         pd.read_csv(CLEAN / "poblacion_pais.csv"))
    resumen, difs = [], []
    for t in (v for v in VENTANAS if bt.ventanas_previas(v)):
        res = evaluar_ventana_mundlak(df, t)
        print(f"\n=== Prueba {t} → {t + H} ({len(res['prueba']):,} filas, {int(res['prueba'].E.sum())} entradas)")
        filas = bt.resumen_ventana(res, t)
        resumen += filas
        print(pd.DataFrame(filas).drop(columns=["ventana", "filas", "paises", "entradas"]).round(3).to_string(index=False))
        for nombre, base in (("mundlak_efectos", "mundlak_densidad"), ("mundlak_capas", "mundlak_densidad"),
                             ("mundlak_capas", "mundlak_efectos"), ("mundlak_densidad", "densidad_sola")):
            d = pd.DataFrame(bt.comparar_con_densidad_sola(res, (nombre,), base)).assign(ventana=t, contra=base)
            difs.append(d)
            print(d.round(3).to_string(index=False))
        print("coeficientes (estandarizados) de mundlak_capas:", res["coeficientes"]["mundlak_capas"])
    pd.DataFrame(resumen).to_csv(args.salida, index=False)
    pd.concat(difs).to_csv(str(args.salida).replace(".csv", "_diferencias.csv"), index=False)
    print(f"\n-> {args.salida}")


if __name__ == "__main__":
    main()
