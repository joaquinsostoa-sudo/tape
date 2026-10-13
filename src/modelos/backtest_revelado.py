"""Backtest con requisitos revelados (paso 2 del plan de las capas): ¿el faltante de dotación respecto de los productores mejora
la predicción fuera de muestra por encima de la densidad sola?

Especificación principal, declarada de antemano (A1 + B1 + C1 + D1 + E1): densidad + el faltante de las cuatro capas respecto de la
mediana de los países con presencia en el producto + el faltante de ingreso (log PIB per cápita) como control, con efectos fijos de
país y producto. Hipótesis: los cuatro coeficientes de capas son negativos. Criterio de éxito: supera a `densidad_sola` en precision@20
por país con intervalo del 95 % que excluya el cero en al menos dos de las tres ventanas de prueba.
Comparaciones adicionales: `solo_ingreso` (¿importan las capas más allá del ingreso?) y sensibilidades (media, percentil 25, distancia
absoluta), que no cuentan para el criterio de éxito. Dos muestras: todos los productos de BACI y solo los que tienen requisitos de NBER-CES.

Uso: uv run python -m src.modelos.backtest_revelado
"""
from __future__ import annotations

import argparse

import pandas as pd

from src.modelos import backtest_nacional as bt
from src.modelos.logit_disperso import LogitEfectosFijos
from src.modelos.logit_nacional import CLEAN, MODELO, VENTANAS, construir_datos
from src.modelos.requisito_revelado import CAPAS_REVELADAS

CAPAS4 = [c for c in CAPAS_REVELADAS if c != "pib"]
MODELOS = {  # nombre -> columnas (además de d_z)
    "reveladas": [f"f_{c}" for c in CAPAS_REVELADAS],
    "reveladas_sin_ingreso": [f"f_{c}" for c in CAPAS4],
    "solo_ingreso": ["f_pib"],
    "sens_media": [f"fmedia_{c}" for c in CAPAS_REVELADAS],
    "sens_p25": [f"fp25_{c}" for c in CAPAS_REVELADAS],
    "sens_distancia": [f"fdist_{c}" for c in CAPAS_REVELADAS],
}
COMPARACIONES = [("reveladas", "densidad_sola"), ("reveladas", "solo_ingreso"), ("reveladas_sin_ingreso", "densidad_sola"),
                 ("sens_media", "densidad_sola"), ("sens_p25", "densidad_sola"), ("sens_distancia", "densidad_sola")]


def evaluar(df: pd.DataFrame, t_prueba: int) -> dict:
    res = bt.evaluar_ventana(df, t_prueba, columnas_capas=MODELOS["reveladas"])
    ent, pru = res["entrenamiento"], res["prueba"]
    p = {"azar": res["puntajes"]["azar"], "densidad_sola": res["puntajes"]["densidad_sola"]}
    for nombre, cols in MODELOS.items():
        p[nombre] = bt.ajustar_y_predecir(ent, pru, ["d_z", *cols])
    res["puntajes"] = p
    m = LogitEfectosFijos(["d_z", *MODELOS["reveladas"]], bt.EFECTOS, C=10).ajustar(ent, "E")
    res["coeficientes"] = {k: round(v, 3) for k, v in m.coeficientes.items()}
    return res


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--expo", default=str(MODELO / "exportaciones_hs4.parquet"))
    ap.add_argument("--salida", default=str(MODELO / "backtest_revelado.csv"))
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
            print(f"\n=== {muestra} · prueba {t}→{t + 5}: {len(pru):,} filas, {int(pru.E.sum())} entradas, {pru.iso3.nunique()} países, "
                  f"{pru.hs4.nunique()} productos")
            print("coeficientes de `reveladas` (entrenamiento):", res["coeficientes"])
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
