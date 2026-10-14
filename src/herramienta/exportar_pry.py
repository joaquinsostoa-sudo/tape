"""Exporta los datos de la herramienta de Paraguay (mapa de productos, lista y ficha por producto) a un JSON para el prototipo.

Toma `mapa_limites.construir(..., minerales)` (variante con reserva del mineral específico y reservas de energía solo para los productos-recurso) y agrega: coordenadas del espacio producto
(disposición de fuerzas sobre los vecinos más próximos de la matriz φ), productores principales, vecinos que el país ya exporta y las 12 dotaciones por producto.
Descriptivo: la brecha es respecto de los productores, no una probabilidad de éxito.

Uso: uv run python -m src.herramienta.exportar_pry
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from src.figuras.mapa_limites import nombres
from src.modelos.logit_nacional import CLEAN, MODELO, RAIZ
from src.modelos.mapa_brechas import CAPAS
from src.modelos.mapa_limites import ANIO, MINERALES, PAIS, USGS, construir, participacion_reservas
from src.modelos.oportunidades import eci_pais, escalera, leer_atlas

SALIDA = MODELO / f"herramienta_{PAIS}_{ANIO}.json"
VECINOS = 4


def disposicion(phi: np.ndarray, k: int = VECINOS, iteraciones: int = 300, semilla: int = 0) -> np.ndarray:
    """Coordenadas 2D (n × 2, en [0, 1]) del espacio producto: cada producto se une a sus `k` vecinos de mayor proximidad; atracción por los enlaces y repulsión entre todos (Fruchterman-Reingold)."""
    n = phi.shape[0]
    w = np.nan_to_num(phi.astype(float))
    np.fill_diagonal(w, 0.0)
    a = np.zeros((n, n))
    for i in range(n):
        vec = np.argsort(-w[i])[:k]
        vec = vec[w[i, vec] > 0]
        a[i, vec] = w[i, vec]
    a = np.maximum(a, a.T)
    con = np.flatnonzero(a.sum(axis=1) > 0)
    sin = np.setdiff1d(np.arange(n), con)  # sin vecinos: no entran a la disposición, se ubican en un anillo alrededor
    rng = np.random.default_rng(semilla)
    ac = a[np.ix_(con, con)]
    m = len(con)
    pos = rng.normal(size=(m, 2)) * 0.1
    lado = np.sqrt(1.0 / max(m, 1))
    temp = 0.1
    for it in range(iteraciones):
        d = pos[:, None, :] - pos[None, :, :]
        dist = np.sqrt((d**2).sum(-1)) + 1e-9
        mov = ((lado**2 / dist**2)[..., None] * d - (ac / lado * dist)[..., None] * d).sum(axis=1)
        largo = np.sqrt((mov**2).sum(-1))[:, None] + 1e-9
        pos += mov / largo * np.minimum(largo, temp)
        temp = 0.1 * (1 - it / iteraciones) + 0.001
        pos -= pos.mean(axis=0)
    out = np.zeros((n, 2))
    out[con] = pos
    if len(sin):
        radio = 1.1 * np.sqrt((pos**2).sum(-1)).max() if m else 1.0
        ang = np.linspace(0, 2 * np.pi, len(sin), endpoint=False)
        out[sin] = np.column_stack([radio * np.cos(ang), radio * np.sin(ang)])
    out -= out.min(axis=0)
    return out / np.maximum(out.max(axis=0), 1e-9)


def _r(x: float, d: int = 1) -> float | None:
    return None if x is None or not np.isfinite(x) else round(float(x), d)


def exportar() -> dict:
    expo = pd.read_parquet(MODELO / "exportaciones_hs4.parquet")
    puente = pd.read_csv(CLEAN / "puente_paises_baci.csv")
    usgs = participacion_reservas(pd.read_csv(USGS, low_memory=False, encoding="cp1252"), puente)
    r = construir(expo, pd.read_parquet(CLEAN / "dotaciones.parquet"), pd.read_csv(CLEAN / "poblacion_pais.csv"), puente, ANIO, PAIS, usgs[usgs.commodity.isin(set(MINERALES.values()))])
    z = r["interno"]
    t, productos, paises, i = r["tabla"], z["productos"], z["paises"], z["i"]
    xy = disposicion(z["phi"])
    bloques = pd.read_csv(CLEAN / "clasificacion_lall_hs4.csv", dtype={"hs4": str}).drop_duplicates("hs4").set_index("hs4")
    nom = nombres(largo=90, completo=True)
    valor = expo[expo.anio == ANIO].groupby("hs4").x.sum()
    pib = pd.read_parquet(CLEAN / "dotaciones.parquet").query("anio == @ANIO").set_index("iso3").pib_pc_ppa
    rca = z["rca"][z["rca"].iso3.isin(paises)]
    capas = list(CAPAS)
    exporta = np.flatnonzero(z["m"][i] == 1)
    atlas = leer_atlas(PAIS, ANIO).set_index("hs4")  # PCI y COG del Atlas (2019, el mismo año de la herramienta)
    esc = escalera(z["phi"], productos, [productos[j] for j in exporta], atlas.pci, k=4)
    esc_por_origen = {o: g for o, g in esc.groupby("origen")}
    prods = []
    for p, h in enumerate(productos):
        fila = t.iloc[p]
        top = rca[rca.hs4 == h].nlargest(6, "rca")
        prod_p = np.flatnonzero(z["m"][:, p] == 1)
        vec = [q for q in np.argsort(-np.nan_to_num(z["phi"][p])) if q != p and q in set(exporta)][:5]
        prods.append({
            "h": h, "n": str(nom.get(h, h)), "b": bloques.bloque.get(h, "sin_clasificar"), "e": fila.estado, "x": bool(fila.presencia), "c": bool(fila.cercano_no_exportado),
            "d": _r(fila.densidad, 3), "df": _r(fila.deficit_ponderado), "ex": _r(fila.exceso), "rca": _r(fila.rca, 2), "v": _r(valor.get(h, 0) / 1e6, 0),
            "np": len(prod_p), "px": _r(xy[p, 0], 4), "py": _r(xy[p, 1], 4),
            "cap": [[_r(z["pct"][i, p, j] if z["pct"].ndim == 3 else z["pct"][i, j]), _r(z["ref"][i, p, j]), _r(z["gap"][i, p, j]), _r(z["rel"][p, j], 2), int(z["signo"][p, j]), bool(z["duro"][p, j])] for j in range(len(capas))],
            "prod": [[x.iso3, _r(x.rca, 1), _r(pib.get(x.iso3, np.nan), 0)] for x in top.itertuples()],
            "vec": [[productos[q], str(nom.get(productos[q], productos[q])), _r(z["phi"][p, q], 2)] for q in vec],
            "pci": _r(atlas.pci.get(h, np.nan), 2), "cog": _r(atlas.cog.get(h, np.nan), 2),
            "up": [[r_.destino, str(nom.get(r_.destino, r_.destino)), _r(r_.phi, 2), _r(r_.pci_destino, 2)] for r_ in esc_por_origen[h].itertuples()] if h in esc_por_origen else []})
    e = eci_pais(PAIS)
    meta = {"eci": _r(e[e.anio == ANIO].eci.iloc[0], 2), "pci_canasta": _r(float(atlas.pci.reindex([productos[j] for j in exporta]).mean()), 2), "pais": PAIS, "anio": ANIO, "paises": r["paises"], "productos": r["productos"], "tolerancia": _r(r["tolerancia"]), "capas": [CAPAS[c] for c in capas],
            "auc_densidad": _r(float(r["validacion"].iloc[0].auc_promedio_paises), 3), "auc_con_deficit": _r(float(r["validacion"].iloc[3].auc_promedio_paises), 3)}
    return {"meta": meta, "productos": prods}


def main() -> None:
    d = exportar()
    SALIDA.write_text(json.dumps(d, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(SALIDA, f"{SALIDA.stat().st_size / 1e3:.0f} KB", len(d["productos"]), "productos;", RAIZ.name)


if __name__ == "__main__":
    main()
