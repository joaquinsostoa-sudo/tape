"""XGBoost de control con SHAP (tarea 1.10): ¿hay poder predictivo en las capas que el logit no captura?

Mismo esquema fuera de muestra que `backtest_nacional.py` (se entrena solo con ventanas cuyo resultado ya se conocía)
y las mismas filas. Dos modelos con los mismos hiperparámetros, fijados de antemano y sin ajustar en la ventana de prueba:
- `xgb_densidad`: densidad + país y producto como variables categóricas (el equivalente de los efectos fijos).
- `xgb_capas`: lo anterior + las dotaciones del país (a_k) y los requisitos del producto (r_k); los árboles pueden
  armar solos las interacciones r·a y relaciones no lineales.
Si `xgb_capas` no supera a `xgb_densidad`, la conclusión de que las capas no aportan no depende de la forma lineal del logit.
SHAP: valores exactos de TreeSHAP de XGBoost (`pred_contribs`), agrupados por tipo de variable.

Uso: uv run python -m src.modelos.xgb_control
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb

from src.modelos import backtest_nacional as bt
from src.modelos.logit_nacional import (
    CAPAS_PRINCIPALES,
    CLEAN,
    MODELO,
    RAIZ,
    VENTANAS,
    H,
    construir_datos,
)

COLS_A = [f"a_{c}" for c in CAPAS_PRINCIPALES]
COLS_R = [f"r_{c}" for c in CAPAS_PRINCIPALES]
HIPERPARAMETROS = {"n_estimators": 300, "learning_rate": 0.05, "max_depth": 4, "subsample": 0.8, "colsample_bytree": 0.8,
                   "min_child_weight": 5, "reg_lambda": 5.0, "tree_method": "hist", "enable_categorical": True,
                   "objective": "binary:logistic", "random_state": 0, "n_jobs": 4}


def matriz(df: pd.DataFrame, numericas: list[str], categorias: dict[str, pd.Index]) -> pd.DataFrame:
    """Variables numéricas más país y producto como categorías (el catálogo es común a entrenamiento y prueba)."""
    x = df[numericas].reset_index(drop=True).copy()
    for col in ("iso3", "hs4"):
        x[col] = pd.Categorical(df[col].to_numpy(), categories=categorias[col])
    return x


def ajustar_predecir(ent: pd.DataFrame, pru: pd.DataFrame, numericas: list[str]) -> tuple[np.ndarray, xgb.XGBClassifier, pd.DataFrame]:
    cats = {c: pd.Index(sorted(set(ent[c]) | set(pru[c]))) for c in ("iso3", "hs4")}
    m = xgb.XGBClassifier(**HIPERPARAMETROS).fit(matriz(ent, numericas, cats), ent.E.to_numpy())
    x_pru = matriz(pru, numericas, cats)
    return m.predict_proba(x_pru)[:, 1], m, x_pru


def shap_por_grupo(m: xgb.XGBClassifier, x: pd.DataFrame, n: int = 20000, semilla: int = 0) -> pd.Series:
    """|SHAP| medio por variable (TreeSHAP exacto de XGBoost) sobre una muestra de `x`, en orden descendente."""
    muestra = x.sample(min(n, len(x)), random_state=semilla)
    contrib = m.get_booster().predict(xgb.DMatrix(muestra, enable_categorical=True), pred_contribs=True)[:, :-1]
    return pd.Series(np.abs(contrib).mean(axis=0), index=muestra.columns).sort_values(ascending=False)


def evaluar_ventana_xgb(df: pd.DataFrame, t_prueba: int) -> dict:
    res = bt.evaluar_ventana(df, t_prueba)
    ent, pru = res["entrenamiento"], res["prueba"]
    base = ["densidad"]
    s_d, _, _ = ajustar_predecir(ent, pru, base)
    s_c, m_c, x_c = ajustar_predecir(ent, pru, base + COLS_A + COLS_R)
    res["puntajes"]["xgb_densidad"], res["puntajes"]["xgb_capas"] = s_d, s_c
    res["modelo_capas"], res["x_capas"] = m_c, x_c
    return res


def figura_shap(shap: pd.Series, ruta: Path, titulo: str) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    colores = {"densidad": "#1f77b4", "iso3": "#7f7f7f", "hs4": "#7f7f7f"}
    fig, ax = plt.subplots(figsize=(7, 4.2))
    s = shap.sort_values()
    ax.barh(s.index, s.values, color=[colores.get(i, "#d95f02" if i.startswith("a_") else "#1b9e77") for i in s.index])
    ax.set_xlabel("|SHAP| medio (en logit de la probabilidad de entrada)")
    ax.set_title(titulo, fontsize=10)
    ax.text(0.99, 0.04, "azul: densidad · gris: país y producto · naranja: dotaciones del país · verde: requisitos del producto",
            transform=ax.transAxes, ha="right", fontsize=7)
    fig.tight_layout()
    ruta.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(ruta, dpi=140)
    plt.close(fig)


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--expo", default=str(MODELO / "exportaciones_hs4.parquet"))
    ap.add_argument("--salida", default=str(MODELO / "xgb_resultados.csv"))
    args = ap.parse_args(argv)
    df = construir_datos(pd.read_parquet(args.expo), pd.read_parquet(CLEAN / "dotaciones.parquet"),
                         pd.read_csv(CLEAN / "requisitos_producto_hs4.csv", dtype={"hs4": str}),
                         pd.read_csv(CLEAN / "poblacion_pais.csv"))
    resumen, difs = [], []
    ultimo = None
    for t in (v for v in VENTANAS if bt.ventanas_previas(v)):
        res = evaluar_ventana_xgb(df, t)
        p = res["puntajes"]
        res["puntajes"] = {k: p[k] for k in ("azar", "densidad_sola", "capas", "xgb_densidad", "xgb_capas")}
        print(f"\n=== Prueba {t} → {t + H} ({len(res['prueba']):,} filas, {int(res['prueba'].E.sum())} entradas)")
        filas = bt.resumen_ventana(res, t)
        resumen += filas
        print(pd.DataFrame(filas).drop(columns=["ventana", "filas", "paises", "entradas"]).round(3).to_string(index=False))
        for nombre, base in (("xgb_capas", "xgb_densidad"), ("xgb_densidad", "densidad_sola"), ("xgb_capas", "densidad_sola")):
            d = pd.DataFrame(bt.comparar_con_densidad_sola(res, (nombre,), base)).assign(ventana=t, contra=base)
            difs.append(d)
            print(d.round(3).to_string(index=False))
        ultimo = (t, res)
    pd.DataFrame(resumen).to_csv(args.salida, index=False)
    pd.concat(difs).to_csv(str(args.salida).replace(".csv", "_diferencias.csv"), index=False)
    t, res = ultimo
    shap = shap_por_grupo(res["modelo_capas"], res["x_capas"])
    print(f"\n|SHAP| medio de xgb_capas en la prueba {t}:\n{shap.round(4).to_string()}")
    figura_shap(shap, RAIZ / "docs" / "figuras" / "xgb_shap.png", f"XGBoost con capas: importancia (SHAP), prueba {t}→{t + H}")
    print(f"\n-> {args.salida}")


if __name__ == "__main__":
    main()
