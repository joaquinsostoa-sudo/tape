"""Paso 3 del plan de las capas: entradas a nivel de sector TAPE (especificación declarada el 2026-10-13, ver `docs/supuestos.md`).

Las exportaciones HS4 se pasan a los sectores TAPE con el puente HS92 → sector de la Fase 0 (`puente_hs92_sector.csv`, D1 abierta): el peso de
un producto HS4 en un sector es el valor mundial de sus HS6 asignados a ese sector (por el peso de cada uno) sobre el valor mundial del HS4.
Después se corre la misma maquinaria de HS4 tratando al sector como «producto»: RCA, presencia D13, densidad, entrada D7, faltantes revelados
y esquema fuera de muestra. Métrica: precision@5 por país (unos 40 sectores con comercio). Pruebas declaradas: (a) `reveladas` − `densidad_sola`
con efectos fijos (criterio de éxito); (b) variante sin efectos fijos, (i) aporte de las capas y (ii) frente a `densidad_sola`.

Uso: uv run python -m src.modelos.backtest_sector
"""
from __future__ import annotations

import argparse

import pandas as pd

from src.modelos import backtest_nacional as bt
from src.modelos import backtest_revelado as rv
from src.modelos import backtest_revelado_mundlak as rm
from src.modelos.logit_nacional import CLEAN, HS4_ENERGIA, MODELO, VENTANAS, construir_datos

KS_SECTOR = (3, 5)
REQ_VACIO = pd.DataFrame({"hs4": pd.Series(dtype=str), "energia": pd.Series(dtype=float), "capital": pd.Series(dtype=float),
                          "habilidades": pd.Series(dtype=float), "valor_peso_usd_kg": pd.Series(dtype=float)})


def pesos_hs4_sector(puente: pd.DataFrame) -> pd.DataFrame:
    """Peso de cada producto HS4 en cada sector (hs4, sector_id, w): valor mundial × peso de sus HS6 sobre el valor mundial del HS4.

    Los HS6 sin sector (sin mapeo) y la energía binacional no reparten nada: la masa de un HS4 puede sumar menos de 1."""
    b = puente.copy()
    b["valor"] = pd.to_numeric(b.valor_mundial, errors="coerce").fillna(0.0)
    b["peso"] = pd.to_numeric(b.peso, errors="coerce").fillna(0.0)
    b["hs4"] = b.hs92.str[:4]
    total = b.drop_duplicates("hs92").groupby("hs4").valor.sum().rename("total")
    asignado = b[b.sector_id.notna() & (b.marca != "excluir_energia_binacional")]
    w = (asignado.assign(v=asignado.valor * asignado.peso).groupby(["hs4", "sector_id"]).v.sum().rename("v").reset_index()
         .merge(total, on="hs4"))
    w = w[w.total > 0].assign(w=lambda d: d.v / d.total)
    return w[["hs4", "sector_id", "w"]]


def exportaciones_sector(expo: pd.DataFrame, pesos: pd.DataFrame) -> pd.DataFrame:
    """Exportaciones por (anio, iso3, sector) como suma ponderada de las HS4, sin la energía binacional."""
    e = expo[expo.hs4 != HS4_ENERGIA].merge(pesos, on="hs4", how="inner")
    e["x"] = e.x * e.w
    return e.groupby(["anio", "iso3", "sector_id"], as_index=False).x.sum()


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--expo", default=str(MODELO / "exportaciones_hs4.parquet"))
    ap.add_argument("--salida", default=str(MODELO / "backtest_sector.csv"))
    args = ap.parse_args(argv)
    expo = pd.read_parquet(args.expo)
    pesos = pesos_hs4_sector(pd.read_csv(CLEAN / "puente_hs92_sector.csv", dtype=str))
    sec = exportaciones_sector(expo, pesos)
    mapeado = sec.x.sum() / expo[expo.hs4 != HS4_ENERGIA].x.sum()
    print(f"exportaciones mapeadas a sector: {100 * mapeado:.1f} % del comercio sin energía; {sec.sector_id.nunique()} sectores")
    df = construir_datos(sec.rename(columns={"sector_id": "hs4"}), pd.read_parquet(CLEAN / "dotaciones.parquet"), REQ_VACIO,
                         pd.read_csv(CLEAN / "poblacion_pais.csv"), revelados=True, solo_con_requisitos=False)
    bt.KS_PAIS = KS_SECTOR
    filas, difs = [], []
    for t in (v for v in VENTANAS if bt.ventanas_previas(v)):
        res = rv.evaluar(df, t)
        resm = rm.evaluar(df, t)
        pru = res["prueba"]
        print(f"\n=== prueba {t}→{t + 5}: {len(pru):,} filas, {int(pru.E.sum())} entradas ({100 * pru.E.mean():.1f} %), "
              f"{pru.iso3.nunique()} países, {pru.hs4.nunique()} sectores")
        print("coeficientes de `reveladas` (entrenamiento):", res["coeficientes"])
        print("coeficientes de `mundlak_reveladas`:", resm["coeficientes"]["mundlak_reveladas"])
        res["puntajes"].update({k: v for k, v in resm["puntajes"].items() if k.startswith("mundlak")})
        r = bt.resumen_ventana(res, t)
        filas += r
        print(pd.DataFrame(r)[["modelo", "tasa_base", "auc_pr", "p_pais_3", "p_pais_5"]].round(3).to_string(index=False))
        for modelo, base in [("reveladas", "densidad_sola"), ("reveladas", "solo_ingreso"), ("mundlak_reveladas", "mundlak_densidad"),
                             ("mundlak_reveladas", "densidad_sola")]:
            d = pd.DataFrame(bt.comparar_con_densidad_sola(res, (modelo,), base)).assign(ventana=t, contra=base)
            difs.append(d)
            x = d.set_index("metrica")
            print(f"  {modelo} − {base}: p@5 {x.loc['p_pais_5', 'dif']:+.3f} ({x.loc['p_pais_5', 'ic_inf']:+.3f}; "
                  f"{x.loc['p_pais_5', 'ic_sup']:+.3f}) | AUC-PR {x.loc['auc_pr', 'dif']:+.3f} ({x.loc['auc_pr', 'ic_inf']:+.3f}; "
                  f"{x.loc['auc_pr', 'ic_sup']:+.3f})")
    pd.DataFrame(filas).to_csv(args.salida, index=False)
    pd.concat(difs).to_csv(str(args.salida).replace(".csv", "_diferencias.csv"), index=False)
    print(f"\n-> {args.salida}")


if __name__ == "__main__":
    main()
