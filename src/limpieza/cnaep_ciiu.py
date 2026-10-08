"""Tabla oficial de correspondencia CNAEP 1.0 <-> CIIU Rev.4 (BCP, 2016): PDF -> tabla de 5 dígitos.

Cada fila de datos del PDF tiene un código CNAEP de 4 dígitos (x~60), un dígito de detalle (x~115) y
una o más clases CIIU Rev.4 de 4 dígitos (x~338), alineadas por altura. Un asterisco marca que la
clase CIIU se reparte entre varios códigos CNAEP. Un código CNAEP puede corresponder a varias clases
CIIU (p. ej. 5911 -> 5911 y 5912): la celda de la derecha queda centrada frente a la fila.
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import pdfplumber

RAIZ = Path(__file__).resolve().parents[2]
PDF = RAIZ / "data" / "raw" / "bcp_cuentas_nacionales" / "Tabla_correspondencia_CNAEP1.0_CIIU4.pdf"
SALIDA = RAIZ / "data" / "clean" / "cnaep1_ciiu4.csv"
COL_CODIGO, COL_DIGITO, COL_CIIU = (50, 70), (105, 130), (325, 350)
PENALIZACION_COMPARTIR = 15.0  # puntos de altura: compartir una clase entre filas debe estar muy justificado


def _en(x: float, rango: tuple[float, float]) -> bool:
    return rango[0] <= x <= rango[1]


def repartir_digitos(digitos: list[int], n_codigos: int) -> list[list[int]]:
    """Parte la lista de dígitos en corridas estrictamente crecientes (una por código CNAEP)."""
    corridas: list[list[int]] = []
    for d in digitos:
        if corridas and d > corridas[-1][-1]:
            corridas[-1].append(d)
        else:
            corridas.append([d])
    if len(corridas) != n_codigos:
        raise ValueError(f"{len(corridas)} corridas de dígitos para {n_codigos} códigos")
    return corridas


def asignar_ciiu(ys_filas: list[float], ys_ciiu: list[float]) -> list[list[int]]:
    """Alinea las filas CNAEP con los tokens CIIU (ambos ordenados por altura).

    Cada fila recibe un tramo consecutivo de tokens; el primer token de una fila puede ser el último
    de la anterior (una clase CIIU que abarca varias filas CNAEP). Minimiza la suma de
    |altura media del tramo - altura de la fila|, con una penalización mínima por compartir.
    Devuelve, para cada fila, los índices de sus tokens CIIU.
    """
    r, m = len(ys_filas), len(ys_ciiu)
    if m == 0:
        raise ValueError("no hay clases CIIU en la página")
    if m == r:  # caso normal: una clase CIIU por fila
        return [[i] for i in range(r)]
    inf = float("inf")
    # mejor[i][j]: costo de asignar las primeras i filas terminando en el token j-1 (j = tokens usados)
    mejor = [[inf] * (m + 1) for _ in range(r + 1)]
    previo: list[list[tuple[int, int]]] = [[(0, 0)] * (m + 1) for _ in range(r + 1)]
    mejor[0][0] = 0.0
    for i in range(1, r + 1):
        for j in range(1, m + 1):
            for s in range(j):  # el tramo es [s, j)
                for ant, penal in ((s, 0.0), (s + 1, PENALIZACION_COMPARTIR)):  # ant = tokens usados antes; s+1 => comparte s
                    if ant > m or mejor[i - 1][ant] == inf or (i == 1 and ant != 0):
                        continue
                    if i > 1 and ant < s:  # no se permiten tokens sin asignar entre filas
                        continue
                    media = sum(ys_ciiu[s:j]) / (j - s)
                    c = mejor[i - 1][ant] + abs(media - ys_filas[i - 1]) + penal
                    if c < mejor[i][j]:
                        mejor[i][j], previo[i][j] = c, (ant, s)
    if mejor[r][m] == inf:
        raise ValueError(f"no hay alineación posible: {r} filas y {m} clases CIIU")
    grupos: list[list[int]] = []
    j = m
    for i in range(r, 0, -1):
        ant, s = previo[i][j]
        grupos.append(list(range(s, j)))
        j = ant
    return grupos[::-1]


def extraer_pagina(pagina: pdfplumber.page.Page) -> list[dict]:
    palabras = pagina.extract_words()
    codigos = sorted((w for w in palabras if re.fullmatch(r"\d{4}", w["text"]) and _en(w["x0"], COL_CODIGO)),
                     key=lambda w: w["top"])
    digitos = sorted((w for w in palabras if re.fullmatch(r"\d", w["text"]) and _en(w["x0"], COL_DIGITO)),
                     key=lambda w: w["top"])
    ciiu = sorted((w for w in palabras if re.fullmatch(r"\d{4}", w["text"]) and _en(w["x0"], COL_CIIU)),
                  key=lambda w: w["top"])
    asteriscos = [w for w in palabras if w["text"] == "*" and w["x0"] > 340]
    if not digitos:
        return []
    if len(codigos) == len(digitos):  # un código dibujado por fila: emparejar en orden
        corridas = [[int(w["text"])] for w in digitos]
    else:  # un código centrado para varias filas: repartir por corridas crecientes
        corridas = repartir_digitos([int(w["text"]) for w in digitos], len(codigos))
    codigo_de_fila = [c["text"] for c, corrida in zip(codigos, corridas, strict=True) for _ in corrida]
    grupos = asignar_ciiu([d["top"] for d in digitos], [c["top"] for c in ciiu])
    filas = []
    for k, (d, cod4) in enumerate(zip(digitos, codigo_de_fila, strict=True)):
        ini = (digitos[k - 1]["top"] + d["top"]) / 2 if k > 0 else 0
        fin = (d["top"] + digitos[k + 1]["top"]) / 2 if k + 1 < len(digitos) else pagina.height
        nombre = " ".join(w["text"] for w in palabras if 130 <= w["x0"] <= 325 and ini <= w["top"] < fin)
        for idx in grupos[k]:
            c = ciiu[idx]
            filas.append({
                "cnaep": cod4 + d["text"], "cnaep_nombre": nombre, "ciiu4": c["text"],
                "ciiu_compartida": any(abs(a["top"] - c["top"]) < 6 for a in asteriscos),
                "uno_a_varios": len(grupos[k]) > 1, "pagina": pagina.page_number,
                "alineacion": "directa" if len(ciiu) == len(digitos) else "aproximada",
            })
    return filas


# Filas donde el alineado automático falla; verificadas contra el texto del PDF (págs. 26, 32 y 41).
CORRECCIONES: dict[str, list[str]] = {
    "49210": ["4921", "4929"], "49221": ["4921", "4929"], "49229": ["4921", "4929"],
    "49231": ["4922"], "49239": ["4922", "4929"],
    "66220": ["6622"],
    "97000": ["9700", "9810", "9820"],
}


def aplicar_correcciones(df: pd.DataFrame) -> pd.DataFrame:
    """Sustituye las clases CIIU de las filas con error conocido y las marca como corregidas a mano."""
    df = df.assign(corregida_a_mano=False)
    nuevas = []
    for cnaep, clases in CORRECCIONES.items():
        base = df[df.cnaep == cnaep].iloc[0].to_dict()
        for c in clases:
            nuevas.append({**base, "ciiu4": c, "uno_a_varios": len(clases) > 1, "corregida_a_mano": True})
    return pd.concat([df[~df.cnaep.isin(CORRECCIONES)], pd.DataFrame(nuevas)], ignore_index=True).sort_values(
        ["cnaep", "ciiu4"], ignore_index=True)


def extraer(ruta: Path = PDF) -> pd.DataFrame:
    filas: list[dict] = []
    with pdfplumber.open(ruta) as pdf:
        for p in pdf.pages:
            filas += extraer_pagina(p)
    return aplicar_correcciones(pd.DataFrame(filas)).drop_duplicates(["cnaep", "ciiu4"], ignore_index=True)


def main() -> None:
    df = extraer()
    df.to_csv(SALIDA, index=False, encoding="utf-8")
    print(f"{df.cnaep.nunique()} códigos CNAEP de 5 dígitos, {len(df)} pares, {df.ciiu4.nunique()} clases CIIU; "
          f"uno-a-varios: {df[df.uno_a_varios].cnaep.nunique()}")


if __name__ == "__main__":
    main()
