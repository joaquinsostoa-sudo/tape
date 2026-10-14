"""Cuadro de bloques de productos × dotaciones: ¿qué proporción de los países tiene ventaja comparativa revelada en cada bloque, según su tercil de dotación?

Bloques: los seis de `clasificacion_lall.py` (Lall 2000 llevada a HS4). Un país «tiene ventaja» en un bloque si su RCA del bloque en el año es ≥ 1 (RCA calculado con el
comercio mundial, sin la energía binacional). Muestra: países D8 del año. Dotaciones: tierra, agua dulce, reservas de petróleo, gas, carbón y minerales, capital humano,
capital físico por trabajador (tercil bajo = trabajo abundante), electricidad barata, logística y, de referencia, el PIB per cápita.

Terciles entre los países de la muestra con dato. Las dotaciones con más de un tercio de ceros (reservas) usan «sin reservas» como grupo bajo y parten a los demás en dos mitades.
Descriptivo y sin controles: las dotaciones están muy correlacionadas con el ingreso; por eso se agrega la diferencia dentro de terciles de ingreso (arriba contra abajo de la mediana
de la dotación, promediada con el tamaño de cada tercil de ingreso).

Uso: uv run python -m src.modelos.bloques_dotaciones
"""
from __future__ import annotations

import argparse

import numpy as np
import pandas as pd
from scipy.stats import fisher_exact

from src.modelos.logit_nacional import CLEAN, HS4_ENERGIA, MODELO, RAIZ, paises_elegibles
from src.modelos.recursos import USGS, participacion_reservas, reservas_energia

ANIO = 2015
BLOQUES = ["primarios_agropecuarios", "minerales_y_energia", "manufacturas_agropecuarias", "manufacturas_de_minerales", "manufactura_liviana",
           "manufactura_pesada_media_tec", "manufactura_alta_tec"]
DOTACIONES = {  # columna -> (nombre en el cuadro, orden: alto es «más dotado»)
    "log_tierra": "Tierra cultivable por persona", "log_agua": "Agua dulce por persona", "l_petroleo": "Reservas de petróleo por persona",
    "l_gas": "Reservas de gas por persona", "l_carbon": "Reservas de carbón por persona", "riqueza_mineral": "Reservas de minerales (USGS)",
    "hc": "Capital humano", "log_capital_trabajador": "Capital físico por trabajador", "menos_log_precio": "Electricidad barata",
    "lpi": "Logística (LPI)", "pib_pc_ppa": "PIB per cápita (referencia)",
}


def rca_bloques(expo: pd.DataFrame, bloques: pd.DataFrame, anio: int) -> pd.DataFrame:
    """RCA de cada bloque por país, con el comercio mundial del año (sin la energía binacional); devuelve iso3, bloque, rca."""
    e = expo[(expo.anio == anio) & (expo.hs4 != HS4_ENERGIA)].merge(bloques[["hs4", "bloque"]], on="hs4", how="left")
    e["bloque"] = e.bloque.fillna("sin_clasificar")
    x = e.groupby(["iso3", "bloque"], as_index=False).x.sum()
    pais, mundo, total = x.groupby("iso3").x.transform("sum"), x.groupby("bloque").x.transform("sum"), x.x.sum()
    x["rca"] = (x.x / pais) / (mundo / total)
    return x[["iso3", "bloque", "rca"]]


def terciles(s: pd.Series) -> pd.Series:
    """«bajo», «medio» o «alto» por país. Con más de un tercio de ceros, el cero es «bajo» y el resto se parte por la mediana de los positivos."""
    s = s.dropna()
    if (s == 0).mean() > 1 / 3:
        med = s[s > 0].median()
        return pd.Series(np.where(s == 0, "bajo", np.where(s <= med, "medio", "alto")), index=s.index)
    r = s.rank(method="first")
    return pd.cut(r, [0, len(s) / 3, 2 * len(s) / 3, len(s) + 1], labels=["bajo", "medio", "alto"]).astype(str)


def cuadro(ventaja: pd.DataFrame, dot: pd.DataFrame, col: str) -> pd.DataFrame:
    """Para una dotación: por bloque, % de países con ventaja en cada tercil, diferencia alto − bajo (puntos) y p de Fisher (alto contra bajo)."""
    t = terciles(dot.set_index("iso3")[col]).rename("tercil")
    d = ventaja.merge(t, left_on="iso3", right_index=True)
    filas = []
    for b in BLOQUES:
        g = d[d.bloque == b]
        if g.empty:  # bloque sin filas en esta tabla
            continue
        por = g.groupby("tercil").ventaja.agg(["mean", "size", "sum"])
        alto, bajo = por.loc["alto"], por.loc["bajo"]
        p = fisher_exact([[alto["sum"], alto["size"] - alto["sum"]], [bajo["sum"], bajo["size"] - bajo["sum"]]])[1]
        filas.append({"dotacion": col, "bloque": b, "pct_bajo": 100 * bajo["mean"], "pct_medio": 100 * por.loc["medio", "mean"], "pct_alto": 100 * alto["mean"],
                      "dif_alto_bajo": 100 * (alto["mean"] - bajo["mean"]), "p_fisher": p, "n_bajo": int(bajo["size"]), "n_alto": int(alto["size"])})
    return pd.DataFrame(filas)


