"""
Backtest del modelo base (1.11).

Entrena con ventana t0, predice t0+h, mide precision@k.

Uso:
    python -m src.modelos.backtest
"""

import duckdb
import numpy as np
import statsmodels.formula.api as smf

from src.modelos.evaluacion import precision_at_k, auc_pr

DB_PATH = r"C:\ever\complejidad\econofold.duckdb"
VENTANAS = [
    (2000, 2005, "densidad_1995_1999"),
    (2005, 2010, "densidad_2000_2004"),
    (2010, 2015, "densidad_2005_2009"),
    (2015, 2020, "densidad_2010_2014"),
]


def main() -> None:
    con = duckdb.connect(DB_PATH)
    resultados = []

    for t0, t1, tabla_dens in VENTANAS:
        print(f"\n=== Ventana {t0} → {t1} ===")
        df = con.execute(f"""
            SELECT p.country, p.product, p.E, d.densidad
            FROM panel_{t0}_{t1} p
            LEFT JOIN {tabla_dens} d
              ON p.country = d.country AND p.product = d.product
            WHERE d.densidad IS NOT NULL
        """).fetchdf()

        df["densidad_z"] = (df["densidad"] - df["densidad"].mean()) / df["densidad"].std()

        modelo = smf.logit(
            "E ~ densidad_z + C(country) + C(product)",
            data=df,
        ).fit(disp=False, maxiter=100)

        df["prob"] = modelo.predict(df)

        p20 = precision_at_k(df["E"].values, df["prob"].values, k=20)
        p50 = precision_at_k(df["E"].values, df["prob"].values, k=50)
        p100 = precision_at_k(df["E"].values, df["prob"].values, k=100)
        ap = auc_pr(df["E"].values, df["prob"].values)

        print(f"  precision@20 = {p20:.4f}")
        print(f"  precision@50 = {p50:.4f}")
        print(f"  precision@100 = {p100:.4f}")
        print(f"  AUC-PR = {ap:.4f}")

        resultados.append({
            "ventana": f"{t0}-{t1}",
            "precision_20": p20,
            "precision_50": p50,
            "precision_100": p100,
            "auc_pr": ap,
            "n": len(df),
            "positivos": int(df["E"].sum()),
        })

    print("\n=== Resumen ===")
    for r in resultados:
        print(f"  {r['ventana']}: p@20={r['precision_20']:.3f}, "
              f"p@50={r['precision_50']:.3f}, AUC-PR={r['auc_pr']:.3f}")

    con.close()


if __name__ == "__main__":
    main()