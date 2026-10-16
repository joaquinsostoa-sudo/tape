"""¿Qué tan bien predice la densidad territorial por sí sola? (D34, declarada antes de correr en `docs/supuestos.md`).

Prueba principal, en cada fuente por separado (Censo Económico 2011 con φ ≤ 2010 y mapa MIC 2026 con φ ≤ 2024): AUC de la densidad para predecir la presencia de un sector en un distrito
sobre todas las celdas distrito × sector, contra dos bases simples: prevalencia del sector en los otros distritos y tamaño del distrito (establecimientos sin contar el sector).
**Criterio (Joaquín):** AUC(densidad) − AUC(base) ≥ 0,03 contra cada una de las dos bases, con intervalo del 95 % (remuestreo de distritos, 1.000 repeticiones, semilla 42) que excluya el cero,
en las dos fuentes. Descriptivo: AUC-PR, precisión entre los 3 sectores de mayor densidad de cada distrito, AUC dentro del distrito y la presencia alternativa (al menos una unidad).
Secundario, con advertencia: entradas 2010 → 2026. Las bases se calculan una vez con la muestra completa y el remuestreo es de distritos (sus celdas viajan juntas).

Uso: uv run python -m src.fase2.prueba_densidad
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import rankdata
from sklearn.metrics import average_precision_score

from src.fase2.densidad_territorial import densidad, phi_sectores
from src.fase2.presencia import SECTORES, fuentes_comunes, presencia_alterna, presencia_lq
from src.puentes.taxonomia_tape import RAIZ

SALIDA = RAIZ / "data" / "model" / "prueba_densidad_territorial.csv"
CELDAS = RAIZ / "data" / "model"
N_BOOT = 1000
SEMILLA = 42
MEJORA_MINIMA = 0.03


def auc(puntaje: np.ndarray, y: np.ndarray) -> float:
    """AUC (probabilidad de que una celda presente tenga mayor puntaje que una ausente; los empates cuentan la mitad). NaN si falta una de las dos clases."""
    y = np.asarray(y).astype(bool).ravel()
    n1, n0 = int(y.sum()), int((~y).sum())
    if n1 == 0 or n0 == 0:
        return float("nan")
    r = rankdata(np.asarray(puntaje, dtype=float).ravel())
    return float((r[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def bases(pres: pd.DataFrame, e: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Puntajes de las dos bases simples: prevalencia del sector en los OTROS distritos y tamaño del distrito sin contar el sector."""
    n = len(pres)
    p = pres.astype(float)
    prev = (p.sum(axis=0).to_numpy()[None, :] - p.to_numpy()) / (n - 1)
    tam = e.sum(axis=1).to_numpy()[:, None] - e.to_numpy()
    return {"prevalencia": pd.DataFrame(prev, index=pres.index, columns=pres.columns), "tamano": pd.DataFrame(tam, index=pres.index, columns=pres.columns)}


def intervalo(valores: np.ndarray) -> tuple[float, float]:
    """Percentiles 2,5 y 97,5 de las repeticiones."""
    v = valores[~np.isnan(valores)]
    return float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))


def comparar(y: pd.DataFrame, puntajes: dict[str, pd.DataFrame], mascara: pd.DataFrame | None = None, n_boot: int = N_BOOT, semilla: int = SEMILLA) -> pd.DataFrame:
    """AUC de cada puntaje, y la diferencia de la densidad con cada base, con intervalo por remuestreo de distritos. `mascara` limita las celdas (por ejemplo las ausentes en 2010)."""
    m = np.ones(y.shape, dtype=bool) if mascara is None else mascara.to_numpy(dtype=bool)
    Y = y.to_numpy(dtype=float)
    S = {k: v.to_numpy(dtype=float) for k, v in puntajes.items()}

    def evaluar(idx: np.ndarray) -> dict[str, float]:
        mm, yy = m[idx].ravel(), Y[idx].ravel()
        a = {k: auc(v[idx].ravel()[mm], yy[mm]) for k, v in S.items()}
        for base in [k for k in S if k != "densidad"]:
            a[f"dif_{base}"] = a["densidad"] - a[base]
        return a

    punto = evaluar(np.arange(len(Y)))
    rng = np.random.default_rng(semilla)
    reps = [evaluar(rng.integers(0, len(Y), len(Y))) for _ in range(n_boot)]
    filas = []
    for k, v in punto.items():
        lo, hi = intervalo(np.array([r[k] for r in reps]))
        filas.append({"metrica": f"auc_{k}", "valor": v, "ic_inf": lo, "ic_sup": hi})
    return pd.DataFrame(filas)


def cumple(tabla: pd.DataFrame) -> bool:
    """Criterio de D34 en una fuente: la densidad supera a cada base en al menos 0,03 de AUC con el intervalo del 95 % por encima de cero."""
    d = tabla[tabla["metrica"].str.startswith("auc_dif_")]
    return bool(len(d) > 0 and ((d["valor"] >= MEJORA_MINIMA) & (d["ic_inf"] > 0)).all())


