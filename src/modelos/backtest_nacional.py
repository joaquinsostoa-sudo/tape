"""Backtest fuera de muestra del modelo nacional (tarea 1.11, D2 a).

Para cada ventana de prueba t0 se entrena solo con las ventanas cuyo resultado ya se conocía en t0 (es decir,
v + h ≤ t0), y se predice la entrada de t0 a t0 + h. Efectos fijos de país y de producto constantes entre ventanas
(más un indicador de ventana) y penalización suave (C = 10), de modo que los países y productos sin entradas en el
pasado reciben un efecto finito. La densidad se estandariza con la media y el desvío del entrenamiento.

Modelos comparados sobre las mismas filas (países con todas las capas):
- `azar`: la tasa de entrada de la ventana de prueba (línea base de precisión).
- `densidad_cruda`: ordenar por densidad, sin modelo.
- `prior_producto`: tasa histórica de entrada de cada producto en el entrenamiento.
- `densidad_sola`: logit con densidad y efectos fijos (la comparación que exige la regla del proyecto).
- `capas`: el mismo logit más las interacciones r·a de las capas (D15).

Métricas: precision@k por país (la lista corta de cada país, promedio entre países con al menos una entrada) y
agrupada, AUC-PR, Brier. Incertidumbre: bootstrap por país de las diferencias contra `densidad_sola`.
Sesgos que no se corrigen (anacronismos aceptados): requisitos con la tecnología de EE. UU. de 2012-2018 (D4), precio de la
electricidad 2014-2019 aplicado a todos los años, LPI de 2007 hacia atrás en 2000 y 2005 (D14).

Uso: uv run python -m src.modelos.backtest_nacional  (usa data/model/exportaciones_hs4.parquet)
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from src.modelos.evaluacion import auc_pr, precision_at_k
from src.modelos.logit_disperso import LogitEfectosFijos
from src.modelos.logit_nacional import (
    CAPAS_PRINCIPALES,
    CLEAN,
    ESPECIFICACIONES,
    MODELO,
    VENTANAS,
    H,
    construir_datos,
)

EFECTOS = ["iso3", "hs4", "anio"]
KS_PAIS = (10, 20)
KS_AGRUPADO = (100, 500)
REPETICIONES = 300


def ventanas_previas(t_prueba: int, ventanas=VENTANAS, h: int = H) -> list[int]:
    """Ventanas de entrenamiento: las que ya tenían su resultado (t0 + h) conocido en `t_prueba`."""
    return [v for v in ventanas if v + h <= t_prueba]


def estandarizar_densidad(entrenamiento: pd.DataFrame, prueba: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """`d_z` con la media y el desvío del entrenamiento (nada de la ventana de prueba entra en la escala)."""
    mu, sd = entrenamiento.densidad.mean(), entrenamiento.densidad.std()
    return (entrenamiento.assign(d_z=(entrenamiento.densidad - mu) / sd),
            prueba.assign(d_z=(prueba.densidad - mu) / sd))


def prior_producto(entrenamiento: pd.DataFrame, prueba: pd.DataFrame) -> np.ndarray:
    """Tasa de entrada histórica del producto en el entrenamiento; productos nunca vistos, la tasa general."""
    tasa = entrenamiento.groupby("hs4").E.mean()
    return prueba.hs4.map(tasa).fillna(entrenamiento.E.mean()).to_numpy()


def ajustar_y_predecir(entrenamiento: pd.DataFrame, prueba: pd.DataFrame, columnas: list[str], C: float = 10.0) -> np.ndarray:
    m = LogitEfectosFijos(columnas, EFECTOS, C=C).ajustar(entrenamiento, "E")
    return m.predecir(prueba)


def precision_por_pais(prueba: pd.DataFrame, puntaje: np.ndarray, k: int) -> pd.Series:
    """precision@k dentro de cada país (la lista corta de cada uno), solo países con al menos una entrada."""
    d = prueba[["iso3", "hs4", "E"]].assign(s=puntaje)
    d = d[d.groupby("iso3").E.transform("sum") > 0]
    return d.groupby("iso3").apply(lambda g: precision_at_k(g.E.to_numpy(), g.s.to_numpy(), k), include_groups=False)


def intervalo_bootstrap(diferencias: np.ndarray, reps: int = REPETICIONES, semilla: int = 0) -> tuple[float, float, float]:
    """Media de las diferencias por país y su intervalo del 95 % por remuestreo de países."""
    rng = np.random.default_rng(semilla)
    n = len(diferencias)
    medias = rng.choice(diferencias, size=(reps, n), replace=True).mean(axis=1)
    return float(diferencias.mean()), float(np.quantile(medias, 0.025)), float(np.quantile(medias, 0.975))


def auc_pr_bootstrap(prueba: pd.DataFrame, a: np.ndarray, b: np.ndarray, reps: int = 200, semilla: int = 0) -> tuple[float, float, float]:
    """AUC-PR(a) − AUC-PR(b) con intervalo del 95 % por remuestreo de países."""
    rng = np.random.default_rng(semilla)
    grupos = {p: idx for p, idx in prueba.reset_index(drop=True).groupby("iso3").indices.items()}
    paises = np.array(list(grupos))
    y = prueba.E.to_numpy()
    dif = []
    for _ in range(reps):
        idx = np.concatenate([grupos[p] for p in rng.choice(paises, size=len(paises), replace=True)])
        if y[idx].sum() == 0:
            continue
        dif.append(auc_pr(y[idx], a[idx]) - auc_pr(y[idx], b[idx]))
    return auc_pr(y, a) - auc_pr(y, b), float(np.quantile(dif, 0.025)), float(np.quantile(dif, 0.975))


def evaluar_ventana(df: pd.DataFrame, t_prueba: int, capas: dict = CAPAS_PRINCIPALES, h: int = H, ventanas=VENTANAS) -> dict:
    """Entrena con las ventanas previas, predice `t_prueba` y devuelve puntajes y tablas de la ventana."""
    cols_capas = ["d_z", *(f"ra_{c}" for c in capas)]
    previas = ventanas_previas(t_prueba, ventanas, h)
    base = df.dropna(subset=["densidad", *cols_capas[1:]])
    ent, pru = estandarizar_densidad(base[base.anio.isin(previas)], base[base.anio == t_prueba])
    puntajes = {
        "azar": np.full(len(pru), ent.E.mean()),
        "densidad_cruda": pru.densidad.to_numpy(),
        "prior_producto": prior_producto(ent, pru),
        "densidad_sola": ajustar_y_predecir(ent, pru, ["d_z"]),
        "capas": ajustar_y_predecir(ent, pru, cols_capas),
    }
    return {"entrenamiento": ent, "prueba": pru, "puntajes": puntajes, "ventanas_previas": previas}


def resumen_ventana(res: dict, t_prueba: int) -> list[dict]:
    pru, p = res["prueba"], res["puntajes"]
    y = pru.E.to_numpy()
    filas = []
    por_pais = {nombre: {k: precision_por_pais(pru, s, k) for k in KS_PAIS} for nombre, s in p.items() if nombre != "azar"}
    for nombre, s in p.items():
        fila = {"ventana": t_prueba, "modelo": nombre, "filas": len(pru), "entradas": int(y.sum()), "paises": pru.iso3.nunique(),
                "tasa_base": float(y.mean())}
        for k in KS_AGRUPADO:
            fila[f"p_{k}"] = precision_at_k(y, s, k) if nombre != "azar" else float(y.mean())
        fila["auc_pr"] = auc_pr(y, s) if nombre != "azar" else float(y.mean())
        if nombre in por_pais:
            for k in KS_PAIS:
                fila[f"p_pais_{k}"] = float(por_pais[nombre][k].mean())
        fila["brier"] = float(np.mean((y - s) ** 2)) if nombre not in ("azar", "densidad_cruda") else np.nan
        filas.append(fila)
    return filas


def calibracion_deciles(y: np.ndarray, s: np.ndarray) -> pd.DataFrame:
    """Probabilidad predicha media y frecuencia real de entrada por decil de la probabilidad predicha."""
    d = pd.DataFrame({"y": y, "s": s})
    d["decil"] = pd.qcut(d.s.rank(method="first"), 10, labels=False) + 1
    return d.groupby("decil").agg(predicho=("s", "mean"), real=("y", "mean"), n=("y", "size")).reset_index()


def comparar_con_densidad_sola(res: dict, modelos=("capas", "prior_producto"), base: str = "densidad_sola") -> list[dict]:
    """Diferencias de cada modelo contra `base` (por defecto `densidad_sola`), con intervalo por remuestreo de países."""
    pru, p = res["prueba"], res["puntajes"]
    filas = []
    for contra in modelos:
        for k in KS_PAIS:
            a, b = precision_por_pais(pru, p[contra], k), precision_por_pais(pru, p[base], k)
            dif = (a - b).dropna().to_numpy()
            m, lo, hi = intervalo_bootstrap(dif)
            filas.append({"modelo": contra, "metrica": f"p_pais_{k}", "dif": m, "ic_inf": lo, "ic_sup": hi})
        m, lo, hi = auc_pr_bootstrap(pru, p[contra], p[base])
        filas.append({"modelo": contra, "metrica": "auc_pr", "dif": m, "ic_inf": lo, "ic_sup": hi})
    return filas


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--expo", default=str(MODELO / "exportaciones_hs4.parquet"))
    ap.add_argument("--salida", default=str(MODELO / "backtest_resultados.csv"))
    args = ap.parse_args(argv)
    expo = pd.read_parquet(Path(args.expo))
    dot = pd.read_parquet(CLEAN / "dotaciones.parquet")
    req = pd.read_csv(CLEAN / "requisitos_producto_hs4.csv", dtype={"hs4": str})
    pob = pd.read_csv(CLEAN / "poblacion_pais.csv")
    df = construir_datos(expo, dot, req, pob)
    assert set(ESPECIFICACIONES["capas"]) <= set(df.columns)
    resumen, difs, calibraciones = [], [], []
    for t in (v for v in VENTANAS if ventanas_previas(v)):
        res = evaluar_ventana(df, t)
        print(f"\n=== Prueba {t} → {t + H}: entrenamiento con {res['ventanas_previas']} ({len(res['entrenamiento']):,} filas), "
              f"prueba {len(res['prueba']):,} filas, {int(res['prueba'].E.sum())} entradas, {res['prueba'].iso3.nunique()} países")
        filas = resumen_ventana(res, t)
        resumen += filas
        print(pd.DataFrame(filas).drop(columns=["ventana", "filas", "paises"]).round(3).to_string(index=False))
        d = pd.DataFrame(comparar_con_densidad_sola(res)).assign(ventana=t)
        difs.append(d)
        print(d.round(3).to_string(index=False))
        cal = calibracion_deciles(res["prueba"].E.to_numpy(), res["puntajes"]["capas"]).assign(ventana=t)
        calibraciones.append(cal)
        print("calibración de `capas` por decil (predicho / real):",
              ", ".join(f"{p:.3f}/{r:.3f}" for p, r in zip(cal.predicho, cal.real, strict=True)))
    pd.concat(calibraciones).to_csv(str(args.salida).replace(".csv", "_calibracion.csv"), index=False)
    pd.DataFrame(resumen).to_csv(args.salida, index=False)
    pd.concat(difs).to_csv(str(args.salida).replace(".csv", "_diferencias.csv"), index=False)
    print(f"\n-> {args.salida}")


if __name__ == "__main__":
    main()
