"""
Panel de entradas (D7, D8).

Variable dependiente: E_cp = 1[RCA_cpt < 0.5 ∧ RCA_cp,t+h >= 1], h = 5 y 10.

Uso:
    python -m src.modelos.panel
"""

import duckdb

DB_PATH = r"C:\ever\complejidad\econofold.duckdb"
HORIZONTES = [5, 10]
VENTANAS = [(2000, 2005), (2005, 2010), (2010, 2015), (2015, 2020)]
MIN_POBLACION = 1_000_000
MIN_EXPORT = 1_000_000_000  # 1.000 millones USD


def main() -> None:
    con = duckdb.connect(DB_PATH)
    con.execute("SET memory_limit='4GB';")
    con.execute("SET temp_directory='C:/ever/complejidad/duckdb_temp';")

    print("=== 1. Exportaciones totales por país-año (para D8) ===")
    con.execute("""
        CREATE OR REPLACE TABLE exports_total AS
        SELECT t AS year, i AS country, SUM(v) AS total_export
        FROM baci_global
        GROUP BY t, i
    """)

    print("=== 2. Panel de entradas ===")
    for t0, t1 in VENTANAS:
        for h in HORIZONTES:
            tabla = f"panel_{t0}_{t0 + h}"
            con.execute(f"""
                CREATE OR REPLACE TABLE {tabla} AS
                WITH inicio AS (
                    SELECT country, product, rca
                    FROM rca_depurado
                    WHERE year = {t0} AND rca < 0.5
                ),
                fin AS (
                    SELECT country, product, rca
                    FROM rca_depurado
                    WHERE year = {t0 + h} AND rca >= 1
                )
                SELECT
                    i.country,
                    i.product,
                    i.rca AS rca_inicio,
                    COALESCE(f.rca, 0.0) AS rca_fin,
                    CASE WHEN f.rca IS NOT NULL THEN 1 ELSE 0 END AS E
                FROM inicio i
                LEFT JOIN fin f
                  ON i.country = f.country AND i.product = f.product
            """)
            n = con.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]
            positivos = con.execute(f"SELECT SUM(E) FROM {tabla}").fetchone()[0]
            print(f"  {tabla}: {n:,} filas, {positivos:,} entradas ({100*positivos/n:.2f}%)")

    print("\n✓ Panel de entradas construido")
    con.close()


if __name__ == "__main__":
    main()