"""Limpieza del Censo Económico Nacional 2011 (INE; datos del año 2010), Cuadro 1: unidades económicas y personal ocupado por departamento, distrito, sector y rama.

El archivo (`49d4bCEN2011_DIST_CUADRO_1.xlsx`, tal como lo bajó el equipo de la web del INE) trae bloques anidados: departamento (en mayúsculas, con sus propios totales y ramas) → distrito → sector (Industria, Comercio, Servicios) → rama CIIU Rev.4
a 2 o 3 dígitos. Las ramas chicas se agrupan en una fila «Otras actividades de <sector>» sin código (reserva estadística). Industria incluye minería de apoyo, manufactura, electricidad,
construcción; no hay agropecuario ni administración pública.

Salida: `data/clean/censo2011_distrito_rama.csv` (nivel distrito) y `censo2011_departamento_rama.csv` (nivel departamento), una fila por rama, con `ciiu` vacío y `rama = Otras...` en el residual.
Comprobaciones (en `verificar`): las ramas suman el total del sector, los sectores el total del distrito, los distritos el del departamento, los departamentos el TOTAL.

Uso: uv run python -m src.limpieza.censo_2011
"""
from __future__ import annotations

import re
import sys

import pandas as pd

from src.puentes.taxonomia_tape import RAIZ

ENTRADA = RAIZ / "data" / "raw" / "censo_2011" / "49d4bCEN2011_DIST_CUADRO_1.xlsx"
SALIDA_DIST = RAIZ / "data" / "clean" / "censo2011_distrito_rama.csv"
SALIDA_DEP = RAIZ / "data" / "clean" / "censo2011_departamento_rama.csv"
SECTORES = ("Industria", "Comercio", "Servicios")
COLS = ["a", "b", "ue", "po", "po_h", "po_m", "remuneraciones", "gastos", "ingresos"]


def _es_departamento(texto: str) -> bool:
    return texto == texto.upper() and re.search("[A-ZÁÉÍÓÚÑ]", texto) is not None


def sector_de_division(ciiu: str) -> str:
    """Sector del archivo según la división CIIU: Industria (05-43), Comercio (45-47) y Servicios (49 en adelante); «Mixto» si no hay código (residual de un distrito sin sectores)."""
    if not ciiu:
        return "Mixto"
    d = int(ciiu[:2])
    return "Industria" if d < 45 else ("Comercio" if d <= 47 else "Servicios")


def completar(ramas: pd.DataFrame, totales: pd.DataFrame) -> pd.DataFrame:
    """Agrega una fila residual «implícito» cuando el total de un sector es mayor que la suma de sus ramas (sectores sin detalle por reserva estadística, p. ej. 5 servicios en Carmelo Peralta)."""
    cols = COLS[2:]
    claves = ["departamento", "distrito", "sector"]
    suma = ramas[~ramas.sector_inferido].fillna({"distrito": ""}).groupby(claves)[cols].sum()
    tot = totales[totales.sector.notna()].fillna({"distrito": ""}).set_index(claves)[cols]
    falta = (tot - suma.reindex(tot.index).fillna(0.0))
    falta = falta[falta.ue > 0].reset_index()
    if falta.empty:
        return ramas
    falta["distrito"] = falta.distrito.replace("", None)
    falta["ciiu"], falta["sector_inferido"] = "", False
    falta["rama"] = "Otras actividades de " + falta.sector.str.lower() + " (implícito)"
    return pd.concat([ramas, falta[ramas.columns]], ignore_index=True)


