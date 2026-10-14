"""
Backtest del modelo base (1.11).

Usa LogitEfectosFijos (matrices dispersas) en lugar de statsmodels.

Uso:
    python -m src.modelos.backtest --db RUTA
"""

import argparse

import duckdb

from src.modelos.evaluacion import auc_pr, precision_at_k
from src.modelos.logit_disperso import LogitEfectosFijos

VENTANAS = [
    (2000, 2005, "densidad_1995_1999"),
    (2005, 2010, "densidad_2000_2004"),
    (2010, 2015, "densidad_2005_2009"),
    (2015, 2020, "densidad_2010_2014"),
]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True, help="ruta de la base DuckDB")
    args = ap.parse_args()

    con = duckdb.connect(args.db, read_only=True)
    resultados = []

    for t0, t1, tabla_dens in VENTANAS:
        print(f"\n=== Ventana {t0} -> {t1} ===")
        df = con.execute(f"""
            SELECT p.country, p.product, p.E, d.densidad
            FROM panel_{t0}_{t1} p
            LEFT JOIN {tabla_dens} d
              ON p.country = d.country AND p.product = d.product
            WHERE d.densidad IS NOT NULL
        """).fetchdf()

        if len(df) == 0:
            print("  (sin filas, se omite)")
            continue

        df["densidad_z"] = (df["densidad"] - df["densidad"].mean()) / df["densidad"].std()

        modelo = LogitEfectosFijos(
            columnas=["densidad_z"],
            efectos=["country", "product"],
            C=10,
        ).ajustar(df, "E")

        df["prob"] = modelo.predecir(df)

        p20 = precision_at_k(df["E"].values, df["prob"].values, k=20)
        p50 = precision_at_k(df["E"].values, df["prob"].values, k=50)
        p100 = precision_at_k(df["E"].values, df["prob"].values, k=100)
        ap = auc_pr(df["E"].values, df["prob"].values)

        print(f"  n = {len(df):,} filas, {int(df['E'].sum()):,} entradas")
        print(f"  precision@20  = {p20:.4f}")
        print(f"  precision@50  = {p50:.4f}")
        print(f"  precision@100 = {p100:.4f}")
        print(f"  AUC-PR        = {ap:.4f}")
        print(f"  coef densidad = {modelo.coeficientes['densidad_z']:.4f}")

        resultados.append({
            "ventana": f"{t0}-{t1}",
            "precision_20": p20,
            "precision_50": p50,
            "precision_100": p100,
            "auc_pr": ap,
            "n": len(df),
            "positivos": int(df["E"].sum()),
            "coef_densidad": modelo.coeficientes["densidad_z"],
        })

    print("\n=== Resumen ===")
    print(f"{'Ventana':<12} {'p@20':>8} {'p@50':>8} {'p@100':>8} {'AUC-PR':>8} {'coef_d':>8}")
    for r in resultados:
        print(f"{r['ventana']:<12} {r['precision_20']:>8.3f} "
              f"{r['precision_50']:>8.3f} {r['precision_100']:>8.3f} "
              f"{r['auc_pr']:>8.3f} {r['coef_densidad']:>8.3f}")

    con.close()


if __name__ == "__main__":
    main()