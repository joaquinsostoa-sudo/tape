"""Robustez de la definición de la entrada (tarea 1.11): ¿el resultado «las capas no mejoran a la densidad sola» depende de cómo
se define la entrada?

Repite el backtest fuera de muestra con otras definiciones y compara `capas` contra `densidad_sola` en cada una:
- `base`: RCA_t < 0,5 y RCA_t+5 ≥ 1 (D7).
- `h10`: horizonte de 10 años (ventanas 2000, 2005 y 2010; una sola prueba posible, 2010→2020).
- `dos_de_tres`: RCA ≥ 1 en 2 de los 3 años que terminan en t + 5 (variante de robustez de D7).
- `inicio_025`: parte de RCA_t < 0,25 (más exigente: productos más lejanos).
- `inicio_100`: parte de RCA_t < 1 (la definición habitual de «aparición»).
- `fin_150`: llega a RCA_t+5 ≥ 1,5 (más exigente: ventaja más clara).

Uso: uv run python -m src.modelos.robustez_entrada
"""
from __future__ import annotations

import argparse

import pandas as pd

from src.modelos import backtest_nacional as bt
from src.modelos.logit_nacional import CLEAN, MODELO, VENTANAS, construir_datos

VARIANTES = {
    "base": {},
    "h10": {"ventanas": (2000, 2005, 2010), "h": 10},
    "dos_de_tres": {"dos_de_tres": True},
    "inicio_025": {"inicio_max": 0.25},
    "inicio_100": {"inicio_max": 1.0},
    "fin_150": {"fin_min": 1.5},
}


def evaluar_variante(df: pd.DataFrame, ventanas, h: int) -> list[dict]:
    """Una fila por ventana de prueba: tasa base, precision@20 por país de cada modelo y diferencias con intervalo."""
    filas = []
    for t in (v for v in ventanas if bt.ventanas_previas(v, ventanas, h)):
        res = bt.evaluar_ventana(df, t, h=h, ventanas=ventanas)
        pru, p = res["prueba"], res["puntajes"]
        dif = {(r["metrica"]): r for r in bt.comparar_con_densidad_sola(res, ("capas",))}
        p20 = {m: float(bt.precision_por_pais(pru, p[m], 20).mean()) for m in ("densidad_cruda", "prior_producto", "densidad_sola", "capas")}
        filas.append({"ventana": f"{t}→{t + h}", "paises": pru.iso3.nunique(), "entradas": int(pru.E.sum()),
                      "tasa_base": float(pru.E.mean()), **{f"p20_{m}": v for m, v in p20.items()},
                      "dif_p20": dif["p_pais_20"]["dif"], "dif_p20_inf": dif["p_pais_20"]["ic_inf"], "dif_p20_sup": dif["p_pais_20"]["ic_sup"],
                      "dif_auc": dif["auc_pr"]["dif"], "dif_auc_inf": dif["auc_pr"]["ic_inf"], "dif_auc_sup": dif["auc_pr"]["ic_sup"]})
    return filas


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--expo", default=str(MODELO / "exportaciones_hs4.parquet"))
    ap.add_argument("--salida", default=str(MODELO / "robustez_entrada.csv"))
    ap.add_argument("--variantes", nargs="*", default=list(VARIANTES))
    args = ap.parse_args(argv)
    expo = pd.read_parquet(args.expo)
    dot = pd.read_parquet(CLEAN / "dotaciones.parquet")
    req = pd.read_csv(CLEAN / "requisitos_producto_hs4.csv", dtype={"hs4": str})
    pob = pd.read_csv(CLEAN / "poblacion_pais.csv")
    todas = []
    for nombre in args.variantes:
        cfg = dict(VARIANTES[nombre])
        ventanas, h = cfg.pop("ventanas", VENTANAS), cfg.pop("h", 5)
        df = construir_datos(expo, dot, req, pob, ventanas=ventanas, h=h, **cfg)
        filas = [{"variante": nombre, **f} for f in evaluar_variante(df, ventanas, h)]
        todas += filas
        print(f"\n=== {nombre}")
        t = pd.DataFrame(filas)
        t["dif precision@20"] = [f"{r.dif_p20:+.3f} ({r.dif_p20_inf:+.3f}; {r.dif_p20_sup:+.3f})" for r in t.itertuples()]
        t["dif AUC-PR"] = [f"{r.dif_auc:+.3f} ({r.dif_auc_inf:+.3f}; {r.dif_auc_sup:+.3f})" for r in t.itertuples()]
        print(t[["ventana", "paises", "entradas", "tasa_base", "p20_densidad_sola", "p20_capas", "dif precision@20", "dif AUC-PR"]]
              .round(3).to_string(index=False))
    pd.DataFrame(todas).to_csv(args.salida, index=False)
    print(f"\n-> {args.salida}")


if __name__ == "__main__":
    main()
