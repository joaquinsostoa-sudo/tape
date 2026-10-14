"""
Depuración del comercio (D6) + recálculo del RCA.

- Excluye HS 271600 (energía Itaipú/Yacyretá).
- Marca reexportaciones: import_value > 0.5 * export_value.
- Recalcula el RCA DESPUÉS de depurar. El RCA original tiene la energía
  en el denominador (23% de las exportaciones de Paraguay en 2015), lo que
  subestima el RCA de todos los demás productos.

Uso:
    python -m src.modelos.depurar --db RUTA
"""

import argparse

import duckdb

HS_ITAIPU = "271600"
PARAGUAY_CODE = 600
UMBRAL_REEXPORT = 0.5


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True, help="ruta de la base DuckDB")
    ap.add_argument("--temp", default=None, help="directorio temporal")
    args = ap.parse_args()

    con = duckdb.connect(args.db)
    con.execute("SET memory_limit='4GB';")
    con.execute("SET preserve_insertion_order=false;")
    if args.temp:
        con.execute(f"SET temp_directory='{args.temp}';")

    print("=== 1. Exportaciones Paraguay por año-producto ===")
    con.execute(f"""
        CREATE OR REPLACE TABLE exportaciones_py AS
        SELECT t AS year, k AS product, SUM(v) AS export_value
        FROM baci_global
        WHERE i = {PARAGUAY_CODE}
        GROUP BY t, k
    """)

    print("=== 2. Marcar reexportaciones ===")
    con.execute(f"""
        CREATE OR REPLACE TABLE reexportaciones_py AS
        SELECT
            e.year, e.product, e.export_value, i.import_value,
            (i.import_value / NULLIF(e.export_value, 0)) AS ratio_imp_exp,
            CASE WHEN i.import_value > {UMBRAL_REEXPORT} * e.export_value
                 THEN 1 ELSE 0 END AS es_reexportacion
        FROM exportaciones_py e
        JOIN importaciones_py i
          ON e.year = i.year AND e.product = i.product
    """)

    print("=== 3. Comercio depurado ===")
    con.execute(f"""
        CREATE OR REPLACE TABLE baci_depurado AS
        SELECT b.*
        FROM baci_global b
        WHERE b.k != '{HS_ITAIPU}'
          AND NOT (
              b.i = {PARAGUAY_CODE}
              AND EXISTS (
                  SELECT 1 FROM reexportaciones_py r
                  WHERE r.year = b.t
                    AND r.product = b.k
                    AND r.es_reexportacion = 1
              )
          )
    """)

    print("=== 4. RCA recalculado sobre el comercio depurado ===")
    con.execute("""
        CREATE OR REPLACE TABLE rca_depurado AS
        WITH total_pais_producto AS (
            SELECT t AS year, i AS country, k AS product, SUM(v) AS x_ik
            FROM baci_depurado
            GROUP BY t, i, k
        ),
        total_pais AS (
            SELECT t AS year, i AS country, SUM(v) AS x_i
            FROM baci_depurado
            GROUP BY t, i
        ),
        total_producto AS (
            SELECT t AS year, k AS product, SUM(v) AS x_k
            FROM baci_depurado
            GROUP BY t, k
        ),
        total_mundial AS (
            SELECT t AS year, SUM(v) AS x_world
            FROM baci_depurado
            GROUP BY t
        )
        SELECT
            tpp.year,
            tpp.country,
            tpp.product,
            tpp.x_ik,
            (tpp.x_ik / tp.x_i) / (tpr.x_k / tw.x_world) AS rca
        FROM total_pais_producto tpp
        JOIN total_pais tp ON tpp.year = tp.year AND tpp.country = tp.country
        JOIN total_producto tpr ON tpp.year = tpr.year AND tpp.product = tpr.product
        JOIN total_mundial tw ON tpp.year = tw.year
    """)

    n_orig = con.execute("SELECT COUNT(*) FROM rca_matrix").fetchone()[0]
    n_dep = con.execute("SELECT COUNT(*) FROM rca_depurado").fetchone()[0]
    n_reexp = con.execute(
        "SELECT COUNT(*) FROM reexportaciones_py WHERE es_reexportacion = 1"
    ).fetchone()[0]

    print(f"\nRCA original: {n_orig:,}")
    print(f"RCA depurado (recalculado): {n_dep:,}")
    print(f"Reexportaciones marcadas: {n_reexp:,}")
    print("\nOK Depuracion completa")

    con.close()


if __name__ == "__main__":
    main()