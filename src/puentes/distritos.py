"""Equivalencia de distritos entre el Censo Económico 2011 (234 distritos, solo nombres), los límites DGEEC 2012 (247 polígonos) y las ciudades del Censo 2022 / mapa MIC (263).

Unidad de comparación = el distrito del Censo 2011 (`unidad_2011`): todo distrito posterior se asigna a uno de ellos (a sí mismo si existía, o a su distrito padre si se creó después).
1. 2011 ↔ 2012: se emparejan los nombres dentro de cada departamento (asignación óptima por similitud de nombres normalizados: tildes, abreviaturas, grafías guaraníes como YBY/YVY/IVY, «Ex ...»).
   Los polígonos de 2012 que quedan sin pareja son distritos nuevos: su padre es el distrito vecino (de 2011) con el que comparten la frontera más larga (confianza `baja`; lo valida el equipo).
2. 2022 ↔ 2012: igual por nombres. Las ciudades de 2022 sin pareja son nuevas: su padre es el polígono de 2012 que contiene su punto, y de ahí su unidad de 2011.
Cada fila lleva similitud, relación y confianza (alta: similitud ≥ 0,9; media: 0,7 a 0,9; baja: padre por vecindad o por punto). Los emparejamientos dudosos van a revisión.

Uso: uv run python -m src.puentes.distritos
"""
from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher

import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment

from .taxonomia_tape import RAIZ

CENSO_2011 = RAIZ / "data" / "clean" / "censo2011_distrito_rama.csv"
CIUDADES_2022 = RAIZ / "data" / "clean" / "ciudades_mic.csv"
ADM1 = RAIZ / "data" / "raw" / "limites_admin" / "geoBoundaries-PRY-ADM1.geojson"
ADM2 = RAIZ / "data" / "raw" / "limites_admin" / "geoBoundaries-PRY-ADM2.geojson"
SALIDA_2012 = RAIZ / "data" / "clean" / "puente_distritos_2012.csv"
SALIDA_2022 = RAIZ / "data" / "clean" / "puente_distritos_2022.csv"
UMBRAL = 0.6
MIN_KM2 = 1.0  # polígonos de 2012 menores a esto son fragmentos (hay dos de San Juan del Paraná de 0,2 km²), no distritos
CRS_METRICO = "EPSG:32721"
DEPARTAMENTOS = {"CAPITAL": "ASUNCION", "PTE HAYES": "PRESIDENTE HAYES"}
TITULOS = {"DR", "DOCTOR", "GENERAL", "GRAL", "MARISCAL", "MCAL", "CAPITAN", "CAP", "CPTAN", "CORONEL", "CNEL", "TENIENTE", "TTE", "MAYOR", "SGTO", "SARGENTO", "PRESIDENTE", "PTE", "PUERTO", "PTO", "EX", "DE", "DEL", "LA", "LAS", "LOS", "STA", "SANTA"}


def normalizar(texto: str) -> str:
    """Mayúsculas, sin tildes ni signos, espacios simples."""
    t = unicodedata.normalize("NFKD", str(texto).upper())
    t = "".join(c for c in t if c.isascii())
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9 ]", " ", t)).strip()


def departamento(nombre: str) -> str:
    n = normalizar(nombre)
    return DEPARTAMENTOS.get(n, n)


def llave(nombre: str) -> str:
    """Llave fonética para comparar nombres: sin títulos ni «Ex ...», sin espacios, Y→I, V→B, W→U y sin H (YBY, YVY, IBI; YPEJHU, YPE HU)."""
    n = normalizar(nombre)
    n = re.sub(r"\bEX\b.*$", "", n).strip()  # «La Victoria (Ex Puerto Casado)»: el nombre actual es el primero
    palabras = [p for p in n.split() if p not in TITULOS]
    s = "".join(palabras) or n.replace(" ", "")
    return s.replace("Y", "I").replace("V", "B").replace("W", "U").replace("H", "")


def _palabras(nombre: str) -> set[str]:
    n = re.sub(r"\bEX\b.*$", "", normalizar(nombre)).strip()
    return {p for p in n.split() if p not in TITULOS}


