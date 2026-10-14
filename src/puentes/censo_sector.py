"""Puente de las ramas del Censo Económico 2011 (CIIU nacional de 2 y 3 dígitos) -> sector TAPE, con pesos y confianza por fila.

Método:
1. El código del censo se busca como prefijo entre las 4 dígitos de la CIIU Rev.4 de la ONU (`isic4-cpc21.txt`). Si no hay ninguna clase con ese prefijo (códigos nacionales como 610, 620, 780, 800, 870...),
   se usa la división (los 2 primeros dígitos). Un código de 2 dígitos es el residual que el INE agrupó por reserva estadística: toma todas las clases de la división.
2. Cada clase pesa lo mismo; el peso de un sector es la fracción de clases que caen en él (`sectores_de_clase`). Es un supuesto neutro: no se usa ninguna fuente posterior a 2010 (p. ej. la
   composición del mapa MIC 2026) para repartir, porque contaminaría el backtest territorial.
3. Confianza: `alta` si todas las clases caen en un sector; `media` si hay dos sectores o el código es de 3 dígitos sin equivalente internacional exacto; `baja` si hay más de dos o es un residual de 2 dígitos.
4. **Desviaciones de la CIIU Rev.4 internacional** (señaladas, no corregidas en silencio; se resuelven en `DESVIACIONES` por el nombre de la rama): 107 («alimentos preparados para animales» = 1080 internacional),
   109 («otros productos alimenticios n.c.p.» = todo el grupo internacional 107), 111 y 112 (bebidas alcohólicas y no alcohólicas = grupo 110 internacional), 202 («biocombustibles», sin clase propia: 2011 como en el
   puente HS) y 209 («otros productos químicos n.c.p.» = grupo internacional 202).

Uso: uv run python -m src.puentes.censo_sector
"""
from __future__ import annotations

import pandas as pd

from .taxonomia_tape import RAIZ, SECTORES, clases_ciiu4, prefijos, sectores_de_clase

CENSO_DISTRITO = RAIZ / "data" / "clean" / "censo2011_distrito_rama.csv"
SALIDA = RAIZ / "data" / "clean" / "puente_censo2011_sector.csv"
SALIDA_DISTRITO = RAIZ / "data" / "clean" / "censo2011_distrito_sector_tape.csv"
NUMERICAS = ["ue", "po", "po_h", "po_m", "remuneraciones", "gastos", "ingresos"]

# código del censo -> (clases CIIU Rev.4 con su peso, confianza, nota). Nombres de las ramas leídos del propio censo.
DESVIACIONES: dict[str, tuple[list[tuple[str, float]], str, str]] = {
    "107": ([("1080", 1.0)], "alta", "el censo llama 107 a «alimentos preparados para animales» (en la Rev.4 internacional es 108)"),
    "109": ([("1071", 1 / 6), ("1072", 1 / 6), ("1073", 1 / 6), ("1074", 1 / 6), ("1075", 1 / 6), ("1079", 1 / 6)], "baja",
            "«otros productos alimenticios n.c.p.» abarca todo el grupo internacional 107 (panadería, azúcar, confitería, pastas, comidas preparadas y otros); reparto neutro por clase"),
    "111": ([("1101", 1 / 3), ("1102", 1 / 3), ("1103", 1 / 3)], "media", "bebidas alcohólicas = destilación, vinos y cerveza del grupo internacional 110"),
    "112": ([("1104", 1.0)], "alta", "bebidas no alcohólicas y aguas envasadas = 1104 internacional"),
    "202": ([("2011", 1.0)], "media", "biocombustibles no tienen clase CIIU propia; se asimilan a 2011 como en el puente HS (etanol)"),
    "209": ([("2021", 0.25), ("2022", 0.25), ("2023", 0.25), ("2029", 0.25)], "baja", "«otros productos químicos n.c.p.» abarca el grupo internacional 202; reparto neutro por clase"),
}


def _confianza(sectores: dict[str, float], dos_digitos: bool, sin_equivalente: bool) -> str:
    n = len(sectores)
    if n == 1:
        return "media" if sin_equivalente else "alta"
    if dos_digitos or n > 2:
        return "baja"
    return "media"