def dif_dentro_de_ingreso(ventaja: pd.DataFrame, dot: pd.DataFrame, col: str) -> pd.DataFrame:
    """Diferencia (arriba − abajo de la mediana de la dotación) en el % de países con ventaja, promediada dentro de terciles de ingreso, y la misma diferencia sin control."""
    d = dot.dropna(subset=[col, "pib_pc_ppa"]).copy()
    d["ingreso"] = terciles(d.set_index("iso3").pib_pc_ppa).reindex(d.iso3).to_numpy()
    d["arriba"] = d[col] > d[col].median() if (d[col] != 0).mean() > 2 / 3 else d[col] > 0
    filas = []
    for b in BLOQUES:
        g = ventaja[ventaja.bloque == b].merge(d[["iso3", "ingreso", "arriba"]], on="iso3")
        if g.empty:
            continue
        sin = 100 * (g[g.arriba].ventaja.mean() - g[~g.arriba].ventaja.mean())
        difs, pesos = [], []
        for _, h in g.groupby("ingreso"):
            if h.arriba.nunique() == 2:
                difs.append(h[h.arriba].ventaja.mean() - h[~h.arriba].ventaja.mean())
                pesos.append(len(h))
        con = 100 * np.average(difs, weights=pesos) if difs else np.nan
        filas.append({"dotacion": col, "bloque": b, "dif_sin_control": sin, "dif_dentro_de_ingreso": con})
    return pd.DataFrame(filas)


def dotaciones_del_anio(dot: pd.DataFrame, pob: pd.DataFrame, puente: pd.DataFrame, anio: int) -> pd.DataFrame:
    """Una fila por país con todas las dotaciones del año; la riqueza mineral es la suma de las participaciones en las reservas mundiales de los 18 minerales (ausente = 0)."""
    d = dot[dot.anio == anio].merge(reservas_energia(pob).query("anio == @anio"), on=["iso3", "anio"], how="left")
    import pandas as _pd

    from src.modelos.recursos import MINERALES
    usgs = participacion_reservas(_pd.read_csv(USGS, low_memory=False, encoding="cp1252"), puente)
    riqueza = usgs[usgs.commodity.isin(set(MINERALES.values()))].groupby("iso3").share.sum().rename("riqueza_mineral")
    d = d.merge(riqueza, left_on="iso3", right_index=True, how="left")
    d["riqueza_mineral"] = d.riqueza_mineral.fillna(0.0)
    return d


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--expo", default=str(MODELO / "exportaciones_hs4.parquet"))
    ap.add_argument("--anio", type=int, default=ANIO)
    args = ap.parse_args(argv)
    expo = pd.read_parquet(args.expo)
    bloques = pd.read_csv(CLEAN / "clasificacion_lall_hs4.csv", dtype={"hs4": str})
    dot = pd.read_parquet(CLEAN / "dotaciones.parquet")
    pob = pd.read_csv(CLEAN / "poblacion_pais.csv")
    puente = pd.read_csv(CLEAN / "puente_paises_baci.csv")
    muestra = paises_elegibles(expo, pob, args.anio)
    r = rca_bloques(expo, bloques, args.anio)
    r = r[r.iso3.isin(muestra) & r.bloque.isin(BLOQUES)]
    grilla = pd.MultiIndex.from_product([sorted(muestra), BLOQUES], names=["iso3", "bloque"]).to_frame(index=False)
    ventaja = grilla.merge(r, on=["iso3", "bloque"], how="left")
    ventaja["rca"] = ventaja.rca.fillna(0.0)
    ventaja["ventaja"] = ventaja.rca >= 1
    d = dotaciones_del_anio(dot, pob, puente, args.anio)
    d = d[d.iso3.isin(muestra)]
    print(f"{args.anio}: {len(muestra)} países en la muestra; con ventaja por bloque:", ventaja.groupby("bloque").ventaja.sum().to_dict())
    tabla = pd.concat([cuadro(ventaja, d, c) for c in DOTACIONES])
    control = pd.concat([dif_dentro_de_ingreso(ventaja, d, c) for c in DOTACIONES if c != "pib_pc_ppa"])
    tabla = tabla.merge(control, on=["dotacion", "bloque"], how="left")
    tabla.to_csv(MODELO / f"bloques_dotaciones_{args.anio}.csv", index=False)
    paises = ventaja.pivot(index="iso3", columns="bloque", values="rca").round(2)
    for c in DOTACIONES:
        paises[f"tercil_{c}"] = terciles(d.set_index("iso3")[c])
    paises.to_csv(MODELO / f"bloques_paises_{args.anio}.csv")
    print(tabla.round(1).to_string(index=False))
    print(RAIZ)


if __name__ == "__main__":
    main()
