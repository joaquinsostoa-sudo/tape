"""Diagnóstico multi-capa por industria y distrito (D36): qué le falta a cada distrito frente a quienes ya producen el sector, y quién debe actuar.

Es una descripción de distancias, no una predicción ni una probabilidad (D16, D34). Reglas declaradas en `docs/supuestos.md` (D36):
- Capas que el sector exige: base de capital humano (siempre), formación específica (D28), energía y logística (D33), recursos (D35, solo con medida).
- Referencia: distritos con al menos una industria del sector en el mapa MIC 2026. Umbral = percentil 10 de los productores en cada capa; con menos de 5 productores el sector
  queda «sin referencia» en esa capa; con 5 a 9, confianza baja; con 10 o más, alta.
- Estado por capa según la brecha (índice del distrito menos umbral): sin brecha (≥ 0), cerca del umbral (de −10 a 0) o con brecha (< −10).
- Nivel de política: 0 mercado; 1 ajuste puntual (una brecha de formación o base de hasta 20 puntos); 2 acción colectiva (dos o más, o una de más de 20); 3 Estado (brecha de energía o
  logística). Una brecha de recursos es un límite duro: el distrito queda «no apto por recursos» y fuera del ranking.
- Orden (solo celdas con todas las capas evaluadas con dato en el distrito; si no, «datos incompletos»): apto por recursos, menos brechas (energía y logística juntas cuentan como una), mayor margen mínimo sobre el umbral. Sin puntaje único.
- Complejidad (informativa, no entra en el orden): PCI y COG del sector (percentil entre sectores) y escalón relativo = PCI del sector menos la mediana del PCI de los sectores del distrito.

Salidas (en `data/model/`): `diagnostico_multicapa.csv` (sector × distrito), `diagnostico_multicapa_referencias.csv` (umbral por sector y capa),
`diagnostico_multicapa_sensibilidad.csv` y `diagnostico_multicapa_control.csv`.
Uso: uv run python -m src.puentes.diagnostico_multicapa
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..modelos.candidatos_sector import pesos_producto_sector
from . import base_capital_humano as bc
from .taxonomia_tape import RAIZ

C = RAIZ / "data" / "clean"
M = RAIZ / "data" / "model"
CAPAS = ("base", "formacion", "energia", "logistica", "recursos")
ESCALA = 30
MIN_PRODUCTORES = 5
PRODUCTORES_ALTA = 10
PERCENTIL_UMBRAL = 0.10
BANDA = 10.0
CORTE_NIVEL = 20.0
SIN, CERCA, CON = "sin brecha", "cerca del umbral", "con brecha"


def estado(brecha: pd.Series, banda: float = BANDA) -> pd.Series:
    """Estado de una capa según la brecha (índice menos umbral): sin brecha si es ≥ 0, cerca del umbral si está dentro de la banda por debajo, con brecha si está más abajo. NaN → vacío."""
    e = np.where(brecha >= 0, SIN, np.where(brecha >= -banda, CERCA, CON))
    return pd.Series(np.where(brecha.isna(), "", e), index=brecha.index)


def umbral_referencia(indice: pd.Series, productor: pd.Series, referencia: str = "productores") -> tuple[float, int, str]:
    """Umbral de una capa, número de productores con dato y confianza. Con la referencia «productores»: percentil 10 de los productores; con menos de 5 es NaN («sin referencia»).
    Con «mediana»: mediana de todos los distritos con dato (sensibilidad). Confianza: alta con 10 o más productores, baja con 5 a 9, vacía si no hay referencia."""
    ok = indice.notna()
    n = int((productor & ok).sum())
    if n < MIN_PRODUCTORES:
        return np.nan, n, ""
    conf = "alta" if n >= PRODUCTORES_ALTA else "baja"
    if referencia == "mediana":
        return float(indice[ok].median()), n, conf
    return float(indice[productor & ok].quantile(PERCENTIL_UMBRAL)), n, conf


def nivel_politica(estados: dict[str, pd.Series], brechas: dict[str, pd.Series], corte: float = CORTE_NIVEL) -> pd.DataFrame:
    """Nivel de política (0 a 3) y si el distrito es apto por recursos. `estados` y `brechas` por capa; solo cuentan las capas evaluadas.
    3 si hay brecha de energía o logística; si no, 0 sin brechas, 1 con una sola brecha de formación o base de hasta `corte` puntos y 2 en los demás casos."""
    idx = next(iter(estados.values())).index
    con = {c: (e == CON) for c, e in estados.items()}
    cero = pd.Series(False, index=idx)
    infra = con.get("energia", cero) | con.get("logistica", cero)
    fb = [c for c in ("base", "formacion") if c in con]
    n_fb = sum((con[c].astype(int) for c in fb), start=pd.Series(0, index=idx))
    mag = pd.concat([(-brechas[c]).where(con[c]) for c in fb], axis=1).max(axis=1) if fb else pd.Series(np.nan, index=idx)
    nivel = np.select([infra, n_fb == 0, (n_fb == 1) & (mag <= corte)], [3, 0, 1], 2)
    return pd.DataFrame({"nivel": nivel, "apto_recursos": ~con.get("recursos", cero), "infraestructura_conjunta": con.get("energia", cero) & con.get("logistica", cero)}, index=idx)


def pci_cog_sector(oport: pd.DataFrame, pesos: pd.DataFrame, valor: pd.Series) -> pd.DataFrame:
    """PCI y COG por sector: media ponderada por el comercio mundial (D1: peso del HS4 en el sector por su valor mundial), solo con productos que tienen dato."""
    m = pesos.merge(oport[["hs4", "pci", "cog"]], on="hs4").assign(p=lambda d: d["w"] * d["hs4"].map(valor).fillna(0.0))
    filas = []
    for s, g in m.groupby("sector_id"):
        fila = {"sector_id": s}
        for c in ("pci", "cog"):
            h = g.dropna(subset=[c])
            fila[c] = float(np.average(h[c], weights=h["p"])) if len(h) and h["p"].sum() > 0 else np.nan
        filas.append(fila)
    return pd.DataFrame(filas)


def escalon(pci_pct: pd.Series, produce: pd.DataFrame) -> pd.DataFrame:
    """Escalón relativo de cada sector frente a cada distrito: percentil de PCI del sector menos la mediana de los percentiles de PCI de los sectores que el distrito produce.
    `produce` es una matriz distrito × sector de booleanos; devuelve la misma forma con el valor numérico (NaN sin dato)."""
    pct = pci_pct.reindex(produce.columns)
    med = produce.apply(lambda f: pct[f & pct.notna()].median() if (f & pct.notna()).any() else np.nan, axis=1)
    return pd.DataFrame(pct.to_numpy()[None, :] - med.to_numpy()[:, None], index=produce.index, columns=produce.columns)


def etiqueta_escalon(e: pd.Series, banda: float = BANDA) -> pd.Series:
    """«más complejo» si el escalón supera la banda, «menos complejo» si baja más que la banda, «similar» en medio; vacío sin dato."""
    return pd.Series(np.where(e.isna(), "", np.where(e > banda, "más complejo", np.where(e < -banda, "menos complejo", "similar"))), index=e.index)


def cargar() -> dict:
    """Todas las entradas, con los distritos alineados por (dep, clave)."""
    base = bc.distritos_base()
    prox = pd.read_csv(C / "proximidad_distrito.csv")
    prox["dep"] = [bc.departamento(v) for v in prox["departamento"]]
    prox["clave"] = [bc.llave(v) for v in prox["distrito"]]
    dot = pd.read_csv(C / "dotaciones_distrito.csv")
    dot["dep"] = [bc.departamento(v) for v in dot["departamento"]]
    dot["clave"] = [bc.llave(v) for v in dot["distrito"]]
    ind = bc.a_clave_base(pd.read_parquet(C / "industrias_distrito_sector_tape.parquet"), "departamento", "distrito", base)
    ind = ind[ind["sector_id"].astype(str).str.startswith("S")]
    grad = pd.read_csv(C / "proximidad_graduados_sector.csv")
    grad["dep"] = [bc.departamento(v) for v in grad["departamento"]]
    grad["clave"] = [bc.llave(v) for v in grad["distrito"]]
    exig = pd.read_csv(C / "exigencia_capas_sector.csv", dtype=str).fillna("")
    pu = pd.read_csv(C / "puente_hs92_sector.csv", dtype={"hs92": str})
    for c in ("peso", "valor_mundial"):
        pu[c] = pd.to_numeric(pu[c], errors="coerce")
    valor = pu.drop_duplicates("hs92").assign(hs4=lambda d: d["hs92"].str[:4]).groupby("hs4")["valor_mundial"].sum()
    oport = pd.read_csv(M / "oportunidades_PRY_2024.csv", dtype={"hs4": str})
    compl = pci_cog_sector(oport, pesos_producto_sector(pu), valor)
    return {"prox": prox, "dot": dot, "ind": ind, "grad": grad, "exig": exig, "complejidad": compl}


def indices_sector(fila: pd.Series, d: pd.DataFrame, grad: pd.DataFrame, escala: int, escenario: str) -> tuple[dict[str, pd.Series], list[str]]:
    """Índices (percentil 0-100) por capa que el sector exige, alineados con `d` (que trae los índices del distrito), y las capas exigidas sin medida («sin dato»)."""
    capas = {"base": d[f"indice_v2_{escala}_{escenario}"]}
    sin_dato: list[str] = []
    if fila["exige_formacion"] == "si":
        g = grad[(grad["sector_id"] == fila["sector_id"]) & (grad["escenario"] == escenario) & (grad["escala_km"] == escala)]
        if len(g):
            pool = d[["dep", "clave"]].merge(g[["dep", "clave", "pool"]], on=["dep", "clave"], how="left")["pool"].fillna(0.0)
            pool = pool.where(capas["base"].notna().to_numpy())
            capas["formacion"] = bc.percentil(pd.Series(pool.to_numpy(), index=d.index))
        else:
            sin_dato.append("formacion")
    if fila["exige_energia"] == "si":
        capas["energia"] = d[f"idx_energia_{escala}"]
    if fila["exige_logistica"] == "si":
        capas["logistica"] = d[f"idx_logistica_{escala}"]
    if fila["exige_recursos"] == "si":
        if fila["clase_tierra"]:
            capas["recursos"] = d[f"idx_recursos_{fila['clase_tierra']}_{escala}"]
        else:
            sin_dato.append("recursos")
    return capas, sin_dato


def construir(datos: dict, escala: int = ESCALA, escenario: str = "principal", referencia: str = "productores", banda: float = BANDA, corte: float = CORTE_NIVEL) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Matriz sector × distrito y tabla de referencias (umbral por sector y capa)."""
    d = datos["prox"][["dep", "clave", "departamento", "distrito", "poblacion", f"indice_v2_{escala}_{escenario}"]].merge(
        datos["dot"][["dep", "clave"] + [c for c in datos["dot"].columns if c.startswith("idx_") and c.endswith(f"_{escala}")]], on=["dep", "clave"], how="left").reset_index(drop=True)
    ind = datos["ind"].groupby(["sector_id", "dep", "clave"])["n_industrias"].sum().reset_index()
    ind = ind[ind["n_industrias"] > 0]
    produce_ref = {s: set(zip(g["dep"], g["clave"], strict=True)) for s, g in ind.groupby("sector_id")}
    llaves = list(zip(d["dep"], d["clave"], strict=True))
    comp = datos["complejidad"].set_index("sector_id")
    pci_pct = bc.percentil(comp["pci"].dropna()).reindex(comp.index)
    cog_pct = bc.percentil(comp["cog"].dropna()).reindex(comp.index)
    sectores = list(datos["exig"]["sector_id"])
    produce = pd.DataFrame({s: [k in produce_ref.get(s, set()) for k in llaves] for s in sectores}, index=d.index)
    esc = escalon(pci_pct, produce.loc[:, [s for s in sectores if s in pci_pct.index]])
    filas, refs = [], []
    for _, fila in datos["exig"].iterrows():
        s = fila["sector_id"]
        capas, sin_dato = indices_sector(fila, d, datos["grad"], escala, escenario)
        prod = produce[s]
        est, brec, evaluadas = {}, {}, {}
        for capa, idx in capas.items():
            umbral, n, conf = umbral_referencia(idx, prod, referencia)
            refs.append({"sector_id": s, "capa": capa, "n_productores": n, "umbral": round(umbral, 1) if not np.isnan(umbral) else np.nan,
                         "confianza": conf if conf else "sin referencia", "referencia": referencia})
            if np.isnan(umbral):
                continue
            brec[capa] = idx - umbral
            est[capa] = estado(brec[capa], banda)
            evaluadas[capa] = idx
        out = pd.DataFrame({"sector_id": s, "departamento": d["departamento"], "distrito": d["distrito"], "ya_produce": prod,
                            "capas_exigidas": ",".join(capas), "capas_sin_dato": ",".join(sin_dato), "capas_evaluadas": ",".join(evaluadas),
                            "n_capas_exigidas": len(capas), "n_capas_evaluadas": len(evaluadas), "n_productores_sector": int(prod.sum())})
        for capa in CAPAS:
            out[f"{capa}_indice"] = capas[capa].round(1) if capa in capas else np.nan
            out[f"{capa}_brecha"] = brec[capa].round(1) if capa in brec else np.nan
            out[f"{capa}_estado"] = est.get(capa, "")
        if evaluadas:
            niv = nivel_politica(est, brec, corte)
            con = pd.concat([(est[c] == CON).astype(int).rename(c) for c in est], axis=1)
            n_brechas = con.drop(columns=["recursos"], errors="ignore").sum(axis=1) - niv["infraestructura_conjunta"].astype(int)
            out["n_brechas"] = n_brechas.to_numpy()
            out["n_cerca"] = sum(((e == CERCA).astype(int) for c, e in est.items() if c != "recursos"), start=pd.Series(0, index=d.index)).to_numpy()
            out["margen_min"] = pd.concat(list(brec.values()), axis=1).min(axis=1).round(1).to_numpy()
            ev = pd.concat(list(evaluadas.values()), axis=1).set_axis(list(evaluadas), axis=1)
            out["capa_limitante"] = np.where(ev.isna().all(axis=1), "", ev.fillna(np.inf).idxmin(axis=1))
            out["infraestructura_conjunta"] = niv["infraestructura_conjunta"].to_numpy()
            out["apto_recursos"] = niv["apto_recursos"].to_numpy()
            out["nivel_politica"] = np.where(niv["apto_recursos"], niv["nivel"], np.nan)
            out["nivel_texto"] = np.where(~niv["apto_recursos"], "no apto por recursos (límite duro)", pd.Series(niv["nivel"]).map(
                {0: "0 mercado", 1: "1 ajuste puntual", 2: "2 acción colectiva", 3: "3 Estado"}))
        else:
            for c in ("n_brechas", "n_cerca", "margen_min", "capa_limitante", "infraestructura_conjunta", "apto_recursos", "nivel_politica"):
                out[c] = np.nan
            out["nivel_texto"] = "sin referencia"
        faltan = pd.concat([idx.isna().rename(c) for c, idx in evaluadas.items()], axis=1) if evaluadas else pd.DataFrame(index=d.index)
        out["capas_sin_dato_distrito"] = [",".join(c for c in faltan.columns if f[c]) for _, f in faltan.iterrows()] if evaluadas else ""
        out["datos_incompletos"] = out["capas_sin_dato_distrito"].ne("") if evaluadas else False
        out["confianza_referencia"] = "sin referencia" if not evaluadas else ("baja" if any(r["confianza"] == "baja" for r in refs[-len(capas):] if r["sector_id"] == s) else "alta")
        out["situacion"] = np.select(
            [~out["n_capas_evaluadas"].astype(bool), out["datos_incompletos"], out["ya_produce"], out["apto_recursos"].eq(False), out["n_brechas"].eq(0)],
            ["sin referencia", "datos incompletos", "ya se produce", "no apto por recursos", "oportunidad no realizada"], "no se produce, con brechas")
        sin_ficha = out["datos_incompletos"] & out["n_brechas"].eq(0)  # sin brechas conocidas pero con una capa sin dato: no se puede decir «mercado»
        out.loc[sin_ficha, ["nivel_texto", "nivel_politica"]] = ["datos incompletos", np.nan]
        out["pci_sector_pct"] = round(pci_pct.get(s, np.nan), 1)
        out["cog_sector_pct"] = round(cog_pct.get(s, np.nan), 1)
        out["escalon_pci"] = esc[s].round(1).to_numpy() if s in esc.columns else np.nan
        out["escalon_etiqueta"] = etiqueta_escalon(out["escalon_pci"], banda).to_numpy()
        filas.append(out)
    m = pd.concat(filas, ignore_index=True)
    ranquear = m["apto_recursos"].eq(True) & m["n_capas_evaluadas"].gt(0) & ~m["datos_incompletos"]
    m["clave_orden"] = np.where(ranquear, m["n_brechas"] * 1000.0 - m["margen_min"], np.nan)
    m["rango_en_industria"] = m.groupby("sector_id")["clave_orden"].rank(method="min")
    m["rango_en_distrito"] = m.groupby(["departamento", "distrito"])["clave_orden"].rank(method="min")
    return m.drop(columns="clave_orden"), pd.DataFrame(refs)


