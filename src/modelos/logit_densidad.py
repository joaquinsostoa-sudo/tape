"""
Modelo base: logit con densidad sola (1.8).

Pr(E=1) = Λ(α_ct + γ_pt + β · d_cpt)

Uso:
    python -m src.modelos.logit_densidad
"""

import duckdb
import statsmodels.formula.api as smf

DB_PATH = r"C:\ever\complejidad\econofold.duckdb"
TABLA_PANEL = "panel_2005_2010"  # podés parametrizar
TABLA_DENSIDAD = "densidad_2000_2004"


def main() -> None:
    con = duckdb.connect(DB_PATH)

    print(f"=== Cargando panel {TABLA_PANEL} ===")
    df = con.execute(f"""
        SELECT p.country, p.product, p.rca_inicio, p.E,
               d.densidad
        FROM {TABLA_PANEL} p
        LEFT JOIN {TABLA_DENSIDAD} d
          ON p.country = d.country AND p.product = d.product
        WHERE d.densidad IS NOT NULL
    """).fetchdf()

    print(f"  {len(df):,} filas")
    print(f"  Entradas: {df['E'].sum():,} ({100 * df['E'].mean():.2f}%)")

    # Estandarizar densidad
    df["densidad_z"] = (df["densidad"] - df["densidad"].mean()) / df["densidad"].std()

    print("\n=== Estimando logit ===")
    modelo = smf.logit(
        "E ~ densidad_z + C(country) + C(product)",
        data=df,
    ).fit(disp=False, maxiter=100)

    print(modelo.summary())

    # Predicciones
    df["prob"] = modelo.predict(df)

    # Guardar
    con.execute("CREATE OR REPLACE TABLE predicciones_base AS SELECT * FROM df")
    print("\n✓ Predicciones guardadas en predicciones_base")

    con.close()


if __name__ == "__main__":
    main()