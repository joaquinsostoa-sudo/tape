"""
Presencia sostenida por ventana (D7 - presencia para φ y densidad).

DECISION (2026-10-12, Ever):
  Presencia = RCA >= 1 en al menos 2 de los 3 anios que terminan en t,
  para algun anio t dentro de la ventana.

Razon:
  - Consistente con D7 (variante de robustez).
  - Cumple la regla 4 de CLAUDE.md (entradas sostenidas).
  - Robusto a picos de un solo anio (BACI trae ruido).
  - Menos exigente que "3 de 3", mas exigente que "RCA puntual".

Alternativa descartada: promedio movil de 3 anios (32% persistencia, deja
pasar rachas de un solo anio). Diferencia medida por Joaquin con datos
reales (ventana 2010-2015): 2-de-3 da 13.277 entradas con 47% persistencia;
promedio movil da 24.776 con 32%.

Lee de `rca_depurado` (no de `rca_matrix`): el RCA ya viene sin energia
de Itaipu/Yacyreti y sin reexportaciones.

Uso:
    python -m src.modelos.presencia --db RUTA
"""

import argparse

import duckdb

VENTANAS = [(1995, 1999), (2000, 2004), (2005, 2009),
            (2010, 2014), (2015, 2019), (2020, 2024)]

# Parametros de la decision
ANIOS_VENTANA = 3       # cuantos anios mira hacia atras
MIN_ANIOS_OK = 2        # cuantos de esos 3 tienen que cumplir RCA >= 1


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

    print(f"=== 1. RCA persistente: >= {MIN_ANIOS_OK} de {ANIOS_VENTANA} anios con RCA >= 1 ===")
    # Para cada (country, product, year), mirar los ultimos 3 anios
    # (incluyendo el actual) y contar cuantos tienen RCA >= 1.
    con.execute(f"""
        CREATE OR REPLACE TABLE rca_persistente AS
        SELECT
            year,
            country,
            product,
            rca,
            SUM(CASE WHEN rca >= 1 THEN 1 ELSE 0 END) OVER (
                PARTITION BY country, product
                ORDER BY year
                ROWS BETWEEN {ANIOS_VENTANA - 1} PRECEDING AND CURRENT ROW
            ) AS anios_ok,
            COUNT(*) OVER (
                PARTITION BY country, product
                ORDER BY year
                ROWS BETWEEN {ANIOS_VENTANA - 1} PRECEDING AND CURRENT ROW
            ) AS anios_disponibles
        FROM rca_depurado
    """)

    n_persist = con.execute(
        f"SELECT COUNT(*) FROM rca_persistente WHERE anios_ok >= {MIN_ANIOS_OK}"
    ).fetchone()[0]
    print(f"  Pares (country, product, year) con persistencia: {n_persist:,}")

    print("\n=== 2. Presencia por ventana (al menos un anio t en la ventana) ===")
    for ini, fin in VENTANAS:
        tabla = f"presencia_{ini}_{fin}"
        con.execute(f"""
            CREATE OR REPLACE TABLE {tabla} AS
            SELECT DISTINCT
                country,
                product,
                1 AS has_rca
            FROM rca_persistente
            WHERE year BETWEEN {ini} AND {fin}
              AND anios_ok >= {MIN_ANIOS_OK}
        """)
        n = con.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]
        print(f"  {tabla}: {n:,} pares pais-producto")

    print("\nOK Presencia sostenida calculada")
    con.close()


if __name__ == "__main__":
    main()