"""Prototipo de ficha de brechas: ¿en qué dotaciones está Paraguay por debajo de quienes ya producen el producto X?

Para un producto HS4 y un año, compara el percentil de Paraguay en cada dotación (entre los países D8 con dato) con el percentil mediano de:
- todos los productores (presencia D13: RCA ≥ 1 en 2 de los 3 años de calendario que terminan en alguno de los 5 años hasta t), Paraguay excluido;
- los productores de ingreso parecido al de Paraguay (mismo tercio de PIB per cápita), para separar la dotación del desarrollo;
- la vecindad del producto en el espacio producto: los productos con mayor proximidad φ (D3), con el peso de φ, cada uno con su mediana de productores.
La brecha es la referencia menos el percentil de Paraguay, en puntos de percentil (positiva = Paraguay está por debajo). Es un benchmark descriptivo: no prueba que cerrar
la brecha lleve a producir (el backtest no encontró que las dotaciones predigan las entradas). No incluye salarios ni régimen de maquila, que importan para arneses.

Uso: uv run python -m src.modelos.ficha_brechas
"""
from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

from src.modelos.bloques_dotaciones import terciles
from src.modelos.densidad_np import densidad, matriz_presencia, proximidad
from src.modelos.logit_nacional import CLEAN, MODELO, calcular_rca, paises_elegibles, presencia

PAIS = "PRY"
CAPAS = {  # columna de dotaciones -> nombre
    "hc": "Capital humano", "log_capital_trabajador": "Capital por trabajador", "lpi": "Logística (LPI)", "menos_log_precio": "Electricidad barata",
    "menos_log_salario": "Mano de obra barata", "log_tierra": "Tierra cultivable", "log_agua": "Agua dulce", "pib_pc_ppa": "PIB per cápita (referencia)",
}
MIN_PRODUCTORES = 5
VECINOS = 15
PRODUCTOS = {"8544": "Arneses y cables aislados (HS 8544)", "2207": "Etanol (HS 2207)"}


def percentiles(dot: pd.DataFrame, columnas: list[str]) -> pd.DataFrame:
    """Percentil (0 a 100) de cada país en cada dotación, entre los países de la tabla con dato."""
    p = dot.set_index("iso3")[columnas].rank(pct=True) * 100
    return p


def mediana_productores(pct: pd.DataFrame, productores: set[str], excluir: str = PAIS) -> tuple[pd.Series, int]:
    """Mediana del percentil de los productores (sin `excluir`) en cada dotación y cuántos productores hay."""
    idx = [i for i in productores if i in pct.index and i != excluir]
    return (pct.loc[idx].median() if idx else pd.Series(np.nan, index=pct.columns)), len(idx)


