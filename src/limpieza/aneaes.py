"""Carreras de grado y programas de posgrado de la ANEAES, con la marca `acreditada`.

Fuente: data/raw/aneaes/*.xls (consultas exportadas del sistema de la ANEAES, ver su README). Son .xls con la
estructura OLE dañada: xlrd los abre solo con `ignore_workbook_corruption=True`.
La fila es una carrera (o programa) en una sede. Las no acreditadas traen fecha de resolución; las acreditadas,
vigencia (inicio y fin). La sede es texto libre ("No aplica" cuando no se informa): no es ciudad normalizada.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd
import xlrd

RAIZ = Path(__file__).resolve().parents[2]
CARPETA = RAIZ / "data" / "raw" / "aneaes"
SALIDA = RAIZ / "data" / "clean" / "aneaes_programas.parquet"
# archivo -> (nivel, acreditada)
ARCHIVOS = {
    "carreras_grado_acreditadas.xls": ("grado", True),
    "carreras_grado_no_acreditadas.xls": ("grado", False),
    "programas_posgrado_acreditados.xls": ("posgrado", True),
    "programas_posgrado_no_acreditados.xls": ("posgrado", False),
}
NOMBRES = {  # encabezado normalizado (sin <br> ni espacios) -> columna
    "carreradegrado": "programa", "programadeposgrado": "programa", "institución": "institucion",
    "facultad/unidadacadémica": "facultad", "sede/filial/campus": "sede", "modelo/sistema": "modelo",
    "nro.resolución": "nro_resolucion", "fechainicio": "fecha_inicio", "fechafin": "fecha_fin",
    "fechaderesolución": "fecha_resolucion",
}


def normalizar_encabezado(texto: str) -> str:
    """Quita los <br> y todos los espacios de un encabezado y lo pasa a minúsculas."""
    return "".join(texto.replace("<br>", "").split()).lower()


def serial_a_fecha(valor: float | str) -> datetime | None:
    """Número de serie de Excel -> fecha; vacío -> None."""
    return None if valor in ("", None) else xlrd.xldate_as_datetime(float(valor), 0)


def leer(ruta: Path, nivel: str, acreditada: bool) -> pd.DataFrame:
    hoja = xlrd.open_workbook(ruta, ignore_workbook_corruption=True).sheet_by_index(0)
    cols = [NOMBRES[normalizar_encabezado(c)] for c in hoja.row_values(0)]
    df = pd.DataFrame([hoja.row_values(i) for i in range(1, hoja.nrows)], columns=cols)
    for c in ("fecha_inicio", "fecha_fin", "fecha_resolucion"):
        df[c] = pd.to_datetime(df[c].map(serial_a_fecha)) if c in df else pd.NaT
    df["nro_resolucion"] = df["nro_resolucion"].astype(str).str.removesuffix(".0")
    df.insert(0, "nivel", nivel)
    df.insert(1, "acreditada", acreditada)
    return df


def cargar(carpeta: Path = CARPETA) -> pd.DataFrame:
    """Une las cuatro tablas. Lanza FileNotFoundError si falta alguna."""
    partes = []
    for nombre, (nivel, acreditada) in ARCHIVOS.items():
        ruta = carpeta / nombre
        if not ruta.exists():
            raise FileNotFoundError(ruta)
        partes.append(leer(ruta, nivel, acreditada))
    df = pd.concat(partes, ignore_index=True)
    df.insert(0, "programa_id", range(1, len(df) + 1))
    return df


def main() -> None:
    df = cargar()
    df.to_parquet(SALIDA, index=False)
    print(df.groupby(["nivel", "acreditada"]).size().to_string())


if __name__ == "__main__":
    main()
