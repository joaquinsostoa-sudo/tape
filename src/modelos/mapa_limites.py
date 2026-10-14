"""Mapa de brechas con relevancia revelada: límite duro, déficit ponderado y exceso (declarado en docs/supuestos.md el 2026-10-14, antes de correr).

- Relevancia de la dotación k para el producto p: rel = |2·AUC − 1|, con AUC de la posición del país en k para separar quienes tienen presencia en p de quienes no; signo + si AUC > 0,5.
- Límite duro (país, p, k): k relevante (rel ≥ REL_ALTA) con signo +, y el país por debajo del percentil 10 de las posiciones de los productores (sin él).
- Exceso: en las dotaciones irrelevantes (rel < REL_BAJA), max(0, posición − mediana de los productores sin el país); índice = promedio.
- Déficit ponderado = Σ rel·brecha / Σ rel sobre las dotaciones con signo +. Compatible = sin límite duro y déficit ≤ percentil 75 entre los pares ya productores del tercio de ingreso.
- Prueba del exceso: logit de presencia con densidad y exceso, efectos fijos de país y de producto, errores agrupados por país (éxito: coeficiente < 0 con p < 0,05).
Descriptivo, no causal. Uso: uv run python -m src.modelos.mapa_limites
"""
from __future__ import annotations

import argparse
import warnings

import numpy as np
import pandas as pd
from scipy.stats import rankdata
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold

from src.modelos.bloques_dotaciones import dotaciones_del_anio, terciles
from src.modelos.densidad_np import densidad, matriz_presencia, proximidad
from src.modelos.logit_disperso import LogitEfectosFijos
from src.modelos.logit_nacional import (
    CLEAN,
    MODELO,
    calcular_rca,
    paises_elegibles,
    presencia,
    sin_variacion,
)
from src.modelos.mapa_brechas import (
    CAPAS,
    MINIMO,
    PAIS,
    PISO_TOLERANCIA,
    auc_por_pais,
    brechas,
    posiciones,
    referencias,
)
from src.modelos.recursos import MINERALES, USGS, participacion_reservas

REL_ALTA = 0.5
REL_BAJA = 0.2
PCT_LIMITE = 10
CAPA_MINERAL = "riqueza_mineral"  # en la variante específica, la reserva del mineral propio del producto
PROP_PRODUCTORES_AUSENCIA = 0.75
ANIO = 2019


def relevancia(pct: np.ndarray, m: np.ndarray, minimo: int = MINIMO) -> tuple[np.ndarray, np.ndarray]:
    """Relevancia (productos × dotaciones) = |2·AUC − 1| y signo (+1 / −1) de la posición para separar productores de no productores; vacía con menos de `minimo` productores o sin no productores."""
    n_p, k = m.shape[1], pct.shape[-1]
    rel, signo = np.full((n_p, k), np.nan), np.ones((n_p, k))
    for p in range(n_p):
        y = m[:, p] == 1
        base = pct if pct.ndim == 2 else pct[:, p, :]
        for j in range(k):
            ok = ~np.isnan(base[:, j])
            a, yy = base[ok, j], y[ok]
            n1, n0 = int(yy.sum()), int((~yy).sum())
            if n1 < minimo or n0 == 0:
                continue
            auc = (rankdata(a)[yy].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)  # Mann-Whitney, empates con rango medio
            rel[p, j], signo[p, j] = abs(2 * auc - 1), 1.0 if auc >= 0.5 else -1.0
    return rel, signo


def limites_duros(pct_pais: np.ndarray, pct: np.ndarray, m: np.ndarray, i: int, rel: np.ndarray, signo: np.ndarray, minimo: int = MINIMO) -> np.ndarray:
    """Límite duro del país `i` (productos × dotaciones, booleano): dotación relevante con signo + y país bajo el percentil `PCT_LIMITE` de los productores (sin él)."""
    n_p, k = rel.shape
    out = np.zeros((n_p, k), bool)
    for p in range(n_p):
        s = np.flatnonzero(m[:, p])
        s = s[s != i]
        if len(s) < minimo:
            continue
        base = pct if pct.ndim == 2 else pct[:, p, :]
        propio = pct_pais if pct_pais.ndim == 1 else pct_pais[p]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            q = np.nanpercentile(base[s], PCT_LIMITE, axis=0)
        out[p] = (rel[p] >= REL_ALTA) & (signo[p] > 0) & (propio < q)
    return out