def descriptivos(y: pd.DataFrame, dens: pd.DataFrame) -> dict[str, float]:
    """AUC-PR y tasa base; precisión entre los 3 sectores de mayor densidad de cada distrito contra la tasa base del distrito; AUC medio dentro del distrito."""
    Y, Dd = y.to_numpy(dtype=bool), dens.to_numpy(dtype=float)
    precis, tasas, aucs = [], [], []
    for i in range(len(Y)):
        if Y[i].sum() == 0 or Y[i].sum() == Y.shape[1]:
            continue
        top = np.argsort(-Dd[i], kind="stable")[:3]
        precis.append(Y[i][top].mean())
        tasas.append(Y[i].mean())
        aucs.append(auc(Dd[i], Y[i]))
    return {"tasa_base": float(Y.mean()), "auc_pr": float(average_precision_score(Y.ravel(), Dd.ravel())), "precision_top3": float(np.mean(precis)),
            "tasa_base_distrito": float(np.mean(tasas)), "lift_top3": float(np.mean(precis) / np.mean(tasas)), "auc_dentro_del_distrito": float(np.nanmean(aucs)),
            "distritos_evaluados": float(len(precis))}


def prueba_fuente(nombre: str, e: pd.DataFrame, phi: pd.DataFrame, presencia, tag: str) -> tuple[pd.DataFrame, dict[str, float]]:
    """Prueba de una fuente con una definición de presencia: tabla de AUC y diferencias, y descriptivos."""
    pres = presencia(e)
    dens = densidad(pres, phi)
    b = bases(pres, e)
    tabla = comparar(pres, {"densidad": dens, **b})
    desc = descriptivos(pres, dens)
    tabla.insert(0, "prueba", tag)
    tabla.insert(1, "fuente", nombre)
    return tabla, desc


def main() -> None:
    censo, mic = fuentes_comunes()
    phi10, phi24 = phi_sectores(2010, SECTORES), phi_sectores(2024, SECTORES)
    print(f"unidades comunes: {len(censo)} | sectores: {censo.shape[1]} | φ ≤ 2010 y ≤ 2024")
    tablas, desc_filas = [], []
    definiciones = {"principal (LQ > 1,5)": (presencia_lq, presencia_lq), "alterna (al menos una unidad)": (lambda e: presencia_alterna(e, 1.0), lambda e: presencia_alterna(e, 0.5))}
    veredicto = {}
    for etiqueta, (pc, pm) in definiciones.items():
        for nombre, e, phi, pres_f in (("censo 2010", censo, phi10, pc), ("MIC 2026", mic, phi24, pm)):
            t, d = prueba_fuente(nombre, e, phi, pres_f, etiqueta)
            tablas.append(t)
            desc_filas.append({"prueba": etiqueta, "fuente": nombre, **d})
            veredicto[(etiqueta, nombre)] = cumple(t)
    # secundario: entradas 2010 -> 2026
    p10, p26 = presencia_lq(censo), presencia_lq(mic)
    dens10 = densidad(p10, phi10)
    b10 = bases(p10, censo)
    ausentes = ~p10
    t = comparar(p26, {"densidad": dens10, **b10}, mascara=ausentes)
    t.insert(0, "prueba", "secundaria: entradas 2010→2026 (celdas ausentes en 2010)")
    t.insert(1, "fuente", "censo 2010 → MIC 2026")
    tablas.append(t)
    ent = (ausentes & p26)
    desc_filas.append({"prueba": "secundaria: entradas", "fuente": "censo 2010 → MIC 2026", "tasa_base": float(ent.values.sum() / ausentes.values.sum()), "entradas": float(ent.values.sum()),
                       "celdas_ausentes_2010": float(ausentes.values.sum())})
    out = pd.concat(tablas, ignore_index=True)
    out.round(4).to_csv(SALIDA, index=False, encoding="utf-8")
    pd.DataFrame(desc_filas).round(4).to_csv(CELDAS / "prueba_densidad_territorial_descriptivos.csv", index=False, encoding="utf-8")
    pd.set_option("display.width", 220)
    print("\n== AUC (valor; IC 95 %)")
    print(out.round(3).to_string(index=False))
    print("\n== descriptivos")
    print(pd.DataFrame(desc_filas).round(3).to_string(index=False))
    principal = [veredicto[("principal (LQ > 1,5)", f)] for f in ("censo 2010", "MIC 2026")]
    print(f"\n== CRITERIO D34 (presencia principal): censo 2010 {'SÍ' if principal[0] else 'NO'} | MIC 2026 {'SÍ' if principal[1] else 'NO'} -> "
          f"{'la densidad PREDICE BIEN según lo declarado' if all(principal) else 'la densidad NO cumple lo declarado: se pasa al diagnóstico'}")


if __name__ == "__main__":
    main()
