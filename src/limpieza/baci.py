"""Limpieza de BACI (tarea 1.1): del zip de CEPII a exportaciones e importaciones por país, producto HS6 y año.

BACI trae un CSV por año con una fila por exportador-importador-producto (`t, i, j, k, v, q`: año, exportador, importador, producto HS6 sin ceros a la izquierda, valor en miles de USD,
cantidad en toneladas, a veces «NA»). Cada año se extrae a una carpeta temporal propia, se agrega con DuckDB y se borra, así que nunca hay más de un CSV (≈ 360 MB) en disco.

Salidas en `data/clean/` (ignoradas por git):
- `comercio_exportaciones_hs6.parquet`: `anio, codigo_baci, hs6, valor_miles_usd, toneladas`.
- `comercio_importaciones_hs6.parquet`: lo mismo por país importador (para marcar reexportaciones, D6).
No se excluye nada aquí (la energía HS 2716 y las reexportaciones se tratan en la depuración, tarea 1.2): esta capa solo reproduce BACI.
`exportaciones_hs4(...)` arma la tabla que usan los modelos (`anio, iso3, hs4, x`) y se escribe en `data/model/exportaciones_hs4.parquet`.

Comprobaciones (`verificar`): sin valores negativos; los totales exportados e importados de cada año coinciden (BACI está conciliado); todo exportador e importador está en el catálogo de países;
hs6 de 6 dígitos; sin duplicados por clave.

Uso: uv run python -m src.limpieza.baci
"""
from __future__ import annotations

import re
import shutil
import zipfile
from pathlib import Path

import duckdb
import pandas as pd

from src.puentes.paises_baci import leer_codigos

RAIZ = Path(__file__).resolve().parents[2]
ZIP = RAIZ / "data" / "raw" / "baci" / "BACI_HS92_V202601.zip"
CLEAN = RAIZ / "data" / "clean"
TMP = CLEAN / "_baci_tmp"
SALIDA_EXPO = CLEAN / "comercio_exportaciones_hs6.parquet"
SALIDA_IMPO = CLEAN / "comercio_importaciones_hs6.parquet"
PATRON = re.compile(r"BACI_HS92_Y(\d{4})_V\d+\.csv$")


def miembros_por_anio(nombres: list[str]) -> dict[int, str]:
    """Archivos anuales del zip: {año: nombre}."""
    out = {}
    for n in nombres:
        m = PATRON.search(n)
        if m:
            out[int(m.group(1))] = n
    return dict(sorted(out.items()))


