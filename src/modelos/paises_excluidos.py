"""Países excluidos comparables a Paraguay (prueba B de la declaración del 2026-10-14 en docs/supuestos.md).

En cada ventana de prueba t0 (2005, 2010, 2015) se eligen los 10 países de la muestra con el PIB per cápita PPA (log, estandarizado en la ventana) más cercano al de Paraguay, sin Paraguay;
se los **retira del entrenamiento** (de todas las ventanas previas) y se predicen con el modelo tipo Mundlak de `mundlak.py` (sin efecto fijo de país: densidad, densidad media del país y del producto,
con y sin las capas), entrenado con el resto. El único dato de los retenidos usado para elegirlos es su PIB de t0.
Control: 10 países retenidos al azar de la misma ventana (20 sorteos, semilla fija). Además se reporta Paraguay retenido solo.

Criterios declarados: B1: la precision@20 por país de la densidad en los comparables retenidos, agrupando las tres ventanas, es ≥ 2,0 veces su tasa base. B2: el intervalo del 95 % (remuestreo de
países-ventana) de capas − densidad en precision@20 incluye el cero.

Uso: uv run python -m src.modelos.paises_excluidos
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

from src.modelos import backtest_nacional as bt
from src.modelos import mundlak as mk
from src.modelos.logit_nacional import CLEAN, MODELO, VENTANAS, H, construir_datos

N_RETENIDOS = 10
SORTEOS = 20
SEMILLA = 20261014
K = 20
PAIS = "PRY"
MODELOS = {"mundlak_densidad": mk.COLS_DENS, "mundlak_capas": mk.COLS_DENS + mk.COLS_A + mk.COLS_R + mk.COLS_RA}


def comparables(prueba: pd.DataFrame, n: int = N_RETENIDOS, pais: str = PAIS) -> list[str]:
    """Los `n` países con el PIB (columna `a_pib`) más cercano al de `pais` en la ventana, sin él; orden estable por distancia y luego por código."""
    p = prueba.drop_duplicates("iso3").set_index("iso3").a_pib
    if pais not in p.index:
        raise KeyError(f"{pais} no está en la ventana")
    d = (p.drop(pais) - p[pais]).abs().rename("d").reset_index().sort_values(["d", "iso3"])
    return d.iso3.head(n).tolist()


def sorteo(prueba: pd.DataFrame, rng: np.random.Generator, n: int = N_RETENIDOS, pais: str = PAIS) -> list[str]:
    """`n` países al azar de la ventana, sin `pais`."""
    p = sorted(set(prueba.iso3) - {pais})
    return sorted(rng.choice(p, size=n, replace=False).tolist())


def predecir_retenidos(res: dict, retenidos: list[str], C: float = 1.0) -> tuple[pd.DataFrame, dict[str, np.ndarray]]:
    """Entrena los modelos Mundlak sin los `retenidos` y los predice; devuelve las filas de prueba de los retenidos y sus puntajes."""
    ent = mk.agregar_medias(res["entrenamiento"][~res["entrenamiento"].iso3.isin(retenidos)])
    pru = mk.agregar_medias(res["prueba"])
    cols = sorted({c for cs in MODELOS.values() for c in cs})
    ent, pru = mk.estandarizar(ent, pru, cols)
    marca = pru.iso3.isin(retenidos).to_numpy()
    puntajes = {}
    for nombre, cs in MODELOS.items():
        m = LogisticRegression(C=C, max_iter=2000).fit(ent[cs].to_numpy(), ent.E.to_numpy())
        puntajes[nombre] = m.predict_proba(pru.loc[marca, cs].to_numpy())[:, 1]
    return pru[marca].reset_index(drop=True), puntajes


def metricas_por_pais(filas: pd.DataFrame, puntajes: dict[str, np.ndarray], k: int = K) -> pd.DataFrame:
    """Por país retenido con al menos una entrada: precision@k de cada modelo y su tasa base."""
    base = filas.groupby("iso3").E.mean().rename("base")
    out = pd.concat({n: bt.precision_por_pais(filas, s, k) for n, s in puntajes.items()}, axis=1)
    return out.join(base)


def resumen(m: pd.DataFrame) -> dict[str, float]:
    """Medias entre países-ventana de la precision@k y la tasa base, y el «lift» (cociente entre las medias) de cada modelo."""
    base = float(m.base.mean())
    r = {"paises_ventana": len(m), "tasa_base": base}
    for n in MODELOS:
        r[f"p20_{n}"] = float(m[n].mean())
        r[f"lift_{n}"] = float(m[n].mean() / base) if base > 0 else float("nan")
    return r


def main() -> None:
    import sys

    sys.stdout.reconfigure(encoding="utf-8")
    df = construir_datos(pd.read_parquet(MODELO / "exportaciones_hs4_depurado.parquet"), pd.read_parquet(CLEAN / "dotaciones.parquet"),
                         pd.read_csv(CLEAN / "requisitos_producto_hs4.csv", dtype={"hs4": str}), pd.read_csv(CLEAN / "poblacion_pais.csv"))
    rng = np.random.default_rng(SEMILLA)
    comp, azar, pry = [], [], []
    for t in (v for v in VENTANAS if bt.ventanas_previas(v)):
        res = bt.evaluar_ventana(df, t)
        ret = comparables(res["prueba"])
        print(f"\n=== Ventana {t} → {t + H}: comparables retenidos: {', '.join(ret)}")
        filas, sc = predecir_retenidos(res, ret)
        comp.append(metricas_por_pais(filas, sc).assign(ventana=t))
        for _ in range(SORTEOS):
            f, s = predecir_retenidos(res, sorteo(res["prueba"], rng))
            azar.append(metricas_por_pais(f, s).assign(ventana=t))
        f, s = predecir_retenidos(res, [PAIS])
        mp = metricas_por_pais(f, s)
        print(f"Paraguay retenido: entradas {int(f.E.sum())} de {len(f)} candidatos; precision@{K} densidad {mp['mundlak_densidad'].mean() if len(mp) else float('nan'):.3f}, capas {mp['mundlak_capas'].mean() if len(mp) else float('nan'):.3f}")
        top = f.assign(s=s["mundlak_densidad"]).nlargest(K, "s")
        print("  entradas de Paraguay en su lista de 20 (densidad):", top[top.E == 1].hs4.tolist())
        pry.append(mp.assign(ventana=t))
    c = pd.concat(comp)
    rc = resumen(c)
    dif = (c.mundlak_capas - c.mundlak_densidad).to_numpy()
    m, lo, hi = bt.intervalo_bootstrap(dif)
    a = pd.concat(azar)
    ra = resumen(a)
    print(f"\nCOMPARABLES (3 ventanas, {rc['paises_ventana']} países-ventana con entradas): tasa base {rc['tasa_base']:.3f}; p@{K} densidad {rc['p20_mundlak_densidad']:.3f} (lift {rc['lift_mundlak_densidad']:.2f}), "
          f"capas {rc['p20_mundlak_capas']:.3f} (lift {rc['lift_mundlak_capas']:.2f})")
    print(f"capas − densidad en p@{K}: {m:+.4f} (IC 95 % {lo:+.4f}; {hi:+.4f})")
    print(f"AL AZAR ({SORTEOS} sorteos): tasa base {ra['tasa_base']:.3f}; p@{K} densidad {ra['p20_mundlak_densidad']:.3f} (lift {ra['lift_mundlak_densidad']:.2f}), capas {ra['p20_mundlak_capas']:.3f} (lift {ra['lift_mundlak_capas']:.2f})")
    print(f"B1 (lift de la densidad ≥ 2,0 en comparables): {'cumplida' if rc['lift_mundlak_densidad'] >= 2.0 else 'NO cumplida'}; B2 (el IC incluye el cero): {'cumplida' if lo <= 0 <= hi else 'NO cumplida'}")
    c.to_csv(MODELO / "paises_excluidos_comparables.csv")
    a.to_csv(MODELO / "paises_excluidos_azar.csv")
    pd.concat(pry).to_csv(MODELO / "paises_excluidos_paraguay.csv")


if __name__ == "__main__":
    main()