def sensibilidad(datos: dict) -> pd.DataFrame:
    """Cuántas celdas cambian de nivel de política frente al caso principal con otros umbrales, escalas, escenario de sede y tolerancias."""
    variantes = [("principal", {}), ("umbral en la mediana de todos los distritos", {"referencia": "mediana"}), ("escala de 15 km", {"escala": 15}), ("escala de 60 km", {"escala": 60}),
                 ("reparto parejo entre sedes", {"escenario": "parejo"}), ("banda de 5 puntos", {"banda": 5.0}), ("banda de 15 puntos", {"banda": 15.0}),
                 ("corte de nivel 1 en 10 puntos", {"corte": 10.0}), ("corte de nivel 1 en 30 puntos", {"corte": 30.0})]
    filas, base = [], None
    for nombre, kw in variantes:
        m, _ = construir(datos, **kw)
        clave = m["sector_id"] + "|" + m["distrito"] + "|" + m["departamento"]
        n = pd.Series(m["nivel_texto"].to_numpy(), index=clave.to_numpy())
        if base is None:
            base = n
        fila = {"variante": nombre, "celdas_que_cambian_de_nivel": int((n != base).sum())}
        fila.update({t: int((m["nivel_texto"] == t).sum()) for t in ("0 mercado", "1 ajuste puntual", "2 acción colectiva", "3 Estado", "no apto por recursos (límite duro)", "sin referencia")})
        fila["oportunidades_no_realizadas"] = int((m["situacion"] == "oportunidad no realizada").sum())
        filas.append(fila)
    return pd.DataFrame(filas)


