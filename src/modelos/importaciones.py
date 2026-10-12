"""
Importaciones de Paraguay por año y producto (para D6).

Uso:
    python -m src.modelos.importaciones
"""

import duckdb

DB_PATH = r"C:\ever\complejidad\econofold.duckdb"
PARAGUAY_CODE = 600


def main() -> None:
    con = duckdb.connect(DB_PATH)
    con.execute("SET memory_limit='4GB';")

    print("=== Importaciones Paraguay por año-producto ===")
    con.execute(f"""
        CREATE OR REPLACE TABLE importaciones_py AS
        SELECT
            t AS year,
            k AS product,
            SUM(v) AS import_value
        FROM baci_global
        WHERE j = {PARAGUAY_CODE}
        GROUP BY t, k
    """)

    n = con.execute("SELECT COUNT(*) FROM importaciones_py").fetchone()[0]
    print(f"  {n:,} filas año-producto")

    print("\nEjemplo 2024 (top 10):")
    df = con.execute("""
        SELECT product, import_value
        FROM importaciones_py
        WHERE year = 2024
        ORDER BY import_value DESC
        LIMIT 10
    """).fetchdf()
    print(df.to_string())

    con.close()


if __name__ == "__main__":
    main()