def similitud(a: str, b: str) -> float:
    """Máximo entre la similitud de los nombres normalizados completos, la de sus llaves fonéticas y 0,85 si las palabras de uno están todas en el otro (San Pedro ⊂ San Pedro del Ykuamandiyú)."""
    s = max(SequenceMatcher(None, normalizar(a), normalizar(b)).ratio(), SequenceMatcher(None, llave(a), llave(b)).ratio())
    pa, pb = _palabras(a), _palabras(b)
    if pa and pb and (pa <= pb or pb <= pa):
        s = max(s, 0.85)
    return s


def emparejar(izq: list[str], der: list[str], umbral: float = UMBRAL) -> list[tuple[int, int, float]]:
    """Asignación óptima uno a uno entre dos listas de nombres (mayor similitud total); solo se devuelven los pares con similitud ≥ umbral."""
    if not izq or not der:
        return []
    m = np.array([[similitud(a, b) for b in der] for a in izq])
    f, c = linear_sum_assignment(-m)
    return [(int(i), int(j), float(m[i, j])) for i, j in zip(f, c, strict=True) if m[i, j] >= umbral]


def confianza(sim: float) -> str:
    return "alta" if sim >= 0.9 else ("media" if sim >= 0.7 else "baja")


def poligonos_2012():
    """Polígonos de 2012 con su departamento (por el punto representativo dentro de los límites departamentales); los objetos de varias partes se separan."""
    import geopandas as gpd

    a1 = gpd.read_file(ADM1).to_crs(CRS_METRICO)
    a2 = gpd.read_file(ADM2).to_crs(CRS_METRICO).explode(index_parts=False).reset_index(drop=True)  # «Bella Vista» es un solo objeto con dos partes: Amambay e Itapúa
    pt = a2.copy()
    pt["geometry"] = a2.representative_point()
    j = gpd.sjoin(pt, a1[["shapeName", "geometry"]], how="left", predicate="within")
    a2 = a2.assign(departamento=j["shapeName_right"].values)
    a2 = a2.assign(km2=a2.geometry.area / 1e6)
    return a2.rename(columns={"shapeName": "distrito", "shapeID": "id"})[["departamento", "distrito", "id", "km2", "geometry"]]


def padre_por_vecindad(poligonos, nuevo: int, candidatos: list[int]) -> tuple[int, float] | None:
    """Entre los `candidatos` (índices de polígonos), el que comparte la frontera más larga con el polígono `nuevo`; devuelve (índice, metros) o None si ninguno lo toca."""
    mejor = None
    borde = poligonos.geometry.iloc[nuevo].buffer(50)  # tolerancia por la generalización de los límites
    for c in candidatos:
        largo = borde.intersection(poligonos.geometry.iloc[c].boundary).length / 2
        if largo > 0 and (mejor is None or largo > mejor[1]):
            mejor = (c, largo)
    return mejor


def construir_2012(c11: pd.DataFrame, pol) -> pd.DataFrame:
    """Una fila por polígono de 2012: su unidad de 2011 (nombre del Censo), la relación y la confianza."""
    c11 = c11.assign(dep=c11.departamento.map(departamento))
    pol = pol.assign(dep=pol.departamento.map(departamento)).reset_index(drop=True)
    filas: dict[int, dict] = {}
    for dep, g in pol[pol.km2 >= MIN_KM2].groupby("dep"):
        cen = c11[c11.dep == dep].distrito.tolist()
        idx = g.index.tolist()
        for i, j, s in emparejar(g.distrito.tolist(), cen):
            filas[idx[i]] = {"unidad_2011": cen[j], "relacion": "igual", "similitud": s, "confianza": confianza(s), "nota": ""}
    firmes = [i for i in filas]
    for i in pol.index:
        if i in filas:
            continue
        mismos = [k for k in firmes if pol.dep[k] == pol.dep[i]] or firmes
        p = padre_por_vecindad(pol, i, mismos)
        if p is not None and pol.km2[i] < MIN_KM2:
            filas[i] = {"unidad_2011": filas[p[0]]["unidad_2011"], "relacion": "fragmento", "similitud": 0.0, "confianza": "media",
                        "nota": f"polígono de {pol.km2[i]:.2f} km² pegado a {pol.distrito[p[0]]}"}
        elif p is None:
            filas[i] = {"unidad_2011": "", "relacion": "sin_correspondencia", "similitud": 0.0, "confianza": "baja", "nota": "sin vecino con frontera"}
        else:
            filas[i] = {"unidad_2011": filas[p[0]]["unidad_2011"], "relacion": "nuevo_desde_padre", "similitud": 0.0, "confianza": "baja",
                        "nota": f"padre por frontera más larga: {pol.distrito[p[0]]} ({p[1] / 1000:.1f} km)"}
    out = pd.DataFrame.from_dict(filas, orient="index").sort_index()
    return pd.concat([pol[["dep", "distrito", "id"]].rename(columns={"dep": "departamento", "distrito": "distrito_2012", "id": "id_2012"}), out], axis=1)


