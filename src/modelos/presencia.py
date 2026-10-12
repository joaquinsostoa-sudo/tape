"""
Presencia sostenida por ventana de 5 años (D7).

Reemplaza rca_binary (que usa un solo año) por una definición robusta:
un producto está presente si el RCA promedio móvil de 3 años es >= 1
en al menos un año de la ventana.

Uso:
    python -m src.modelos.presencia
"""

from pathlib import Path
import duckdb

DB_PATH = r"C:\ever\complejidad\econofold.duckdb"
VENTANAS = [(1995, 1999), (2000, 2004), (2005, 2009), (2010, 2014),
            (2015, 2019), (2020, 2024)]


def main() -> None:
    con = duckdb.connect(DB_PATH)
    con.execute("SET memory_limit='4GB';")
    con.execute("SET temp_directory='C:/ever/complejidad/duckdb_temp';")

    print("=== 1. RCA promedio móvil de 3 años ===")
    con.execute("""
        CREATE OR REPLACE TABLE rca_movil AS
        SELECT
            year,
            country,
            product,
            AVG(rca) OVER (
                PARTITION BY country, product
                ORDER BY year
                ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
            ) AS rca_ma3
        FROM rca_matrix
    """)

    print("=== 2. Presencia sostenida por ventana ===")
    for ini, fin in VENTANAS:
        tabla = f"presencia_{ini}_{fin}"
        con.execute(f"""
            CREATE OR REPLACE TABLE {tabla} AS
            SELECT DISTINCT
                country,
                product,
                1 AS has_rca
            FROM rca_movil
            WHERE year BETWEEN {ini} AND {fin}
              AND rca_ma3 >= 1
        """)
        n = con.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]
        print(f"  {tabla}: {n:,} pares país-producto")

    print("✓ Presencia sostenida calculada")
    con.close()


if __name__ == "__main__":
    main()