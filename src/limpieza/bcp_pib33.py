"""PIB por 33 actividades económicas del BCP (cuentas nacionales, anual desde 1991).

Lee las hojas "Valores Corrientes" y "Valores Constantes" del Excel original y las deja en formato
largo: una fila por (actividad, año, tipo de precio). No se modifica el archivo de data/raw.
"""
from __future__ import annotations

from pathlib import Path

import openpyxl
import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
EXCEL = RAIZ / "data" / "raw" / "bcp_cuentas_nacionales" / "PIB_33_actividades_desde_1991.xlsx"
SALIDA = RAIZ / "data" / "clean" / "pib_33_actividades.parquet"
HOJAS = {"Valores Corrientes": "corriente", "Valores Constantes": "constante"}
TOTALES = {"Valor Agregado Bruto": "vab", "Impuestos netos a los productos": "impuestos", "Total": "total"}


def leer_hoja(ws: openpyxl.worksheet.worksheet.Worksheet, precio: str) -> pd.DataFrame:
    """Hoja del BCP -> tabla larga (actividad, tipo_fila, anio, preliminar, precio, valor_mill_gs)."""
    filas = list(ws.iter_rows(values_only=True))
    i0 = next(i for i, r in enumerate(filas) if r[0] and str(r[0]).startswith("Sector econ"))
    anios = [(c, str(c).endswith("*"), int(str(c).rstrip("*"))) for c in filas[i0][1:] if c is not None]
    salida = []
    for r in filas[i0 + 1:]:
        nombre = (r[0] or "").strip() if isinstance(r[0], str) else ""
        if not nombre or nombre.startswith(("Fuente", "*")):
            continue
        tipo = TOTALES.get(nombre, "actividad")
        for j, (_, prelim, anio) in enumerate(anios, start=1):
            valor = r[j]
            if isinstance(valor, (int, float)):
                salida.append((nombre, tipo, anio, prelim, precio, float(valor)))
    return pd.DataFrame(salida, columns=["actividad", "tipo_fila", "anio", "preliminar", "precio", "valor_mill_gs"])


def cargar(ruta: Path = EXCEL) -> pd.DataFrame:
    wb = openpyxl.load_workbook(ruta, data_only=True)
    partes = [leer_hoja(wb[hoja], precio) for hoja, precio in HOJAS.items()]
    df = pd.concat(partes, ignore_index=True)
    orden = list(dict.fromkeys(df.loc[df.tipo_fila == "actividad", "actividad"]))
    df["actividad_id"] = df["actividad"].map({n: f"N{i:02d}" for i, n in enumerate(orden, start=1)})
    return df


def main() -> None:
    df = cargar()
    df.to_parquet(SALIDA, index=False)
    act = df[df.tipo_fila == "actividad"]
    print(f"{act.actividad.nunique()} actividades, años {act.anio.min()}-{act.anio.max()}, filas {len(df)}")


if __name__ == "__main__":
    main()