def exceso_indice(pct: np.ndarray, ref: np.ndarray, rel: np.ndarray) -> np.ndarray:
    """Índice de exceso (países × productos): promedio de max(0, posición − referencia) en las dotaciones irrelevantes con dato; vacío si no hay ninguna."""
    ex = np.maximum(0.0, (pct[:, None, :] if pct.ndim == 2 else pct) - ref)
    ex = np.where((rel < REL_BAJA)[None, :, :], ex, np.nan)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        return np.nanmean(ex, axis=2)


def deficit_ponderado(gap: np.ndarray, rel: np.ndarray, signo: np.ndarray) -> np.ndarray:
    """Déficit ponderado (países × productos) = Σ rel·brecha / Σ rel sobre dotaciones con signo + y dato; 0 si ninguna pesa."""
    w = np.where(signo > 0, np.nan_to_num(rel), 0.0)[None, :, :] * ~np.isnan(gap)
    num = (w * np.nan_to_num(gap)).sum(axis=2)
    den = w.sum(axis=2)
    return np.where(den > 0, num / np.where(den > 0, den, 1.0), 0.0)


def probar_exceso(m: np.ndarray, dens: np.ndarray, exc: np.ndarray, paises: list[str], productos: list[str], extra: np.ndarray | None = None) -> pd.DataFrame:
    """Logit de presencia con densidad y exceso (estandarizados), efectos fijos de país y producto, errores agrupados por país."""
    df = pd.DataFrame({"iso3": np.repeat(paises, len(productos)), "hs4": np.tile(productos, len(paises)), "y": m.ravel(), "dens": dens.ravel(), "exc": exc.ravel()})
    cols = ["dens", "exc"]
    if extra is not None:
        df["extra"] = extra.ravel()
        cols = ["dens", "extra"]
    df = df.dropna(subset=cols)
    for c in cols:
        df[c] = (df[c] - df[c].mean()) / df[c].std()
    d = sin_variacion(df, "y", ["iso3", "hs4"])
    mod = LogitEfectosFijos(cols, ["iso3", "hs4"], C=None).ajustar(d, "y")
    tabla = mod.errores_agrupados(d, "y", "iso3")
    tabla["filas"], tabla["paises"] = len(d), d.iso3.nunique()
    return tabla


def validar(m: np.ndarray, dens: np.ndarray, deficit: np.ndarray, paises: list[str]) -> pd.DataFrame:
    """AUC medio entre países (y de Paraguay) de la densidad, de −déficit y del logit densidad + déficit con país dejado afuera."""
    n_c, n_p = m.shape
    grupos, y = np.repeat(np.arange(n_c), n_p), m.ravel()

    def dentro(a: np.ndarray) -> np.ndarray:
        s = a.std(axis=1, keepdims=True)
        return ((a - a.mean(axis=1, keepdims=True)) / np.where(s == 0, 1.0, s)).ravel()

    filas = []
    i = paises.index(PAIS) if PAIS in paises else None
    for nombre, puntaje in (("densidad", dens), ("menos déficit ponderado", -deficit)):
        a = auc_por_pais(m, puntaje)
        filas.append({"puntaje": nombre, "auc_promedio_paises": float(np.nanmean(a)), "auc_paraguay": float(a[i]) if i is not None else np.nan})
    for nombre, x in (("logit: densidad", np.column_stack([dentro(dens)])), ("logit: densidad + déficit ponderado", np.column_stack([dentro(dens), dentro(deficit)]))):
        pred = np.zeros(len(y))
        for tr, te in GroupKFold(5).split(x, y, grupos):
            pred[te] = LogisticRegression(max_iter=500).fit(x[tr], y[tr]).predict_proba(x[te])[:, 1]
        a = auc_por_pais(m, pred.reshape(n_c, n_p))
        filas.append({"puntaje": nombre + " (países dejados afuera)", "auc_promedio_paises": float(np.nanmean(a)), "auc_paraguay": float(a[i]) if i is not None else np.nan})
    return pd.DataFrame(filas)