def ficha(expo: pd.DataFrame, dot: pd.DataFrame, pob: pd.DataFrame, hs4: str, anio: int, vecinos: int = VECINOS) -> dict:
    """Tabla de brechas de Paraguay para `hs4` en `anio`, con las tres referencias, las confianzas y la vecindad usada."""
    muestra = paises_elegibles(expo, pob, anio)
    rca = calcular_rca(expo)
    rca_m = rca[rca.iso3.isin(muestra)]
    pres = presencia(rca_m, anio)
    columnas = list(CAPAS)
    d = dot[(dot.anio == anio) & dot.iso3.isin(muestra)][["iso3", *columnas]]
    pct = percentiles(d, columnas)
    ingreso = terciles(d.set_index("iso3").pib_pc_ppa)
    prod = set(pres[pres.hs4 == hs4].iso3)
    todos, n_todos = mediana_productores(pct, prod)
    pares = {i for i in prod if i in ingreso.index and ingreso.get(i) == ingreso.get(PAIS)}
    peers, n_peers = mediana_productores(pct, pares)
    m, paises, productos = matriz_presencia(pres.rename(columns={"iso3": "country", "hs4": "product"}))
    phi = proximidad(m)
    vec, mediana_vec, n_vec = [], pd.Series(0.0, index=columnas), 0
    if hs4 in productos:
        j = int(np.searchsorted(productos, hs4))
        orden = np.argsort(phi[j])[::-1][:vecinos]
        pesos_tot = 0.0
        acum = pd.Series(0.0, index=columnas)
        for k in orden:
            if phi[j, k] <= 0:
                continue
            md, n_k = mediana_productores(pct, set(pres[pres.hs4 == productos[k]].iso3))
            if n_k < MIN_PRODUCTORES or md.isna().all():
                continue
            acum, pesos_tot = acum + md.fillna(0) * phi[j, k], pesos_tot + phi[j, k]
            vec.append((str(productos[k]), float(phi[j, k]), n_k))
        mediana_vec = acum / pesos_tot if pesos_tot > 0 else pd.Series(np.nan, index=columnas)
        n_vec = len(vec)
    py = pct.loc[PAIS]
    tabla = pd.DataFrame({"dotacion": [CAPAS[c] for c in columnas], "columna": columnas, "paraguay": py.to_numpy(),
                          "productores": todos.to_numpy(), "productores_ingreso_parecido": peers.to_numpy(), "vecindad": mediana_vec.to_numpy()})
    for ref in ("productores", "productores_ingreso_parecido", "vecindad"):
        tabla[f"brecha_{ref}"] = tabla[ref] - tabla.paraguay
    dens, dens_pct = np.nan, np.nan
    if PAIS in paises and hs4 in productos:
        fila = densidad(m, phi)[list(paises).index(PAIS)]
        sin = m[list(paises).index(PAIS)] == 0  # los productos que Paraguay todavía no tiene con presencia
        dens = float(fila[int(np.searchsorted(productos, hs4))])
        dens_pct = float((fila[sin] <= dens).mean() * 100)
    return {"hs4": hs4, "anio": anio, "tabla": tabla, "n_productores": n_todos, "n_peers": n_peers, "n_vecinos": n_vec, "vecinos": vec, "densidad": dens, "densidad_percentil": dens_pct,
            "tercio_ingreso": ingreso.get(PAIS), "productores": sorted(prod - {PAIS}),
            "confianza": "alta" if min(n_todos, n_peers, n_vec) >= MIN_PRODUCTORES else ("media" if n_todos >= MIN_PRODUCTORES else "baja")}


def trayectoria(expo: pd.DataFrame, hs4: str, anios=(2005, 2010, 2012, 2014, 2016, 2018, 2020, 2022, 2024)) -> pd.DataFrame:
    """Exportaciones (miles de USD) y RCA de Paraguay en el producto, por año."""
    r = calcular_rca(expo)
    r = r[(r.iso3 == PAIS) & (r.hs4 == hs4)].set_index("anio")
    return pd.DataFrame({"anio": list(anios), "exportaciones": [float(r.x.get(a, 0.0)) for a in anios], "rca": [float(r.rca.get(a, 0.0)) for a in anios]})


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--expo", default=str(MODELO / "exportaciones_hs4.parquet"))
    args = ap.parse_args(argv)
    expo = pd.read_parquet(args.expo)
    dot = pd.read_parquet(CLEAN / "dotaciones.parquet")
    pob = pd.read_csv(CLEAN / "poblacion_pais.csv")
    for hs4 in PRODUCTOS:  # noqa: PLC0206
        filas = []
        for anio in (2010, 2015):
            f = ficha(expo, dot, pob, hs4, anio)
            print(f"\n=== {PRODUCTOS[hs4]} · {anio}: {f['n_productores']} productores, {f['n_peers']} de ingreso parecido, {f['n_vecinos']} vecinos; "
                  f"densidad de Paraguay {f['densidad']:.3f}; confianza {f['confianza']}")
            print(f["tabla"].drop(columns="columna").round(0).to_string(index=False))
            print("vecinos:", [(v, round(p, 2)) for v, p, _ in f["vecinos"][:8]])
            filas.append(f["tabla"].assign(hs4=hs4, anio=anio, n_productores=f["n_productores"], n_peers=f["n_peers"], n_vecinos=f["n_vecinos"]))
        pd.concat(filas).to_csv(MODELO / f"ficha_brechas_{hs4}.csv", index=False)


if __name__ == "__main__":
    main()
