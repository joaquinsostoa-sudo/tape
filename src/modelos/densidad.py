"""
Proximidad (φ) por ventana y densidad (D3).
Versión con debug paso a paso.
"""

import sys
import traceback

import duckdb

DB_PATH = r"C:\ever\tape\db\econofold.duckdb"
VENTANAS = [(1995, 1999), (2000, 2004), (2005, 2009), (2010, 2014),
            (2015, 2019), (2020, 2024)]
UMBRAL_BOTH = 5


def calcular_phi(con, ini, fin):
    tabla_pres = f"presencia_{ini}_{fin}"
    tabla_phi = f"phi_{ini}_{fin}"

    print(f"  Calculando {tabla_phi}...")
    sys.stdout.flush()

    n_pres = con.execute(f"SELECT COUNT(*) FROM {tabla_pres}").fetchone()[0]
    print(f"    {tabla_pres}: {n_pres:,} filas")

    con.execute(f"""
        CREATE OR REPLACE TABLE {tabla_phi} AS
        WITH totales AS (
            SELECT product, COUNT(*) AS p_total
            FROM {tabla_pres}
            GROUP BY product
        ),
        pares AS (
            SELECT a.product AS p1, b.product AS p2, COUNT(*) AS both_have
            FROM {tabla_pres} a
            JOIN {tabla_pres} b
              ON a.country = b.country AND a.product < b.product
            GROUP BY a.product, b.product
            HAVING COUNT(*) >= {UMBRAL_BOTH}
        )
        SELECT
            p.p1, p.p2, p.both_have,
            LEAST(CAST(p.both_have AS DOUBLE) / t1.p_total,
                  CAST(p.both_have AS DOUBLE) / t2.p_total) AS proximity
        FROM pares p
        JOIN totales t1 ON p.p1 = t1.product
        JOIN totales t2 ON p.p2 = t2.product

        UNION ALL

        SELECT
            p.p2 AS p1, p.p1 AS p2, p.both_have,
            LEAST(CAST(p.both_have AS DOUBLE) / t1.p_total,
                  CAST(p.both_have AS DOUBLE) / t2.p_total) AS proximity
        FROM pares p
        JOIN totales t1 ON p.p1 = t1.product
        JOIN totales t2 ON p.p2 = t2.product
    """)

    n = con.execute(f"SELECT COUNT(*) FROM {tabla_phi}").fetchone()[0]
    print(f"    OK {tabla_phi}: {n:,} pares simetrizados")


def calcular_densidad(con, ini, fin):
    tabla_pres = f"presencia_{ini}_{fin}"
    tabla_phi = f"phi_{ini}_{fin}"
    tabla_dens = f"densidad_{ini}_{fin}"

    print(f"  Calculando {tabla_dens}...")

    con.execute(f"""
        CREATE OR REPLACE TABLE {tabla_dens} AS
        WITH base AS (
            SELECT DISTINCT country, product FROM rca_matrix WHERE year = {fin}
        ),
        phi_agg AS (
            SELECT p1 AS product, SUM(proximity) AS suma_phi
            FROM {tabla_phi}
            GROUP BY p1
        ),
        dens AS (
            SELECT
                b.country,
                b.product,
                COALESCE(
                    SUM(phi.proximity * COALESCE(pres.has_rca, 0))
                    / NULLIF(MAX(pa.suma_phi), 0),
                    0.0
                ) AS densidad
            FROM base b
            LEFT JOIN {tabla_phi} phi ON phi.p1 = b.product
            LEFT JOIN {tabla_pres} pres
              ON pres.country = b.country AND pres.product = phi.p2
            LEFT JOIN phi_agg pa ON pa.product = b.product
            GROUP BY b.country, b.product
        )
        SELECT country, product, densidad FROM dens
    """)

    n = con.execute(f"SELECT COUNT(*) FROM {tabla_dens}").fetchone()[0]
    print(f"    OK {tabla_dens}: {n:,} filas")


def main():
    print(f"Conectando a {DB_PATH}")
    con = duckdb.connect(DB_PATH)
    con.execute("SET memory_limit='4GB';")
    con.execute("SET temp_directory='C:/ever/tape/db/duckdb_temp';")

    for ini, fin in VENTANAS:
        print(f"\n=== Ventana {ini}-{fin} ===")
        try:
            calcular_phi(con, ini, fin)
            calcular_densidad(con, ini, fin)
        except Exception:
            print(f"  ERROR en ventana {ini}-{fin}:")
            traceback.print_exc()

    print("\nProceso terminado")
    con.close()


if __name__ == "__main__":
    main()