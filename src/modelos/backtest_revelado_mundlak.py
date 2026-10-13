"""Requisito revelado sin efectos fijos, estilo Mundlak (especificación declarada el 2026-10-13, ver `docs/supuestos.md`).

`mundlak_reveladas`: regresión logística (C = 1) con densidad, densidad media del país y del producto en la ventana y los cinco
faltantes revelados (energía, capital humano, capital físico, logística e ingreso), sin efectos fijos. Hipótesis: los cuatro
coeficientes de capas son negativos. Dos pruebas separadas, ambas con el criterio de éxito acordado (diferencia positiva en
precision@20 por país con intervalo del 95 % que excluye el cero en al menos dos de tres ventanas):
(i) aporte de las capas: `mundlak_reveladas` − `mundlak_densidad`; (ii) condición de paso de la Fase 1: `mundlak_reveladas` −
`densidad_sola` (logit con efectos fijos). `mundlak_reveladas_sin_ingreso` es solo sensibilidad.

Uso: uv run python -m src.modelos.backtest_revelado_mundlak
"""
from __future__ import annotations

import argparse

import pandas as pd
from sklearn.linear_model import LogisticRegression

from src.modelos import backtest_nacional as bt
from src.modelos import mundlak as mk
from src.modelos.logit_nacional import CLEAN, MODELO, VENTANAS, construir_datos
from src.modelos.requisito_revelado import CAPAS_REVELADAS

CAPAS4 = [c for c in CAPAS_REVELADAS if c != "pib"]
F5 = [f"f_{c}" for c in CAPAS_REVELADAS]
F4 = [f"f_{c}" for c in CAPAS4]
MODELOS = {
    "mundlak_densidad": mk.COLS_DENS,
    "mundlak_reveladas": mk.COLS_DENS + F5,
    "mundlak_reveladas_sin_ingreso": mk.COLS_DENS + F4,
}
COMPARACIONES = [("mundlak_reveladas", "mundlak_densidad"), ("mundlak_reveladas", "densidad_sola"),
                 ("mundlak_reveladas_sin_ingreso", "mundlak_densidad")]


def evaluar(df: pd.DataFrame, t_prueba: int, C: float = 1.0) -> dict:
    res = bt.evaluar_ventana(df, t_prueba, columnas_capas=F5)
    ent, pru = mk.agregar_medias(res["entrenamiento"]), mk.agregar_medias(res["prueba"])
    todas = sorted({c for cols in MODELOS.values() for c in cols})
    ent, pru = mk.estandarizar(ent, pru, todas)
    p = {"azar": res["puntajes"]["azar"], "densidad_sola": res["puntajes"]["densidad_sola"]}
    res["coeficientes"] = {}
    for nombre, cols in MODELOS.items():
        m = LogisticRegression(C=C, max_iter=3000).fit(ent[cols].to_numpy(), ent.E.to_numpy())
        p[nombre] = m.predict_proba(pru[cols].to_numpy())[:, 1]
        res["coeficientes"][nombre] = {c: round(float(v), 3) for c, v in zip(cols, m.coef_[0], strict=True)}
    res["puntajes"] = p
    return res


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--expo", default=str(MODELO / "exportaciones_hs4.parquet"))
    ap.add_argument("--salida", default=str(MODELO / "backtest_revelado_mundlak.csv"))
    args = ap.parse_args(argv)
    df = construir_datos(pd.read_parquet(args.expo), pd.read_parquet(CLEAN / "dotaciones.parquet"),
                         pd.read_csv(CLEAN / "requisitos_producto_hs4.csv", dtype={"hs4": str}),
                         pd.read_csv(CLEAN / "poblacion_pais.csv"), revelados=True, solo_con_requisitos=False)
    muestras = {"todos_los_productos": df, "solo_con_requisitos": df[df.r_energia.notna()]}
    filas, difs = [], []
    for muestra, d in muestras.items():
        for t in (v for v in VENTANAS if bt.ventanas_previas(v)):
            res = evaluar(d, t)
            pru = res["prueba"]
            print(f"\n=== {muestra} · prueba {t}→{t + 5}: {len(pru):,} filas, {int(pru.E.sum())} entradas, {pru.iso3.nunique()} países")
            print("coeficientes (estandarizados) de mundlak_reveladas:", res["coeficientes"]["mundlak_reveladas"])
            r = bt.resumen_ventana(res, t)
            filas += [{"muestra": muestra, **x} for x in r]
            print(pd.DataFrame(r)[["modelo", "tasa_base", "auc_pr", "p_pais_10", "p_pais_20"]].round(3).to_string(index=False))
            for modelo, base in COMPARACIONES:
                d_ = pd.DataFrame(bt.comparar_con_densidad_sola(res, (modelo,), base)).assign(muestra=muestra, ventana=t, contra=base)
                difs.append(d_)
                x = d_.set_index("metrica")
                print(f"  {modelo} − {base}: p@20 {x.loc['p_pais_20', 'dif']:+.3f} ({x.loc['p_pais_20', 'ic_inf']:+.3f}; "
                      f"{x.loc['p_pais_20', 'ic_sup']:+.3f}) | AUC-PR {x.loc['auc_pr', 'dif']:+.3f} ({x.loc['auc_pr', 'ic_inf']:+.3f}; "
                      f"{x.loc['auc_pr', 'ic_sup']:+.3f})")
    pd.DataFrame(filas).to_csv(args.salida, index=False)
    pd.concat(difs).to_csv(str(args.salida).replace(".csv", "_diferencias.csv"), index=False)
    print(f"\n-> {args.salida}")


if __name__ == "__main__":
    main()
