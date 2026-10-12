"""
Depuración del comercio (D6).

- Excluye HS 271600 (energía Itaipú/Yacyretá).
- Marca reexportaciones: productos donde import_value > 0.5 * export_value.

Uso:
    python -m src.modelos.depurar
"""

import duckdb

DB_PATH = r"C:\ever\complejidad\econofold.duckdb"
PARAGUAY_CODE = 600
HS_ITAIPU = '271600'
UMBRAL_REEXPORT = 0.5


def main() -> None:
    con = duckdb.connect(DB_PATH)
    con.execute("SET memory_limit='4GB';")
    con.execute("SET temp_directory='C:/ever/complejidad/duckdb_temp';")

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

    print("=== 3. RCA depurado ===")
    con.execute(f"""
        CREATE OR REPLACE TABLE rca_depurado AS
        SELECT r.*
        FROM rca_matrix r
        LEFT JOIN reexportaciones_py rx
          ON r.year = rx.year AND r.product = rx.product
        WHERE r.product != '{HS_ITAIPU}'
          AND COALESCE(rx.es_reexportacion, 0) = 0
    """)

    n_orig = con.execute("SELECT COUNT(*) FROM rca_matrix").fetchone()[0]
    n_dep = con.execute("SELECT COUNT(*) FROM rca_depurado").fetchone()[0]
    n_reexp = con.execute(
        "SELECT COUNT(*) FROM reexportaciones_py WHERE es_reexportacion = 1"
    ).fetchone()[0]

    print(f"\nRCA original: {n_orig:,}")
    print(f"RCA depurado: {n_dep:,}")
    print(f"Reexportaciones marcadas: {n_reexp:,}")

    con.close()


if __name__ == "__main__":
    main()