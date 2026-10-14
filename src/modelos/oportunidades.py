"""Oportunidades de complejidad de un país: cercanía (densidad) × complejidad (PCI), con la ganancia de complejidad (COG) y la «escalera» de productos más complejos.

Decisiones (2026-10-14, a pedido del equipo): PCI y COG del Atlas de Complejidad Económica (último año disponible, HS92 a 4 dígitos); la cercanía es la densidad de TAPE (D3, tabla depurada de D6);
**dos ejes, sin fusionarlos en un puntaje único**: la cercanía es la que tiene respaldo predictivo (D16) y la complejidad es una medida de valor.
- Candidatos = productos sin presencia D13 y con RCA < 0,5 (los de `candidatos_sector.py`). Cuadrantes: *cercano* = densidad en el cuartil superior de los candidatos; *complejo* = PCI > 0 (el producto
  promedio del Atlas tiene PCI 0). Se leen: cercano y complejo (prioridad), cercano y simple (fácil, poco valor), lejano y complejo (apuesta), lejano y simple.
- Escalera de un producto que el país ya exporta (presencia D13): sus vecinos con la mayor proximidad φ y PCI mayor que el suyo; para un candidato, los productos actuales de Paraguay que lo vuelven alcanzable.
La mayor complejidad es una asociación, no una promesa: «te acerca a productos más complejos», no «sube tu ECI».

Uso: uv run python -m src.modelos.oportunidades [--pais PRY] [--corte 2024]
"""
from __future__ import annotations

import argparse

import duckdb
import numpy as np
import pandas as pd

from src.modelos.densidad_np import matriz_presencia, proximidad
from src.modelos.logit_nacional import (
    CLEAN,
    MODELO,
    RAIZ,
    calcular_rca,
    paises_elegibles,
    presencia,
)

ATLAS = RAIZ / "data" / "raw" / "atlas" / "hs92_country_product_year_4.csv"
ATLAS_PAIS = RAIZ / "data" / "raw" / "atlas" / "hs92_country_year.csv"
PAIS = "PRY"
CORTE = 2024
CUANTIL_CERCANO = 0.75
PCI_COMPLEJO = 0.0
VECINOS = 5


def leer_atlas(iso3: str, anio: int, ruta=ATLAS) -> pd.DataFrame:
    """PCI y COG del Atlas para el país y el año: `hs4, pci, cog`."""
    return duckdb.connect().execute(f"""SELECT product_hs92_code AS hs4, pci, cog
        FROM read_csv_auto('{ruta.as_posix()}', types={{'product_hs92_code': 'VARCHAR'}}) WHERE country_iso3_code = '{iso3}' AND year = {anio}""").df()


def eci_pais(iso3: str, ruta=ATLAS_PAIS) -> pd.DataFrame:
    """ECI y COI del Atlas por año para el país (contexto)."""
    return duckdb.connect().execute(f"SELECT year AS anio, eci, coi, diversity FROM read_csv_auto('{ruta.as_posix()}') WHERE country_iso3_code = '{iso3}' ORDER BY year").df()


def cuadrantes(df: pd.DataFrame, cuantil: float = CUANTIL_CERCANO, pci: float = PCI_COMPLEJO) -> pd.Series:
    """Cuadrante de cada candidato: cercano si la densidad está en el cuartil superior de los candidatos; complejo si PCI > `pci`."""
    corte = df.densidad.quantile(cuantil)
    cerca, compl = df.densidad >= corte, df.pci > pci
    return pd.Series(np.select([cerca & compl, cerca & ~compl, ~cerca & compl], ["cercano y complejo", "cercano y simple", "lejano y complejo"], "lejano y simple"), index=df.index)


def escalera(phi: np.ndarray, productos: list[str], origenes: list[str], pci: pd.Series, k: int = VECINOS) -> pd.DataFrame:
    """Para cada producto de `origenes`: hasta `k` vecinos de mayor proximidad con PCI mayor que el del origen (distintos del origen)."""
    idx = {h: i for i, h in enumerate(productos)}
    filas = []
    for o in origenes:
        if o not in idx or o not in pci.index or pd.isna(pci[o]):
            continue
        f = np.nan_to_num(phi[idx[o]].astype(float))
        for j in np.argsort(-f):
            q = productos[j]
            if q == o or f[j] <= 0:
                continue
            if q in pci.index and pd.notna(pci[q]) and pci[q] > pci[o]:
                filas.append({"origen": o, "destino": q, "phi": float(f[j]), "pci_origen": float(pci[o]), "pci_destino": float(pci[q])})
                if sum(1 for x in filas[-k:] if x["origen"] == o) >= k:
                    break
    return pd.DataFrame(filas)