def pct_especifico(pct: np.ndarray, paises: list[str], productos: list[str], minerales: pd.DataFrame, k: int) -> tuple[np.ndarray, np.ndarray]:
    """Posiciones (países × productos × dotaciones) donde la capa `k` es, para los productos de `MINERALES`, el percentil de la participación del país en las reservas de SU mineral
    (ausente = 0) y vacía en los demás productos; las otras capas se repiten. Devuelve también la participación (países × productos; vacía fuera de los minerales)."""
    pct3 = np.repeat(pct[:, None, :], len(productos), axis=1).copy()
    share = np.full((len(paises), len(productos)), np.nan)
    pct3[:, :, k] = np.nan
    tabla = minerales.pivot_table(index="iso3", columns="commodity", values="share", aggfunc="sum").reindex(paises).fillna(0.0)
    for p, hs4 in enumerate(productos):
        mineral = MINERALES.get(hs4)
        if mineral is None or mineral not in tabla.columns:
            continue
        share[:, p] = tabla[mineral].to_numpy()
        pct3[:, p, k] = pd.Series(share[:, p]).rank(pct=True).to_numpy() * 100
    return pct3, share


def limite_ausencia(share: np.ndarray, m: np.ndarray, i: int, minimo: int = MINIMO, prop: float = PROP_PRODUCTORES_AUSENCIA) -> np.ndarray:
    """Productos (booleano) donde el país `i` no tiene reservas del mineral y al menos `prop` de los productores (sin él) sí."""
    out = np.zeros(share.shape[1], bool)
    for p in range(share.shape[1]):
        if np.isnan(share[i, p]) or share[i, p] > 0:
            continue
        s = np.flatnonzero(m[:, p])
        s = s[s != i]
        out[p] = len(s) >= minimo and float((share[s, p] > 0).mean()) >= prop
    return out