def control(m: pd.DataFrame, refs: pd.DataFrame) -> pd.DataFrame:
    """Controles declarados: productores sin brecha por construcción, sectores sin referencia por capa y cuántas celdas hay en cada situación."""
    filas = []
    p = m[m["ya_produce"] & (m["n_capas_evaluadas"] > 0)]
    filas.append({"control": "productores evaluados sin ninguna brecha (por construcción cerca del 90 %)", "valor": round(float((p["n_brechas"] == 0).mean()) * 100, 1)})
    for capa in CAPAS:
        r = refs[refs["capa"] == capa]
        filas.append({"control": f"capa {capa}: sectores que la exigen / sin referencia", "valor": f"{len(r)} / {int((r['confianza'] == 'sin referencia').sum())}"})
        filas.append({"control": f"capa {capa}: referencias con confianza baja (5 a 9 productores)", "valor": int((r["confianza"] == "baja").sum())})
    for sit, n in m["situacion"].value_counts().items():
        filas.append({"control": f"celdas en la situación «{sit}»", "valor": int(n)})
    ev = m[m["n_capas_evaluadas"] > 0]
    filas.append({"control": "sectores con referencia y con una sola capa exigida (viables en casi todos lados)", "valor": int(ev[ev["n_capas_exigidas"] == 1]["sector_id"].nunique())})
    return pd.DataFrame(filas)