def agregar_csv(ruta: Path, con: duckdb.DuckDBPyConnection | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Exportaciones (por exportador y producto) e importaciones (por importador y producto) de un CSV anual de BACI."""
    con = con or duckdb.connect()
    base = f"""read_csv('{ruta.as_posix()}', header=true, columns={{'t': 'INTEGER', 'i': 'INTEGER', 'j': 'INTEGER', 'k': 'VARCHAR', 'v': 'DOUBLE', 'q': 'VARCHAR'}})"""
    expo = con.execute(f"""SELECT t AS anio, i AS codigo_baci, lpad(k, 6, '0') AS hs6, SUM(v) AS valor_miles_usd, SUM(TRY_CAST(q AS DOUBLE)) AS toneladas
                           FROM {base} GROUP BY 1, 2, 3""").df()
    impo = con.execute(f"""SELECT t AS anio, j AS codigo_baci, lpad(k, 6, '0') AS hs6, SUM(v) AS valor_miles_usd, SUM(TRY_CAST(q AS DOUBLE)) AS toneladas
                           FROM {base} GROUP BY 1, 2, 3""").df()
    return expo, impo


def procesar_zip(zip_ruta: Path = ZIP, tmp: Path = TMP, anios: list[int] | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Agrega todos los años del zip (o los de `anios`) sin dejar más de un CSV extraído a la vez."""
    expos, impos = [], []
    con = duckdb.connect()
    tmp.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(zip_ruta) as z:
            for anio, nombre in miembros_por_anio(z.namelist()).items():
                if anios and anio not in anios:
                    continue
                destino = tmp / Path(nombre).name
                with z.open(nombre) as origen, open(destino, "wb") as f:
                    shutil.copyfileobj(origen, f, length=1 << 20)
                e, i = agregar_csv(destino, con)
                destino.unlink()
                expos.append(e)
                impos.append(i)
                print(f"  {anio}: {len(e):,} filas de exportación, {len(i):,} de importación")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return pd.concat(expos, ignore_index=True), pd.concat(impos, ignore_index=True)


def verificar(expo: pd.DataFrame, impo: pd.DataFrame, codigos: set[int], tol: float = 1e-6) -> dict[str, int]:
    """Cuenta de problemas por comprobación (todo en 0 = sin problemas)."""
    cat = set(codigos)
    tot_e, tot_i = expo.groupby("anio").valor_miles_usd.sum(), impo.groupby("anio").valor_miles_usd.sum()
    return {
        "valores_negativos": int((expo.valor_miles_usd < 0).sum() + (impo.valor_miles_usd < 0).sum()),
        "anios_con_totales_distintos": int(((tot_e - tot_i).abs() / tot_e > tol).sum()),
        "paises_fuera_del_catalogo": int((~expo.codigo_baci.isin(cat)).sum() + (~impo.codigo_baci.isin(cat)).sum()),
        "hs6_mal_formado": int((expo.hs6.str.len() != 6).sum() + (impo.hs6.str.len() != 6).sum()),
        "claves_duplicadas": int(expo.duplicated(["anio", "codigo_baci", "hs6"]).sum() + impo.duplicated(["anio", "codigo_baci", "hs6"]).sum()),
    }


def exportaciones_hs4(expo: pd.DataFrame, puente: pd.DataFrame) -> pd.DataFrame:
    """Exportaciones por año, país (ISO3) y producto HS4, en miles de USD (`x`); los códigos sin ISO3 se descartan, como en el panel de los modelos."""
    e = expo.assign(hs4=expo.hs6.str[:4]).merge(puente[["codigo_baci", "iso3"]], on="codigo_baci", how="inner")
    return e.groupby(["anio", "iso3", "hs4"], as_index=False).valor_miles_usd.sum().rename(columns={"valor_miles_usd": "x"})


def comparar(nuevo: pd.DataFrame, viejo: pd.DataFrame) -> dict[str, float]:
    """Compara dos tablas `anio, iso3, hs4, x`: filas de cada una, claves solo en una y la mayor diferencia relativa de x en las comunes."""
    k = ["anio", "iso3", "hs4"]
    m = nuevo.merge(viejo, on=k, how="outer", suffixes=("_nuevo", "_viejo"), indicator=True)
    comunes = m[m._merge == "both"]
    dif = ((comunes.x_nuevo - comunes.x_viejo).abs() / comunes.x_viejo.clip(lower=1e-9))
    return {"filas_nuevo": len(nuevo), "filas_viejo": len(viejo), "solo_nuevo": int((m._merge == "left_only").sum()), "solo_viejo": int((m._merge == "right_only").sum()),
            "dif_relativa_max": float(dif.max()) if len(dif) else float("nan"), "filas_con_dif_mayor_1e6": int((dif > 1e-6).sum())}


def main() -> None:
    import sys

    sys.stdout.reconfigure(encoding="utf-8")
    puente = pd.read_csv(CLEAN / "puente_paises_baci.csv")
    catalogo = set(leer_codigos().country_code)  # todos los códigos de BACI, incluso los que no tienen ISO3
    print("Procesando el zip de BACI (un CSV anual por vez)...")
    expo, impo = procesar_zip()
    expo.to_parquet(SALIDA_EXPO, index=False)
    impo.to_parquet(SALIDA_IMPO, index=False)
    print(f"\n{len(expo):,} filas de exportación y {len(impo):,} de importación; años {expo.anio.min()}-{expo.anio.max()}")
    print("verificación:", verificar(expo, impo, catalogo))
    hs4 = exportaciones_hs4(expo, puente)
    ruta = RAIZ / "data" / "model" / "exportaciones_hs4.parquet"
    if ruta.exists():
        print("comparación con data/model/exportaciones_hs4.parquet (del panel de Ever):", comparar(hs4, pd.read_parquet(ruta)))
    hs4.to_parquet(ruta, index=False)  # tabla canónica de los modelos, ahora reproducible desde el zip de CEPII


if __name__ == "__main__":
    main()