def leer(ruta=ENTRADA) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Devuelve (ramas, totales, referencia): ramas con una fila por rama y bloque; totales con las filas de total de departamento, distrito y sector; TOTAL nacional."""
    crudo = pd.read_excel(ruta, header=None).iloc[:, :9]
    crudo.columns = COLS
    ramas, totales = [], []
    dep = dis = sec = None
    nacional: dict = {}
    for r in crudo.itertuples(index=False):
        a = "" if pd.isna(r.a) else str(r.a).strip()
        if pd.isna(r.ue):
            continue
        num = r._asdict()
        datos = {k: num[k] for k in COLS[2:]}
        if a == "TOTAL":
            nacional = datos
        elif re.fullmatch(r"\d{2,4}", a) or (a == "" and isinstance(r.b, str) and r.b.startswith("Otras actividades")):
            # los distritos chicos no traen encabezado de sector: se infiere de la división y se marca
            ramas.append({"departamento": dep, "distrito": dis, "sector": sec or sector_de_division(a), "sector_inferido": sec is None, "ciiu": a, "rama": r.b, **datos})
        elif a in SECTORES:
            sec = a
            totales.append({"departamento": dep, "distrito": dis, "sector": sec, **datos})
        elif _es_departamento(a):
            dep, dis, sec = a, None, None
            totales.append({"departamento": dep, "distrito": None, "sector": None, **datos})
        else:
            dis, sec = a, None
            totales.append({"departamento": dep, "distrito": dis, "sector": None, **datos})
    r, tot = pd.DataFrame(ramas), pd.DataFrame(totales)
    return completar(r, tot), tot, nacional


def verificar(ramas: pd.DataFrame, totales: pd.DataFrame, nacional: dict, tol: float = 0.0) -> dict[str, int]:
    """Cuenta los bloques cuya suma no coincide con su total (unidades económicas); un diccionario vacío de diferencias = todo coincide."""
    mal = {}
    # ramas (con encabezado de sector explícito) contra el total del sector, por (departamento, distrito, sector)
    s = ramas[~ramas.sector_inferido].fillna({"distrito": ""}).groupby(["departamento", "distrito", "sector"]).ue.sum().rename("suma")
    t = totales[totales.sector.notna()].fillna({"distrito": ""}).set_index(["departamento", "distrito", "sector"]).ue
    mal["ramas_vs_sector"] = int(((s - t.reindex(s.index)).abs() > tol).sum())
    # todas las ramas contra el total del distrito o del departamento
    tr = ramas.fillna({"distrito": ""}).groupby(["departamento", "distrito"]).ue.sum()
    tt = totales[totales.sector.isna()].fillna({"distrito": ""}).set_index(["departamento", "distrito"]).ue
    mal["ramas_vs_bloque"] = int(((tr - tt.reindex(tr.index)).abs() > tol).sum())
    # distritos contra el departamento (Asunción es departamento y distrito a la vez)
    d = totales[totales.sector.isna() & totales.distrito.notna()].groupby("departamento").ue.sum()
    dep = totales[totales.sector.isna() & totales.distrito.isna()].set_index("departamento").ue
    mal["distritos_vs_departamento"] = int(((d - dep.reindex(d.index)).abs() > tol).sum())
    mal["departamentos_vs_total"] = int(abs(dep.sum() - nacional.get("ue", 0)) > tol)
    return mal


def main() -> None:
    ramas, totales, nacional = leer()
    mal = verificar(ramas, totales, nacional)
    dep = ramas[ramas.distrito.isna()]
    asuncion = dep[dep.departamento == "ASUNCIÓN"].assign(distrito="ASUNCIÓN")  # el departamento es un solo distrito y el archivo no lo repite
    dist = pd.concat([ramas[ramas.distrito.notna()], asuncion], ignore_index=True)
    dist.to_csv(SALIDA_DIST, index=False, encoding="utf-8")
    dep.to_csv(SALIDA_DEP, index=False, encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    print(f"TOTAL nacional: {nacional['ue']:.0f} unidades, {nacional['po']:.0f} ocupados")
    print(f"distritos: {dist.groupby(['departamento', 'distrito']).ngroups}; filas de rama: {len(dist)} (distrito) y {len(dep)} (departamento)")
    print("diferencias (bloques que no suman):", mal)


if __name__ == "__main__":
    main()