EJEMPLOS = ("S16", "S22")  # una industria con las cinco capas exigidas y una que solo exige la base


def fichas_ejemplo(m: pd.DataFrame, refs: pd.DataFrame) -> None:
    """Fichas de ejemplo por industria (vista por industria, ordenada) y una de distrito (vista por distrito) en `data/model/`."""
    for s in EJEMPLOS:
        x = m[m["sector_id"] == s].sort_values(["rango_en_industria", "distrito"], na_position="last")
        x.to_csv(M / f"diagnostico_multicapa_ficha_{s}.csv", index=False, encoding="utf-8")
        refs[refs["sector_id"] == s].to_csv(M / f"diagnostico_multicapa_ficha_{s}_referencias.csv", index=False, encoding="utf-8")
    x = m[m["distrito"] == "CIUDAD DEL ESTE"].sort_values(["rango_en_distrito", "sector_id"], na_position="last")
    x.to_csv(M / "diagnostico_multicapa_ficha_distrito_CIUDAD_DEL_ESTE.csv", index=False, encoding="utf-8")


def main() -> None:
    datos = cargar()
    m, refs = construir(datos)
    fichas_ejemplo(m, refs)
    m.to_csv(M / "diagnostico_multicapa.csv", index=False, encoding="utf-8")
    refs.to_csv(M / "diagnostico_multicapa_referencias.csv", index=False, encoding="utf-8")
    sen = sensibilidad(datos)
    sen.to_csv(M / "diagnostico_multicapa_sensibilidad.csv", index=False, encoding="utf-8")
    ctl = control(m, refs)
    ctl.to_csv(M / "diagnostico_multicapa_control.csv", index=False, encoding="utf-8")
    print(f"celdas {len(m)} | sectores {m['sector_id'].nunique()} | distritos {m.groupby(['departamento', 'distrito']).ngroups}")
    print(ctl.to_string(index=False))
    print(sen.to_string(index=False))


if __name__ == "__main__":
    main()