def habilitadores(phi: np.ndarray, productos: list[str], presentes: list[str], candidatos: list[str], k: int = 3) -> pd.DataFrame:
    """Para cada candidato, los `k` productos que el país ya exporta más próximos a él (los que lo vuelven alcanzable)."""
    idx = {h: i for i, h in enumerate(productos)}
    pr = [h for h in presentes if h in idx]
    filas = []
    for c in candidatos:
        if c not in idx or not pr:
            continue
        f = np.nan_to_num(phi[idx[c], [idx[h] for h in pr]].astype(float))
        for j in np.argsort(-f)[:k]:
            if f[j] > 0:
                filas.append({"candidato": c, "habilitador": pr[j], "phi": float(f[j])})
    return pd.DataFrame(filas)


def matriz_de_proximidad(expo: pd.DataFrame, pob: pd.DataFrame, pais: str, corte: int) -> tuple[np.ndarray, list[str], list[str]]:
    """φ entre productos con la presencia D13 y la muestra D8 del año de corte (datos ≤ corte, D3); devuelve φ, la lista de productos y los productos presentes del país."""
    muestra = paises_elegibles(expo, pob, corte)
    rca = calcular_rca(expo)
    pres = presencia(rca[rca.iso3.isin(muestra)], corte)
    m, paises, productos = matriz_presencia(pres.rename(columns={"iso3": "country", "hs4": "product"}))
    paises, productos = [str(p) for p in paises], [str(p) for p in productos]
    presentes = [productos[j] for j in np.flatnonzero(m[paises.index(pais)] == 1)]
    return proximidad(m), productos, presentes


def main(argv: list[str] | None = None) -> None:
    import sys

    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pais", default=PAIS)
    ap.add_argument("--corte", type=int, default=CORTE)
    a = ap.parse_args(argv)
    from src.figuras.mapa_limites import nombres

    nom = nombres(largo=70, completo=True)
    atlas = leer_atlas(a.pais, a.corte)
    cand = pd.read_csv(MODELO / f"candidatos_producto_{a.pais}_{a.corte}.csv", dtype={"hs4": str})
    cand = cand[~cand.presente].merge(atlas, on="hs4", how="left").dropna(subset=["pci", "cog"]).reset_index(drop=True)
    cand["cuadrante"] = cuadrantes(cand)
    cand["nombre"] = cand.hs4.map(nom)
    cand.to_csv(MODELO / f"oportunidades_{a.pais}_{a.corte}.csv", index=False)
    phi, productos, presentes = matriz_de_proximidad(pd.read_parquet(MODELO / "exportaciones_hs4_depurado.parquet"), pd.read_csv(CLEAN / "poblacion_pais.csv"), a.pais, a.corte)
    pci = atlas.set_index("hs4").pci
    esc = escalera(phi, productos, presentes, pci)
    esc["nombre_origen"], esc["nombre_destino"] = esc.origen.map(nom), esc.destino.map(nom)
    esc.to_csv(MODELO / f"escalera_{a.pais}_{a.corte}.csv", index=False)
    hab = habilitadores(phi, productos, presentes, cand.hs4.tolist())
    hab["nombre"] = hab.habilitador.map(nom)
    hab.to_csv(MODELO / f"habilitadores_{a.pais}_{a.corte}.csv", index=False)
    e = eci_pais(a.pais)
    print(f"{a.pais} {a.corte}: ECI {e[e.anio == a.corte].eci.iloc[0]:+.3f} (Atlas); {len(presentes)} productos presentes; {len(cand)} candidatos con PCI y COG")
    print(cand.cuadrante.value_counts().to_string())
    print(f"\nCercano y complejo (los {min(20, int((cand.cuadrante == 'cercano y complejo').sum()))} de mayor densidad):")
    t = cand[cand.cuadrante == "cercano y complejo"].sort_values("densidad", ascending=False).head(20)
    print(t[["hs4", "nombre", "densidad", "puntaje", "pci", "cog"]].round(3).to_string(index=False))
    print(f"\nEscalera: {esc.origen.nunique()} de {len(presentes)} productos presentes tienen al menos un vecino más complejo; {len(esc)} escalones")


if __name__ == "__main__":
    main()