def construir(expo: pd.DataFrame, dot: pd.DataFrame, pob: pd.DataFrame, puente: pd.DataFrame, anio: int = ANIO, pais: str = PAIS, minerales: pd.DataFrame | None = None) -> dict:
    """Todo el análisis para `pais` en `anio`."""
    dot = dotaciones_del_anio(dot, pob, puente, anio)
    muestra = paises_elegibles(expo, pob, anio)
    rca = calcular_rca(expo)
    pres = presencia(rca[rca.iso3.isin(muestra)], anio)
    m, paises, productos = matriz_presencia(pres.rename(columns={"iso3": "country", "hs4": "product"}))
    paises, productos = [str(p) for p in paises], [str(p) for p in productos]
    dens = densidad(m, proximidad(m))
    pct = posiciones(dot, paises, anio).to_numpy(np.float32)
    share = None
    if minerales is not None:  # variante: reserva del mineral específico de cada producto
        pct, share = pct_especifico(pct, paises, productos, minerales, list(CAPAS).index(CAPA_MINERAL))
    pib = dot[dot.iso3.isin(paises)].set_index("iso3").reindex(paises).pib_pc_ppa
    grupo = terciles(pib).reindex(paises).map({"bajo": 0, "medio": 1, "alto": 2}).fillna(-1).to_numpy(int)
    ref = referencias(pct, m, grupo)["todos"]
    gap = brechas(pct, ref)
    rel, signo = relevancia(pct, m)
    exc = exceso_indice(pct, ref, rel)
    deficit = deficit_ponderado(gap, rel, signo)
    i = paises.index(pais)
    duro = limites_duros(pct[i], pct, m, i, rel, signo)
    ausencia = np.zeros(len(productos), bool)
    if share is not None:
        ausencia = limite_ausencia(share, m, i)
        duro[:, list(CAPAS).index(CAPA_MINERAL)] |= ausencia
    misma = (grupo == grupo[i])[:, None] & (m == 1)
    tol = max(float(np.nanpercentile(deficit[misma], 75)), PISO_TOLERANCIA)
    capas = list(CAPAS)
    tabla = pd.DataFrame({"hs4": productos, "presencia": m[i].astype(bool), "densidad": dens[i], "deficit_ponderado": deficit[i], "exceso": exc[i], "n_limites_duros": duro.sum(axis=1)})
    tabla["limite_ausencia_mineral"] = ausencia
    tabla["limite_duro"] = [", ".join(CAPAS[capas[j]] for j in np.flatnonzero(f)) for f in duro]
    tabla["compatible"] = (tabla.n_limites_duros == 0) & (tabla.deficit_ponderado <= tol)
    r = rca[(rca.anio == anio) & (rca.iso3 == pais)].set_index("hs4").rca
    tabla["rca"] = tabla.hs4.map(r).fillna(0.0)
    no_exporta = (~tabla.presencia) & (tabla.rca < 0.5)
    corte = tabla.loc[no_exporta, "densidad"].quantile(0.75)
    tabla["cercano_no_exportado"] = no_exporta & (tabla.densidad >= corte)
    relev = pd.DataFrame({"dotacion": [CAPAS[c] for c in capas], "productos_relevantes": (rel >= REL_ALTA).sum(axis=0), "productos_irrelevantes": (rel < REL_BAJA).sum(axis=0),
                          "rel_mediana": np.nanmedian(rel, axis=0), "pct_signo_positivo": 100 * (signo > 0).mean(axis=0)})
    k_tierra = capas.index("log_tierra")
    pk = pct[:, k_tierra][:, None] if pct.ndim == 2 else pct[:, :, k_tierra]
    exc_tierra = np.where((rel[:, k_tierra] < REL_BAJA)[None, :], np.maximum(0.0, pk - ref[:, :, k_tierra]), np.nan)
    return {"tabla": tabla, "relevancia": relev, "tolerancia": tol, "corte": float(corte), "paises": len(paises), "productos": len(productos),
            "prueba": probar_exceso(m, dens, exc, paises, productos), "prueba_tierra": probar_exceso(m, dens, exc, paises, productos, extra=exc_tierra),
            "validacion": validar(m, dens, deficit, paises)}


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--expo", default=str(MODELO / "exportaciones_hs4.parquet"))
    ap.add_argument("--anio", type=int, default=ANIO)
    ap.add_argument("--pais", default=PAIS)
    ap.add_argument("--especifico", action="store_true", help="reserva del mineral específico de cada producto en lugar de la riqueza mineral total")
    a = ap.parse_args(argv)
    puente = pd.read_csv(CLEAN / "puente_paises_baci.csv")
    minerales = None
    if a.especifico:
        usgs = participacion_reservas(pd.read_csv(USGS, low_memory=False, encoding="cp1252"), puente)
        minerales = usgs[usgs.commodity.isin(set(MINERALES.values()))]
    r = construir(pd.read_parquet(a.expo), pd.read_parquet(CLEAN / "dotaciones.parquet"), pd.read_csv(CLEAN / "poblacion_pais.csv"), puente, a.anio, a.pais, minerales)
    t = r["tabla"]
    print(f"{a.pais} {a.anio}: {r['paises']} países, {r['productos']} productos; tolerancia del déficit ponderado: {r['tolerancia']:.1f}")
    print("\nRelevancia revelada por dotación:\n" + r["relevancia"].round(2).to_string(index=False))
    print("\nPrueba del exceso (logit con efectos fijos):\n" + r["prueba"].round(4).to_string(index=False))
    print("\nPrueba con el exceso de tierra solo:\n" + r["prueba_tierra"].round(4).to_string(index=False))
    print("\nValidación:\n" + r["validacion"].round(3).to_string(index=False))
    p, q = t[t.presencia], t[t.cercano_no_exportado]
    print(f"\nControl de sensatez: {100 * p.compatible.mean():.0f} % de las exportaciones actuales de {a.pais} son compatibles ({int(p.compatible.sum())} de {len(p)}); con límite duro: {int((p.n_limites_duros > 0).sum())}")
    print(f"Cercanos no exportados: {len(q)}; compatibles {int(q.compatible.sum())}; con límite duro {int((q.n_limites_duros > 0).sum())}; sin límite pero con déficit alto {int(((q.n_limites_duros == 0) & ~q.compatible).sum())}")
    sufijo = "_especifico" if a.especifico else ""
    mi = t[t.hs4.isin(set(MINERALES))]
    print(f"\nProductos minerales ({len(mi)}): con límite duro {int((mi.n_limites_duros > 0).sum())}, por ausencia de reservas {int(mi.limite_ausencia_mineral.sum())}; exportaciones actuales de {a.pais} marcadas: {int((t.presencia & (t.n_limites_duros > 0)).sum())}")
    print(mi[mi.hs4.isin(["2602", "2606", "2603", "2510", "2528"])][["hs4", "limite_duro", "compatible"]].to_string(index=False))
    t.to_csv(MODELO / f"mapa_limites{sufijo}_{a.pais}_{a.anio}.csv", index=False)
    r["relevancia"].to_csv(MODELO / f"mapa_limites_relevancia{sufijo}_{a.anio}.csv", index=False)


if __name__ == "__main__":
    main()
