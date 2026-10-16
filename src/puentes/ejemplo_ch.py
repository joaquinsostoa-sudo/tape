"""Ejemplo de cómo se aplica la medición de capital humano a una industria que exige formación específica y a una que no.

Es una ILUSTRACIÓN con una regla simple y explícita; no es un resultado ni una decisión declarada:
1. ¿La industria exige formación específica? (NBER ≥ 0,28, `exigencia_formacion_sector.csv`, D28).
2. Base del distrito = percentil del índice v2 a 30 km (pools accesibles de PEA con secundaria, salud y graduados transversales; sede principal).
3. Formación específica = percentil del pool de graduados de técnico y grado del sector a 30 km (cuenta completa, D27; proximidad D30).
4. Puntaje = promedio de la base y la formación específica si la industria la exige; solo la base si no la exige. Se marca cuál de las dos partes limita al distrito.

Ejemplo: S40 Electrónica y equipo eléctrico (exige, NBER 0,44) y S09 Frigoríficos (no exige, NBER 0,16). También se contrasta con dónde están hoy las industrias (mapa MIC) y con la
población, para ver si el puntaje dice algo más que el tamaño del distrito.

Diagnóstico (D31): el umbral es el percentil 10 de los distritos que hoy ya tienen la industria; categorías lista / falta formación específica / falta base / faltan ambas
(para una industria que no exige formación solo cuenta la base); orden por el mínimo de las dos partes; sensibilidad con la mediana de todos los distritos, otras escalas y el reparto parejo.

Salidas: `data/model/ejemplo_ficha_S40.csv`, `data/model/ejemplo_ficha_S09.csv`, `data/model/ejemplo_diagnostico_*.csv` y `data/model/ejemplo_sensibilidad_*.csv`.
Uso: uv run python -m src.puentes.ejemplo_ch
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
MIN_PRODUCTORES = 10
PERCENTIL_UMBRAL = 0.10
CERCA_UMBRAL = 10.0
CATEGORIAS = ("lista", "falta formación específica", "falta base", "faltan ambas")


def puntaje(p_base: pd.Series, p_especifico: pd.Series, exige: bool, metodo: str = "minimo") -> pd.Series:
    """Si la industria exige formación específica: el mínimo de la base y la formación específica (D31, las partes se complementan) o, como sensibilidad, su promedio;
    si no la exige, solo la base."""
    if not exige:
        return p_base.copy()
    partes = pd.concat([p_base, p_especifico], axis=1)
    return partes.mean(axis=1, skipna=False) if metodo == "promedio" else partes.min(axis=1, skipna=False)


def limitante(p_base: pd.Series, p_especifico: pd.Series) -> pd.Series:
    """Qué parte limita al distrito: la de menor percentil."""
    return pd.Series(np.where(p_especifico < p_base, "formación específica", "base"), index=p_base.index)


def ficha(sector: str, exige: bool, prox: pd.DataFrame, por_sector: pd.DataFrame, industrias: pd.DataFrame, escala: int = ESCALA,
          escenario: str = "principal") -> pd.DataFrame:
    """Ficha por distrito para un sector: base, formación específica, puntaje, parte limitante y cuántas industrias hay hoy en el mapa MIC."""
    s = por_sector[(por_sector["sector_id"] == sector) & (por_sector["escenario"] == escenario) & (por_sector["escala_km"] == escala)]
    s = s.assign(dep=[bc.departamento(v) for v in s["departamento"]], clave=[bc.llave(v) for v in s["distrito"]])[["dep", "clave", "propios", "pool"]]
    d = prox.merge(s, on=["dep", "clave"], how="left").fillna({"propios": 0, "pool": 0})
    d.loc[d[f"indice_v2_{escala}_{escenario}"].isna(), "pool"] = np.nan
    d["p_base"] = d[f"indice_v2_{escala}_{escenario}"]
    d["p_especifico"] = bc.percentil(d["pool"])
    d["puntaje"] = puntaje(d["p_base"], d["p_especifico"], exige)
    d["limitante"] = limitante(d["p_base"], d["p_especifico"])
    m = industrias[industrias["sector_id"] == sector].groupby(["dep", "clave"])["n_industrias"].sum().rename("industrias_hoy").reset_index()
    d = d.merge(m, on=["dep", "clave"], how="left").fillna({"industrias_hoy": 0})
    d["rango"] = d["puntaje"].rank(ascending=False, method="min")
    return d


def umbrales(d: pd.DataFrame, referencia: str = "productores") -> dict[str, float | str]:
    """Umbrales de base, formación específica y pool. Con la referencia «productores» son el percentil 10 de los distritos que hoy tienen la industria; si hay menos de
    10, o con la referencia «mediana», son la mediana de todos los distritos. Devuelve también cuántos productores hay y qué referencia se usó."""
    ok = d.dropna(subset=["p_base", "p_especifico"])
    prod = ok[ok["industrias_hoy"] > 0]
    usar = referencia == "productores" and len(prod) >= MIN_PRODUCTORES
    ref, q = (prod, PERCENTIL_UMBRAL) if usar else (ok, 0.5)
    return {"base": float(ref["p_base"].quantile(q)), "especifico": float(ref["p_especifico"].quantile(q)), "pool": float(ref["pool"].quantile(q)),
            "n_productores": float(len(prod)), "referencia": "productores (percentil 10)" if usar else ("mediana de todos los distritos" if referencia == "mediana" else "mediana (menos de 10 productores)")}


def diagnostico(d: pd.DataFrame, exige: bool, referencia: str = "productores") -> pd.DataFrame:
    """Categoría de cada distrito frente al umbral (D31), orden por el mínimo de las dos partes (solo la base si la industria no exige), brecha en graduados y cercanía al umbral."""
    u = umbrales(d, referencia)
    b_ok = d["p_base"] >= u["base"]
    e_ok = d["p_especifico"] >= u["especifico"]
    if exige:
        cat = np.select([b_ok & e_ok, b_ok & ~e_ok, ~b_ok & e_ok], ["lista", "falta formación específica", "falta base"], "faltan ambas")
        orden = d[["p_base", "p_especifico"]].min(axis=1, skipna=False)
        cerca = ((d["p_base"] - u["base"]).abs() <= CERCA_UMBRAL) | ((d["p_especifico"] - u["especifico"]).abs() <= CERCA_UMBRAL)
        faltan = np.where(~e_ok & d["pool"].notna(), np.maximum(0.0, u["pool"] - d["pool"]), 0.0)
    else:
        cat = np.where(b_ok, "lista", "falta base")
        orden = d["p_base"]
        cerca = (d["p_base"] - u["base"]).abs() <= CERCA_UMBRAL
        faltan = np.full(len(d), np.nan)
    sin = d["p_base"].isna() | (d["p_especifico"].isna() & exige)
    out = d.assign(categoria=np.where(sin, "sin dato", cat), orden=orden, cerca_del_umbral=cerca & ~sin, faltan_graduados=np.where(sin, np.nan, faltan).round(0),
                   umbral_base=u["base"], umbral_especifico=u["especifico"], referencia=u["referencia"])
    out["rango_orden"] = out["orden"].rank(ascending=False, method="min")
    return out


def sensibilidad(sector: str, exige: bool, prox: pd.DataFrame, por_sector: pd.DataFrame, industrias: pd.DataFrame) -> pd.DataFrame:
    """Cuántos distritos hay en cada categoría y cuántos cambian de categoría frente al caso principal, con otros umbrales, escalas y escenario de sede."""
    variantes = [("principal: 30 km, sede principal, productores", ESCALA, "principal", "productores"),
                 ("umbral en la mediana de todos los distritos", ESCALA, "principal", "mediana"),
                 ("escala de 15 km", 15, "principal", "productores"), ("escala de 60 km", 60, "principal", "productores"),
                 ("reparto parejo entre sedes", ESCALA, "parejo", "productores")]
    claves = ["dep", "clave"]
    filas, base = [], None
    for nombre, escala, esc, ref in variantes:
        d = diagnostico(ficha(sector, exige, prox, por_sector, industrias, escala, esc), exige, ref)
        if base is None:
            base = d.set_index(claves)["categoria"]
        cambia = int((d.set_index(claves)["categoria"] != base).sum())
        fila = {"variante": nombre, "cambian_de_categoria_frente_al_principal": cambia, "umbral_base": round(float(d["umbral_base"].iloc[0]), 1),
                "umbral_especifico": round(float(d["umbral_especifico"].iloc[0]), 1)}
        fila.update({c: int((d["categoria"] == c).sum()) for c in (*CATEGORIAS, "sin dato")})
        filas.append(fila)
    return pd.DataFrame(filas)


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
        exige = e["exige_formacion"] == "si"
        d = ficha(sector, exige, prox, por_sector, ind)
        d.to_csv(RAIZ / "data" / "model" / f"ejemplo_ficha_{sector}.csv", index=False, encoding="utf-8")
        dg = diagnostico(d, exige)
        dg.to_csv(RAIZ / "data" / "model" / f"ejemplo_diagnostico_{sector}.csv", index=False, encoding="utf-8")
        s = sensibilidad(sector, exige, prox, por_sector, ind)
        s.to_csv(RAIZ / "data" / "model" / f"ejemplo_sensibilidad_{sector}.csv", index=False, encoding="utf-8")
        print()
        print(f"== {sector} {e['nombre']}: NBER {e['habilidades']} -> exige={e['exige_formacion']} | referencia: {dg['referencia'].iloc[0]} ({int(umbrales(d)['n_productores'])} productores)")
        print(f"umbrales: base {dg['umbral_base'].iloc[0]:.0f}, formación específica {dg['umbral_especifico'].iloc[0]:.0f}")
        print(f"control frente a la población: {control_vs_poblacion(d)}")
        print(s.to_string(index=False))


if __name__ == "__main__":
    main()
