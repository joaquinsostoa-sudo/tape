"""Red eléctrica del mapa MIC (pestaña C): subestaciones, potencia disponible por año y trazado de las líneas.

Fuente: data/raw/mic_mapa/red_electrica_mic_2026-10-09.json (ver el README de esa carpeta). Los datos son la
foto del visor (potencia disponible proyectada por subestación, en MW) y no tienen licencia declarada.
Los años de las tablas de potencia no son consecutivos: 23 kV omite 2030 y 220/66 kV omite 2029. Los primeros
cuatro años coinciden con los gráficos del visor; los demás se deducen del orden de los encabezados (por confirmar).
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
JSON_ELEC = RAIZ / "data" / "raw" / "mic_mapa" / "red_electrica_mic_2026-10-09.json"
CLEAN = RAIZ / "data" / "clean"
ANIOS_23KV = [2026, 2027, 2028, 2029, 2031, 2032, 2033]
ANIOS_220_66KV = [2025, 2026, 2027, 2028, 2030, 2031, 2032, 2033]
TABLA_23KV = "C4- POTENCIA DISPONIBLE 23kV (MW)"
TABLA_220_66KV = "C5- POTENCIA DISPONIBLE 220/66kV (MW)"


def _limpiar(texto: str) -> str:
    """Decodifica las entidades que el visor usa en sus tablas (el guion llega como &hyp;)."""
    return texto.replace("&hyp;", "-").replace("&nbsp;", " ").strip()


def subestaciones(datos: dict) -> pd.DataFrame:
    df = pd.DataFrame(datos["subestaciones"]).rename(columns={"serie": "nivel_tension"})
    df.insert(0, "subestacion_id", range(1, len(df) + 1))
    return df


def potencia_larga(datos: dict) -> pd.DataFrame:
    """Potencia disponible en formato largo: departamento, subestación, red (23 kV o 220/66 kV), año, MW."""
    filas = []
    for tabla, red, anios in ((TABLA_23KV, "23kV", ANIOS_23KV), (TABLA_220_66KV, "220/66kV", ANIOS_220_66KV)):
        for f in datos["tablas"][tabla]:
            depto, nombre, valores = _limpiar(f[0]), _limpiar(f[1]), f[2:]
            if len(valores) != len(anios):
                raise ValueError(f"{tabla}: {len(valores)} valores para {len(anios)} años en {nombre}")
            # celda vacía = el visor no informa (SE023kV_LUQUE en 220/66 kV): se guarda NaN, no cero
            filas += [(depto, nombre, red, a, float("nan") if v is None else float(v))
                      for a, v in zip(anios, valores, strict=True)]
    return pd.DataFrame(filas, columns=["departamento", "subestacion", "red", "anio", "potencia_disp_mw"])


def lineas(datos: dict) -> pd.DataFrame:
    """Vértices del trazado, en el orden del visor. `serie` es el tipo (central, corredor, línea, troncal 500 kV)."""
    df = pd.DataFrame(datos["lineas"]).drop(columns="tipo")
    df.insert(0, "vertice_id", range(1, len(df) + 1))
    return df


def main() -> None:
    datos = json.loads(JSON_ELEC.read_text(encoding="utf-8"))
    sub, pot, lin = subestaciones(datos), potencia_larga(datos), lineas(datos)
    sub.to_csv(CLEAN / "mic_subestaciones.csv", index=False, encoding="utf-8")
    pot.to_csv(CLEAN / "mic_potencia_disponible.csv", index=False, encoding="utf-8")
    lin.to_parquet(CLEAN / "mic_lineas_vertices.parquet", index=False)
    print(f"{len(sub)} subestaciones; {len(pot)} filas de potencia; {len(lin)} vértices de línea "
          f"({lin.serie.value_counts().to_dict()})")


if __name__ == "__main__":
    main()