def construir_2022(ciudades: pd.DataFrame, p12: pd.DataFrame, pol) -> pd.DataFrame:
    """Una fila por ciudad de 2022: el polígono de 2012 con el que coincide (o el que contiene su punto) y la unidad de 2011."""
    import geopandas as gpd

    ciudades = ciudades.assign(dep=ciudades.departamento.map(departamento)).reset_index(drop=True)
    filas = []
    for dep, g in ciudades.groupby("dep"):
        d12 = p12[(p12.departamento == dep) & (p12.relacion != "fragmento")].reset_index(drop=True)  # los fragmentos de menos de 1 km² no son distritos
        pares = {i: (j, s) for i, j, s in emparejar(g.ciudad.tolist(), d12.distrito_2012.tolist())}
        for k, (idx, r) in enumerate(g.iterrows()):
            if k in pares:
                j, s = pares[k]
                u = d12.loc[j]
                filas.append({"departamento": dep, "distrito_2022": r.ciudad, "distrito_2012": u.distrito_2012, "unidad_2011": u.unidad_2011, "relacion": "igual" if u.relacion == "igual" else u.relacion,
                              "similitud": s, "confianza": confianza(min(s, 1.0)) if u.confianza != "baja" else "baja", "nota": u.nota})
            else:
                pt = gpd.GeoSeries(gpd.points_from_xy([r.lon], [r.lat]), crs="EPSG:4326").to_crs(CRS_METRICO).iloc[0]
                dentro = pol[pol.geometry.contains(pt)]
                if len(dentro):
                    u = p12[p12.id_2012 == dentro.id.iloc[0]].iloc[0]
                    filas.append({"departamento": dep, "distrito_2022": r.ciudad, "distrito_2012": "", "unidad_2011": u.unidad_2011, "relacion": "nuevo_desde_padre", "similitud": 0.0, "confianza": "baja",
                                  "nota": f"su punto cae en {u.distrito_2012} (2012)"})
                else:
                    filas.append({"departamento": dep, "distrito_2022": r.ciudad, "distrito_2012": "", "unidad_2011": "", "relacion": "sin_correspondencia", "similitud": 0.0, "confianza": "baja", "nota": "punto fuera de los límites"})
    return pd.DataFrame(filas)


def main() -> None:
    import sys

    sys.stdout.reconfigure(encoding="utf-8")
    c11 = pd.read_csv(CENSO_2011, keep_default_na=False)[["departamento", "distrito"]].drop_duplicates()
    pol = poligonos_2012().reset_index(drop=True)
    p12 = construir_2012(c11, pol)
    p12.to_csv(SALIDA_2012, index=False, encoding="utf-8")
    pol["departamento"] = pol.departamento.map(departamento)
    ciudades = pd.read_csv(CIUDADES_2022)
    p22 = construir_2022(ciudades, p12, pol)
    p22.to_csv(SALIDA_2022, index=False, encoding="utf-8")
    sin = set(c11.distrito.map(normalizar)) - set(p12.unidad_2011.map(normalizar))
    print(f"2012: {len(p12)} polígonos; {p12.relacion.value_counts().to_dict()}; confianza {p12.confianza.value_counts().to_dict()}")
    print(f"2022: {len(p22)} ciudades; {p22.relacion.value_counts().to_dict()}; confianza {p22.confianza.value_counts().to_dict()}")
    print(f"distritos de 2011 sin ningún polígono de 2012: {len(sin)} {sorted(sin)}")


if __name__ == "__main__":
    main()