def mapear(codigo: str, clases: list[str]) -> list[dict]:
    """Filas del puente (una por sector TAPE) para un código del censo."""
    if codigo in DESVIACIONES:
        lista, conf, nota = DESVIACIONES[codigo]
        origen = "desviacion"
    else:
        bajo = [c for c in clases if c.startswith(codigo)]
        sin_eq = False
        if not bajo and len(codigo) == 3:  # código nacional sin grupo internacional: se usa la división
            bajo, sin_eq = [c for c in clases if c.startswith(codigo[:2])], True
        if not bajo:  # el comercio no tiene clases en la concordancia de la ONU (no produce bienes): se usan los prefijos de la taxonomía
            sec = sorted({s.id for s in SECTORES for p in prefijos(s) if p.startswith(codigo) or codigo.startswith(p)})
            if not sec:
                return [{"ciiu_censo": codigo, "sector_id": "", "peso": 0.0, "ciiu4": "", "confianza": "sin_sector", "origen": "sin_clases", "nota": "ningún prefijo en la CIIU Rev.4 ni en la taxonomía"}]
            return [{"ciiu_censo": codigo, "sector_id": s, "peso": 1.0 / len(sec), "ciiu4": codigo, "confianza": "alta" if len(sec) == 1 else "media", "origen": "taxonomia",
                     "nota": "sin clases en la concordancia de la ONU (comercio/servicios): prefijo de la taxonomía"} for s in sec]
        lista = [(c, 1.0 / len(bajo)) for c in bajo]
        conf, nota, origen = "", "código nacional sin grupo internacional exacto: se usa la división" if sin_eq else "", "prefijo"
        dos = len(codigo) == 2
        por_sector: dict[str, float] = {}
        for c, p in lista:
            por_sector[sectores_de_clase(c)[0]] = por_sector.get(sectores_de_clase(c)[0], 0.0) + p
        conf = _confianza(por_sector, dos, sin_eq)
    por_sector = {}
    clases_sector: dict[str, list[str]] = {}
    for c, p in lista:
        s = sectores_de_clase(c)[0]
        por_sector[s] = por_sector.get(s, 0.0) + p
        clases_sector.setdefault(s, []).append(c)
    return [{"ciiu_censo": codigo, "sector_id": s, "peso": p, "ciiu4": ",".join(clases_sector[s]), "confianza": conf, "origen": origen, "nota": nota} for s, p in por_sector.items()]


def construir(ramas: pd.DataFrame, clases: list[str]) -> pd.DataFrame:
    """Puente de todos los códigos del censo, con el nombre de la rama y las unidades económicas totales (para ordenar la revisión)."""
    g = ramas[ramas.ciiu != ""].groupby("ciiu").agg(rama=("rama", "first"), ue_total=("ue", "sum")).reset_index()
    filas = []
    for r in g.itertuples(index=False):
        for f in mapear(r.ciiu, clases):
            filas.append({**f, "rama": r.rama, "ue_total": r.ue_total})
    return pd.DataFrame(filas)


def por_distrito(ramas: pd.DataFrame, puente: pd.DataFrame) -> pd.DataFrame:
    """Unidades, ocupados y demás variables por distrito y sector TAPE (las ramas con varios sectores se reparten por el peso). El residual sin código queda como `RESIDUAL_<sector del censo>`."""
    r = ramas.copy()
    r["ciiu"] = r.ciiu.astype(str)
    con = r[r.ciiu != ""].merge(puente[["ciiu_censo", "sector_id", "peso", "confianza"]], left_on="ciiu", right_on="ciiu_censo", how="left")
    sin = r[r.ciiu == ""].assign(sector_id=lambda d: "RESIDUAL_" + d.sector.str.upper(), peso=1.0, confianza="residual")
    t = pd.concat([con, sin], ignore_index=True)
    for c in NUMERICAS:
        t[c] = t[c] * t.peso
    return t.groupby(["departamento", "distrito", "sector_id", "confianza"], as_index=False)[NUMERICAS].sum()


def main() -> None:
    import sys

    sys.stdout.reconfigure(encoding="utf-8")
    ramas = pd.read_csv(CENSO_DISTRITO, dtype={"ciiu": str}, keep_default_na=False)
    puente = construir(ramas, clases_ciiu4())
    puente.to_csv(SALIDA, index=False, encoding="utf-8")
    d = por_distrito(ramas, puente)
    d.to_csv(SALIDA_DISTRITO, index=False, encoding="utf-8")
    total = ramas.ue.sum()
    print(f"{puente.ciiu_censo.nunique()} códigos del censo; {len(puente)} filas; unidades repartidas: {d.ue.sum():.0f} de {total:.0f}")
    manuf = ramas[ramas.ciiu.str[:2].isin([str(x) for x in range(10, 34)]) & (ramas.ciiu != "")]
    m = manuf.merge(puente.drop_duplicates("ciiu_censo")[["ciiu_censo", "confianza", "origen"]], left_on="ciiu", right_on="ciiu_censo")
    print("manufactura (unidades económicas) por confianza del puente:")
    print((m.groupby("confianza").ue.sum() / m.ue.sum() * 100).round(1).to_string())
    print("por origen:", (m.groupby("origen").ue.sum() / m.ue.sum() * 100).round(1).to_dict())


if __name__ == "__main__":
    main()
