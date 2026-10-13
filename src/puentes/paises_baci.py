"""Puente de países: código numérico de BACI -> ISO3 (y nombre).

Las tablas de comercio (BACI) identifican al país con un código numérico (Paraguay = 600); las dotaciones y WDI,
con ISO3 (PRY). Este puente permite unirlas. Tres ISO3 tienen dos códigos BACI (entidades históricas): Bélgica
(56 y 58, Bélgica-Luxemburgo hasta 1998), Alemania (276 y 280, RFA hasta 1990) y Sudán (729 y 736, hasta 2011).
La unión código -> ISO3 es única; ISO3 -> código no, así que se une siempre desde el comercio.

Salida: data/clean/puente_paises_baci.csv. Uso: `uv run python -m src.puentes.paises_baci`.
"""
from __future__ import annotations

import zipfile
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
BACI = RAIZ / "data" / "raw" / "baci"
ZIP = BACI / "BACI_HS92_V202601.zip"
CSV = BACI / "country_codes_V202601.csv"
SALIDA = RAIZ / "data" / "clean" / "puente_paises_baci.csv"
ARCHIVO = "country_codes_V202601.csv"


def leer_codigos(zip_ruta: Path = ZIP, csv_ruta: Path = CSV) -> pd.DataFrame:
    """Lee el catálogo de países de BACI desde el CSV suelto o, si no está, desde el zip."""
    if csv_ruta.exists():
        return pd.read_csv(csv_ruta)
    with zipfile.ZipFile(zip_ruta) as z, z.open(ARCHIVO) as f:
        return pd.read_csv(f)


def construir(codigos: pd.DataFrame) -> pd.DataFrame:
    """Devuelve codigo_baci, iso3, nombre, historico (el ISO3 tiene otro código vigente)."""
    d = codigos.dropna(subset=["country_iso3"]).rename(
        columns={"country_code": "codigo_baci", "country_iso3": "iso3", "country_name": "nombre"})
    d = d[["codigo_baci", "iso3", "nombre"]].astype({"codigo_baci": int})
    d["historico"] = d.nombre.str.contains(r"\(\.\.\.\d{4}\)")
    if d.codigo_baci.duplicated().any():
        raise ValueError("códigos BACI repetidos")
    return d.sort_values("codigo_baci").reset_index(drop=True)


def main() -> None:
    out = construir(leer_codigos())
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(SALIDA, index=False)
    print(f"{len(out)} códigos, {out.iso3.nunique()} ISO3 -> {SALIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
