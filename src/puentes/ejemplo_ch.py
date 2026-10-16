"""Ejemplo de cómo se aplica la medición de capital humano a una industria que exige formación específica y a una que no.

Es una ILUSTRACIÓN con una regla simple y explícita; no es un resultado ni una decisión declarada:
1. ¿La industria exige formación específica? (NBER ≥ 0,28, `exigencia_formacion_sector.csv`, D28).
2. Base del distrito = percentil del índice v2 a 30 km (pools accesibles de PEA con secundaria, salud y graduados transversales; sede principal).
3. Formación específica = percentil del pool de graduados de técnico y grado del sector a 30 km (cuenta completa, D27; proximidad D30).
4. Puntaje = promedio de la base y la formación específica si la industria la exige; solo la base si no la exige. Se marca cuál de las dos partes limita al distrito.

Ejemplo: S40 Electrónica y equipo eléctrico (exige, NBER 0,44) y S09 Frigoríficos (no exige, NBER 0,16). También se contrasta con dónde están hoy las industrias (mapa MIC) y con la
población, para ver si el puntaje dice algo más que el tamaño del distrito.

Salidas: `data/model/ejemplo_ficha_S40.csv` y `data/model/ejemplo_ficha_S09.csv`. Uso: uv run python -m src.puentes.ejemplo_ch
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import base_capital_humano as bc
from .taxonomia_tape import RAIZ

PROXIMIDAD = RAIZ / "data" / "clean" / "proximidad_distrito.csv"
POR_SECTOR = RAIZ / "data" / "clean" / "proximidad_graduados_sector.csv"
INDUSTRIAS = RAIZ / "data" / "clean" / "industrias_distrito_sector_tape.parquet"
EXIGENCIA = RAIZ / "data" / "clean" / "exigencia_formacion_sector.csv"
ESCALA = 30
EJEMPLOS = ("S40", "S09")


def puntaje(p_base: pd.Series, p_especifico: pd.Series, exige: bool) -> pd.Series:
    """Si la industria exige formación específica, promedio de la base y la formación específica; si no, solo la base."""
    return pd.concat([p_base, p_especifico], axis=1).mean(axis=1, skipna=False) if exige else p_base.copy()


def limitante(p_base: pd.Series, p_especifico: pd.Series) -> pd.Series:
    """Qué parte limita al distrito: la de menor percentil."""
    return pd.Series(np.where(p_especifico < p_base, "formación específica", "base"), index=p_base.index)


def ficha(sector: str, exige: bool, prox: pd.DataFrame, por_sector: pd.DataFrame, industrias: pd.DataFrame) -> pd.DataFrame:
    """Ficha por distrito para un sector: base, formación específica, puntaje, parte limitante y cuántas industrias hay hoy en el mapa MIC."""
    s = por_sector[(por_sector["sector_id"] == sector) & (por_sector["escenario"] == "principal") & (por_sector["escala_km"] == ESCALA)]
    s = s.assign(dep=[bc.departamento(v) for v in s["departamento"]], clave=[bc.llave(v) for v in s["distrito"]])[["dep", "clave", "propios", "pool"]]
    d = prox.merge(s, on=["dep", "clave"], how="left").fillna({"propios": 0, "pool": 0})
    d.loc[d[f"indice_v2_{ESCALA}_principal"].isna(), "pool"] = np.nan
    d["p_base"] = d[f"indice_v2_{ESCALA}_principal"]
    d["p_especifico"] = bc.percentil(d["pool"])
    d["puntaje"] = puntaje(d["p_base"], d["p_especifico"], exige)
    d["limitante"] = limitante(d["p_base"], d["p_especifico"])
    m = industrias[industrias["sector_id"] == sector].groupby(["dep", "clave"])["n_industrias"].sum().rename("industrias_hoy").reset_index()
    d = d.merge(m, on=["dep", "clave"], how="left").fillna({"industrias_hoy": 0})
    d["rango"] = d["puntaje"].rank(ascending=False, method="min")
    return d


def cargar() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    prox = pd.read_csv(PROXIMIDAD)
    prox["dep"] = [bc.departamento(v) for v in prox["departamento"]]
    prox["clave"] = [bc.llave(v) for v in prox["distrito"]]
    base = bc.distritos_base()
    ind = bc.a_clave_base(pd.read_parquet(INDUSTRIAS), "departamento", "distrito", base)
    return prox, pd.read_csv(POR_SECTOR), ind, pd.read_csv(EXIGENCIA, dtype=str).fillna("")


def control_vs_poblacion(d: pd.DataFrame) -> dict[str, float]:
    """¿El puntaje describe mejor que el tamaño dónde están hoy las industrias? Distritos con industria en el 20 % superior por puntaje, por población, por base y por formación específica."""
    hoy = d["industrias_hoy"] > 0
    p_pob = bc.percentil(d["poblacion"])
    sup = lambda s: s >= s.quantile(0.8)
    return {"distritos_con_industria": float(hoy.sum()), "en_top20_puntaje": float((sup(d["puntaje"]) & hoy).sum()), "en_top20_poblacion": float((sup(p_pob) & hoy).sum()),
            "en_top20_base": float((sup(d["p_base"]) & hoy).sum()), "en_top20_especifico": float((sup(d["p_especifico"]) & hoy).sum())}


def main() -> None:
    prox, por_sector, ind, exig = cargar()
    for sector in EJEMPLOS:
        e = exig[exig["sector_id"] == sector].iloc[0]
        d = ficha(sector, e["exige_formacion"] == "si", prox, por_sector, ind)
        d.to_csv(RAIZ / "data" / "model" / f"ejemplo_ficha_{sector}.csv", index=False, encoding="utf-8")
        print(f"{sector} {e['nombre']}: NBER {e['habilidades']} -> exige={e['exige_formacion']} | control frente a la población: {control_vs_poblacion(d)}")


if __name__ == "__main__":
    main()
