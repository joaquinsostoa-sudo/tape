"""
Panel de entradas (D7, D8).

D7 - Entrada principal: E = 1[RCA_t < 0.5 AND RCA_t+h >= 1], un solo anio.
     Variante de robustez: RCA >= 1 en al menos 2 de los 3 anios que terminan en t+h.

D8 - Muestra de paises: poblacion >= 1M Y exportaciones >= USD 1.000 millones
     en el anio inicial de cada ventana.

NOTA: BACI trae `v` en MILES de USD. MIN_EXPORT = 1_000_000 (miles) = 1.000
millones USD reales.

Uso:
    python -m src.modelos.panel --db RUTA
"""

import argparse
from pathlib import Path

import duckdb

HORIZONTES = [5, 10]
VENTANAS = [(2000, 2005), (2005, 2010), (2010, 2015), (2015, 2020)]
MIN_POBLACION = 1_000_000
MIN_EXPORT = 1_000_000  # miles de USD = 1.000 millones USD
DOTACIONES = Path("data/clean/dotaciones.parquet")


def cargar_poblacion(con) -> bool:
    if not DOTACIONES.exists():
        return False
    con.execute(f"""
        CREATE OR REPLACE TABLE poblacion_pais AS
        SELECT country, year, poblacion
        FROM read_parquet('{DOTACIONES.as_posix()}')
        WHERE poblacion IS NOT NULL
    """)
    n = con.execute("SELECT COUNT(*) FROM poblacion_pais").fetchone()[0]
    print(f"  Poblacion cargada: {n:,} filas")
    return True


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--temp", default=None)
    args = ap.parse_args()

    con = duckdb.connect(args.db)
    con.execute("SET memory_limit='4GB';")
    con.execute("SET preserve_insertion_order=false;")
    if args.temp:
        con.execute(f"SET temp_directory='{args.temp}';")

    print("=== 1. Exportaciones totales por pais-anio ===")
    con.execute("""
        CREATE OR REPLACE TABLE exports_total AS
        SELECT t AS year, i AS country, SUM(v) AS total_export
        FROM baci_global
        GROUP BY t, i
    """)
    sample = con.execute(
        "SELECT year, country, total_export FROM exports_total WHERE year = 2015 ORDER BY total_export DESC LIMIT 3"
    ).fetchall()
    print(f"  Top 2015 (miles USD): {sample}")

    print("=== 2. Poblacion por pais-anio ===")
    tiene_pob = cargar_poblacion(con)
    if not tiene_pob:
        print("  AVISO: no existe data/clean/dotaciones.parquet")
        print("  Filtro de poblacion omitido. Solo MIN_EXPORT.")

    print("=== 3. Paises elegibles por ventana (D8) ===")
    anios_inicio = sorted(set(t0 for t0, _ in VENTANAS))

    con.execute(f"""
        CREATE OR REPLACE TABLE paises_elegibles AS
        SELECT year, country, total_export
        FROM exports_total
        WHERE year IN ({','.join(map(str, anios_inicio))})
          AND total_export >= {MIN_EXPORT}
    """)

    if tiene_pob:
        con.execute(f"""
            CREATE OR REPLACE TABLE paises_elegibles AS
            SELECT e.year, e.country, e.total_export, p.poblacion
            FROM paises_elegibles e
            LEFT JOIN poblacion_pais p
              ON e.year = p.year AND e.country = p.country
            WHERE e.total_export >= {MIN_EXPORT}
              AND (p.poblacion IS NULL OR p.poblacion >= {MIN_POBLACION})
        """)
        print(f"  Filtros: export >= {MIN_EXPORT:,} (miles USD) Y (pob >= {MIN_POBLACION:,} O sin dato)")
    else:
        print(f"  Filtro: solo export >= {MIN_EXPORT:,} (miles USD)")

    for t0 in anios_inicio:
        n = con.execute(
            f"SELECT COUNT(DISTINCT country) FROM paises_elegibles WHERE year = {t0}"
        ).fetchone()[0]
        print(f"    {t0}: {n} paises")

    print("=== 4. Panel de entradas (D7: un solo anio) ===")
    for t0, _ in VENTANAS:
        for h in HORIZONTES:
            t1 = t0 + h
            tabla = f"panel_{t0}_{t1}"
            con.execute(f"""
                CREATE OR REPLACE TABLE {tabla} AS
                WITH inicio AS (
                    SELECT r.country, r.product, r.rca AS rca_t
                    FROM rca_depurado r
                    JOIN paises_elegibles pe
                      ON r.country = pe.country AND pe.year = {t0}
                    WHERE r.year = {t0} AND r.rca < 0.5
                ),
                fin AS (
                    SELECT country, product, rca AS rca_th
                    FROM rca_depurado
                    WHERE year = {t1} AND rca >= 1
                )
                SELECT
                    i.country, i.product,
                    i.rca_t AS rca_inicio,
                    COALESCE(f.rca_th, 0.0) AS rca_fin,
                    CASE WHEN f.rca_th IS NOT NULL THEN 1 ELSE 0 END AS E
                FROM inicio i
                LEFT JOIN fin f ON i.country = f.country AND i.product = f.product
            """)
            n = con.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]
            if n > 0:
                pos = con.execute(f"SELECT SUM(E) FROM {tabla}").fetchone()[0]
                print(f"  {tabla}: {n:,} filas, {pos:,} entradas ({100*pos/n:.2f}%)")
            else:
                print(f"  {tabla}: sin filas")

    print("=== 5. Variante robusta (2 de 3 anios con RCA >= 1) ===")
    for t0, _ in VENTANAS:
        for h in HORIZONTES:
            t1 = t0 + h
            tabla = f"panel_robusto_{t0}_{t1}"
            con.execute(f"""
                CREATE OR REPLACE TABLE {tabla} AS
                WITH inicio AS (
                    SELECT r.country, r.product, r.rca AS rca_t
                    FROM rca_depurado r
                    JOIN paises_elegibles pe
                      ON r.country = pe.country AND pe.year = {t0}
                    WHERE r.year = {t0} AND r.rca < 0.5
                ),
                fin AS (
                    SELECT country, product,
                           SUM(CASE WHEN rca >= 1 THEN 1 ELSE 0 END) AS anios_ok
                    FROM rca_depurado
                    WHERE year BETWEEN {t1 - 2} AND {t1}
                    GROUP BY country, product
                    HAVING SUM(CASE WHEN rca >= 1 THEN 1 ELSE 0 END) >= 2
                )
                SELECT
                    i.country, i.product,
                    i.rca_t AS rca_inicio,
                    CASE WHEN f.anios_ok IS NOT NULL THEN 1 ELSE 0 END AS E
                FROM inicio i
                LEFT JOIN fin f ON i.country = f.country AND i.product = f.product
            """)
            n = con.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]
            if n > 0:
                pos = con.execute(f"SELECT SUM(E) FROM {tabla}").fetchone()[0]
                print(f"  {tabla}: {n:,} filas, {pos:,} entradas ({100*pos/n:.2f}%)")

    print("\nOK Panel de entradas construido")
    con.close()


if __name__ == "__main__":
    main()