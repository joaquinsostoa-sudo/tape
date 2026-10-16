"""Matcheo del capital humano para un bien cercano y más complejo que aún no se produce (D32).

Un bien que todavía no se produce no tiene productores de referencia; se los toma de los **vecinos** (los 5 productos presentes de Paraguay más próximos por φ) y se sube el umbral por el
**peldaño**: cuánto más requisito de habilidades (NBER) tiene el bien que sus vecinos.
1. Vecinos del bien y sector de cada uno (el de mayor peso en el puente HS → sector).
2. Referencia R: los distritos con industrias del mapa MIC en algún sector de los vecinos (si son menos de 10, la mediana de todos los distritos).
3. Peldaño: percentil del requisito del bien menos percentil del requisito medio de los vecinos, entre los productos con NBER; nunca negativo.
4. Umbrales: base = percentil 10 de R; formación específica del sector del bien = percentil 10 de R **más el peldaño** (tope 100). Categorías y orden como en D31.
5. Densidad territorial (D26 de `supuestos_fase2.md`): peso de los vecinos que el distrito ya produce (manufactura). Cruce con las categorías: candidato / qué desarrollar / capacidad sin uso / no es candidato.
Sensibilidad: B (sin peldaño), A (requisito propio del bien), escalas de 15 y 60 km y reparto parejo.

Es un diagnóstico y no una recomendación de localización. Salidas: `data/model/matcheo_<hs4>.csv` y `data/model/matcheo_<hs4>_sensibilidad.csv`.
Uso: uv run python -m src.puentes.matcheo_bien_nuevo
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..modelos.candidatos_sector import pesos_producto_sector
from ..modelos.logit_nacional import CLEAN, MODELO
from ..modelos.oportunidades import CORTE, PAIS, matriz_de_proximidad
from . import base_capital_humano as bc
from . import ejemplo_ch as ej
from .taxonomia_tape import RAIZ

CORTE_EXIGE = 0.28
K_VECINOS = 5
MIN_REFERENCIA = 10
PERCENTIL_UMBRAL = 0.10
EJEMPLOS = ("8430", "2202")
MANUFACTURA = {f"S{i:02d}" for i in range(9, 45)}


def percentil_requisito(valor: float, serie: pd.Series) -> float:
    """Percentil (0 a 100) de un requisito entre los productos con dato: porcentaje de productos con requisito estrictamente menor."""
    return float(100 * (serie.dropna() < valor).mean())


def vecinos(phi: np.ndarray, productos: list[str], presentes: list[str], bien: str, k: int = K_VECINOS) -> pd.DataFrame:
    """Los `k` productos presentes de Paraguay más próximos al bien (hs4 y φ), de mayor a menor φ; solo con φ positivo."""
    idx = {h: i for i, h in enumerate(productos)}
    pr = [h for h in presentes if h in idx and h != bien]
    f = np.nan_to_num(phi[idx[bien], [idx[h] for h in pr]].astype(float))
    orden = [j for j in np.argsort(-f)[:k] if f[j] > 0]
    return pd.DataFrame({"hs4": [pr[j] for j in orden], "phi": [float(f[j]) for j in orden]})


def peldano(req_bien: float, vec: pd.DataFrame, req: pd.Series) -> dict[str, float]:
    """Peldaño en puntos de percentil: percentil del requisito del bien menos el de los vecinos (media ponderada por φ de los que tienen dato). Sin dato de vecinos, 0."""
    v = vec.assign(h=vec["hs4"].map(req)).dropna(subset=["h"])
    pct_bien = percentil_requisito(req_bien, req)
    if v.empty or v["phi"].sum() <= 0:
        return {"paso": 0.0, "pct_bien": pct_bien, "pct_vecinos": float("nan"), "vecinos_con_dato": 0.0}
    pct_vec = percentil_requisito(float(np.average(v["h"], weights=v["phi"])), req)
    return {"paso": max(0.0, pct_bien - pct_vec), "pct_bien": pct_bien, "pct_vecinos": pct_vec, "vecinos_con_dato": float(len(v))}


def referencia(sectores_vecinos: set[str], presencia: dict[str, set[tuple[str, str]]], claves: list[tuple[str, str]]) -> np.ndarray:
    """Máscara de los distritos con industrias del mapa MIC en algún sector de los vecinos."""
    donde: set[tuple[str, str]] = set()
    for s in sectores_vecinos:
        donde |= presencia.get(s, set())
    return np.array([k in donde for k in claves])


def densidad(phi_bien: dict[str, float], sector_de: dict[str, str], presencia: dict[str, set[tuple[str, str]]], claves: list[tuple[str, str]]) -> np.ndarray:
    """Densidad territorial: Σ φ(bien, producto presente) × [el distrito tiene industria del sector del producto] / Σ φ, sobre los productos cuyo sector es de manufactura."""
    num = np.zeros(len(claves))
    den = 0.0
    for h, f in phi_bien.items():
        s = sector_de.get(h)
        if s not in MANUFACTURA or f <= 0:
            continue
        den += f
        num += f * np.array([k in presencia.get(s, set()) for k in claves])
    return num / den if den > 0 else np.full(len(claves), np.nan)


def umbrales_c(d: pd.DataFrame, mask: np.ndarray, paso: float) -> dict[str, float | str]:
    """Umbrales de la regla C: percentil 10 de la referencia (o mediana de todos si hay menos de 10 distritos); a la formación específica se le suma el peldaño (tope 100)."""
    ok = d.dropna(subset=["p_base", "p_especifico"])
    ref = d[mask].dropna(subset=["p_base", "p_especifico"])
    usar = len(ref) >= MIN_REFERENCIA
    base, q = (ref, PERCENTIL_UMBRAL) if usar else (ok, 0.5)
    return {"base": float(base["p_base"].quantile(q)), "especifico": float(min(100.0, base["p_especifico"].quantile(q) + paso)), "pool": float(base["pool"].quantile(q)),
            "referencia": f"distritos que producen los vecinos ({len(ref)}; percentil 10)" if usar else f"mediana de todos los distritos (la referencia tiene solo {len(ref)})",
            "n_referencia": float(len(ref))}


def cruce(categoria: pd.Series, dens: pd.Series, umbral_dens: float) -> pd.Series:
    """Candidato / qué desarrollar / capacidad sin uso / no es candidato, según haya densidad (produce bienes relacionados) y capital humano «lista»."""
    rel = (dens > 0) & (dens >= umbral_dens)
    lista = categoria == "lista"
    return pd.Series(np.select([rel & lista, rel & ~lista, ~rel & lista], ["candidato", "qué desarrollar", "capacidad sin uso"], "no es candidato"), index=categoria.index).where(categoria != "sin dato", "sin dato")


def evaluar(bien: str, ctx: dict, escala: int = ej.ESCALA, escenario: str = "principal", modo: str = "C") -> tuple[pd.DataFrame, dict[str, float | str]]:
    """Matcheo de un bien: ficha del sector, umbrales según el modo (C: vecinos y peldaño; B: sin peldaño; A: requisito propio) y categorías."""
    sector, req_bien = ctx["sector_de"][bien], float(ctx["req"][bien])
    exige = req_bien >= CORTE_EXIGE
    d = ej.ficha(sector, exige, ctx["prox"], ctx["por_sector"], ctx["ind"], escala, escenario)
    claves = list(zip(d["dep"], d["clave"], strict=True))
    vec = ctx["vecinos"][bien]
    paso = peldano(req_bien, vec, ctx["req"])
    mask = referencia({ctx["sector_de"][h] for h in vec["hs4"] if h in ctx["sector_de"]}, ctx["presencia"], claves)
    if modo == "A":
        pct = paso["pct_bien"]
        u = {"base": pct, "especifico": pct, "pool": float(d["pool"].median()), "referencia": "requisito propio del bien (regla A)", "n_referencia": float("nan")}
    else:
        u = umbrales_c(d, mask, paso["paso"] if (modo == "C" and exige) else 0.0)
    g = ej.diagnostico(d, exige, umbrales_dados=u)
    phi_b = dict(zip(ctx["presentes"], ctx["phi_bien"][bien], strict=True))
    g["densidad"] = densidad(phi_b, ctx["sector_de"], ctx["presencia"], claves)
    umbral_dens = float(np.nanmedian(g["densidad"]))
    g["cruce"] = cruce(g["categoria"], g["densidad"], umbral_dens)
    g["en_referencia"] = mask
    g.attrs.update({"paso": paso, "sector": sector, "exige": exige, "umbral_densidad": umbral_dens})
    return g, u


def contexto() -> dict:
    """Carga todo lo necesario una sola vez (la matriz de proximidad es lo más pesado)."""
    prox, por_sector, ind, exig = ej.cargar()
    expo = pd.read_parquet(MODELO / "exportaciones_hs4_depurado.parquet")
    phi, productos, presentes = matriz_de_proximidad(expo, pd.read_csv(CLEAN / "poblacion_pais.csv"), PAIS, CORTE)
    pu = pd.read_csv(CLEAN / "puente_hs92_sector.csv", dtype={"hs92": str})
    for c in ("peso", "valor_mundial"):
        pu[c] = pd.to_numeric(pu[c], errors="coerce")
    w = pesos_producto_sector(pu)
    sector_de = w.sort_values("w", ascending=False).drop_duplicates("hs4").set_index("hs4")["sector_id"].to_dict()
    req = pd.read_csv(CLEAN / "requisitos_producto_hs4.csv", dtype={"hs4": str}).set_index("hs4")["habilidades"].dropna()
    base = bc.distritos_base()
    mic = bc.a_clave_base(pd.read_parquet(CLEAN / "industrias_distrito_sector_tape.parquet"), "departamento", "distrito", base)
    mic = mic[mic["n_industrias"] > 0]
    presencia = {s: set(zip(g["dep"], g["clave"], strict=True)) for s, g in mic.groupby("sector_id")}
    idx = {h: i for i, h in enumerate(productos)}
    vec, phi_bien = {}, {}
    for b in EJEMPLOS:
        vec[b] = vecinos(phi, productos, presentes, b)
        phi_bien[b] = [float(np.nan_to_num(phi[idx[b], idx[h]])) if h in idx else 0.0 for h in presentes]
    return {"prox": prox, "por_sector": por_sector, "ind": ind, "exig": exig, "req": req, "sector_de": sector_de, "presencia": presencia, "presentes": presentes,
            "vecinos": vec, "phi_bien": phi_bien, "productos": productos}


def sensibilidad(bien: str, ctx: dict) -> pd.DataFrame:
    """Cuántos distritos hay en cada categoría y cuántos cambian frente al caso principal con otras reglas, escalas y escenario de sede."""
    variantes = [("principal: regla C, 30 km, sede principal", ej.ESCALA, "principal", "C"), ("regla B: sin peldaño", ej.ESCALA, "principal", "B"),
                 ("regla A: requisito propio del bien", ej.ESCALA, "principal", "A"), ("escala de 15 km", 15, "principal", "C"),
                 ("escala de 60 km", 60, "principal", "C"), ("reparto parejo entre sedes", ej.ESCALA, "parejo", "C")]
    filas, base = [], None
    for nombre, escala, esc, modo in variantes:
        g, u = evaluar(bien, ctx, escala, esc, modo)
        k = g.set_index(["dep", "clave"])
        if base is None:
            base = k["categoria"]
        fila = {"variante": nombre, "cambian_de_categoria": int((k["categoria"] != base).sum()), "umbral_base": round(float(u["base"]), 1), "umbral_formacion": round(float(u["especifico"]), 1)}
        fila.update({c: int((g["categoria"] == c).sum()) for c in (*ej.CATEGORIAS, "sin dato")})
        fila.update({f"cruce: {c}": int((g["cruce"] == c).sum()) for c in ("candidato", "qué desarrollar", "capacidad sin uso", "no es candidato")})
        filas.append(fila)
    return pd.DataFrame(filas)


def main() -> None:
    ctx = contexto()
    nombres = pd.read_csv(MODELO / "oportunidades_PRY_2024.csv", dtype={"hs4": str}).set_index("hs4")["nombre"]
    for bien in EJEMPLOS:
        g, u = evaluar(bien, ctx)
        p = g.attrs["paso"]
        vec = ctx["vecinos"][bien]
        print(f"\n===== {bien} {nombres.get(bien, '')[:60]} | sector {g.attrs['sector']} | NBER {ctx['req'][bien]:.3f} | exige={g.attrs['exige']}")
        print(f"vecinos: {[(r.hs4, round(r.phi, 2), ctx['sector_de'].get(r.hs4)) for r in vec.itertuples()]}")
        print(f"peldaño: bien p{p['pct_bien']:.0f} / vecinos p{p['pct_vecinos']:.0f} -> paso {p['paso']:.1f} puntos ({int(p['vecinos_con_dato'])} vecinos con dato)")
        print(f"referencia: {u['referencia']} | umbrales: base {u['base']:.0f}, formación {u['especifico']:.0f} | umbral de densidad {g.attrs['umbral_densidad']:.2f}")
        g.drop(columns=["rango_orden"], errors="ignore").to_csv(RAIZ / "data" / "model" / f"matcheo_{bien}.csv", index=False, encoding="utf-8")
        s = sensibilidad(bien, ctx)
        s.to_csv(RAIZ / "data" / "model" / f"matcheo_{bien}_sensibilidad.csv", index=False, encoding="utf-8")
        print(s.to_string(index=False))


if __name__ == "__main__":
    main()
