"""Requisitos por producto r_pk (decisión D4): intensidad energética, de capital, de habilidades y valor por peso.

Cadena: intensidades por industria NAICS (NBER-CES, EE. UU.) -> productos HS 2012 (concordancia de Pierce y Schott,
años 2014-2016) -> productos HS92 (cadena de conversión de `hs_sector`) -> HS de 4 dígitos (unidad de estimación, D5).
El valor por peso sale de BACI, no de NBER-CES.

Supuestos y límites (ver docs/supuestos.md y data/raw/intensidades/README.md):
- La tecnología es la de la manufactura de EE. UU.; la agricultura y la minería no tienen dato (`sin_dato`).
- Los HS6 que caen en varias industrias se reparten en partes iguales por línea HS10 (no hay valores de comercio de
  EE. UU. por HS10 en la concordancia).
- Habilidades = proporción de trabajadores que no son de producción: es un sustituto, la base no mide habilidades.
- Unidades: capital en miles de USD por trabajador; energía como fracción del valor de envíos; valor por peso en USD/kg.
"""
from __future__ import annotations

import zipfile

import pandas as pd

from .hs_sector import BACI_ZIP, ENERGIA, NO_ESPECIFICADO, hs92_a_hs12, valor_mundial
from .taxonomia_tape import RAIZ

NBER = RAIZ / "data" / "raw" / "intensidades" / "nberces" / "nberces5818v1_n2012.csv"
SCHOTT = RAIZ / "data" / "raw" / "concordancias" / "hs_naics_schott" / "hssicnaics_20181015.zip"
SALIDA_HS6 = RAIZ / "data" / "clean" / "requisitos_producto_hs6.parquet"
SALIDA_HS4 = RAIZ / "data" / "clean" / "requisitos_producto.parquet"
SALIDA_HS4_CSV = RAIZ / "data" / "clean" / "requisitos_producto_hs4.csv"
ANIOS_INTENSIDAD = range(2012, 2019)  # NBER-CES llega a 2018
ANIOS_CAPITAL = range(2012, 2017)  # el stock de capital llega a 2016
ANIOS_CONCORDANCIA = ("2014", "2015", "2016")  # HS 2012 vigente y NAICS 2012 ya incorporado
ANIOS_PESO = (2018, 2019)  # antes de la pandemia
VARIABLES = ["energia", "capital", "habilidades"]


def intensidades_naics(nber: pd.DataFrame) -> pd.DataFrame:
    """Por industria: energía/valor de envíos, capital/empleo y proporción de trabajadores que no son de producción.

    Cada razón es suma sobre años de la ventana dividida entre suma (no promedio de razones anuales)."""
    d = nber.assign(naics=nber.naics.astype(str))
    a = d[d.year.isin(ANIOS_INTENSIDAD)].dropna(subset=["emp", "vship", "energy", "prode"]).groupby("naics")
    base = pd.DataFrame({
        "energia": a.energy.sum() / a.vship.sum(),
        "habilidades": (a.emp.sum() - a.prode.sum()) / a.emp.sum(),
    })
    c = d[d.year.isin(ANIOS_CAPITAL)].dropna(subset=["cap", "emp"]).groupby("naics")
    base["capital"] = c.cap.sum() / c.emp.sum()
    return base.reset_index()


def hs12_a_naics(zip_ruta=SCHOTT, anios: tuple[str, ...] = ANIOS_CONCORDANCIA) -> pd.DataFrame:
    """(source = HS6 de 2012, target = NAICS, weight): partes iguales por línea HS10 dentro de cada HS6."""
    partes = []
    with zipfile.ZipFile(zip_ruta) as z:
        for flujo in ("exports", "imports"):
            with z.open(f"hs_sic_naics_{flujo}_89_117_20180927.csv") as f:
                partes.append(pd.read_csv(f, sep="\t", dtype=str, keep_default_na=False,
                                          usecols=["commodity", "year", "naics"]))
    d = pd.concat(partes)
    d = d[d.year.isin(anios) & (d.naics != "")].assign(commodity=lambda x: x.commodity.str.zfill(10))
    d["hs6"] = d.commodity.str[:6]
    lineas = d.drop_duplicates(["commodity", "naics"]).groupby(["hs6", "naics"]).size().rename("n").reset_index()
    lineas["weight"] = lineas.n / lineas.groupby("hs6").n.transform("sum")
    return lineas.rename(columns={"hs6": "source", "naics": "target"})[["source", "target", "weight"]]


def promedio_por_cadena(hs92_hs12: pd.DataFrame, hs12_naics: pd.DataFrame, naics: pd.DataFrame) -> pd.DataFrame:
    """Intensidades por HS92 de 6 dígitos y `cobertura` (parte del peso que llega a una industria con dato).

    El peso de cada camino HS92 -> HS12 -> NAICS es el producto de los pesos de sus tramos."""
    denom = hs92_hs12.groupby("source").weight.sum().rename("denominador")
    c = hs92_hs12.merge(hs12_naics, left_on="target", right_on="source", suffixes=("", "_n")).rename(
        columns={"source": "hs92", "target_n": "naics"})
    c["w"] = c.weight * c.weight_n
    c = c.merge(naics, on="naics", how="left")
    salida = {}
    for v in VARIABLES:
        ok = c[c[v].notna()]
        g = ok.assign(wv=ok.w * ok[v]).groupby("hs92")
        salida[v] = g.wv.sum() / g.w.sum()
        salida[f"peso_{v}"] = g.w.sum()
    # peso_top: la industria principal dentro del camino con más peso (qué tan ambiguo es el reparto)
    top = c.groupby(["hs92", "naics"]).w.sum().groupby("hs92").max().rename("peso_top")
    r = pd.DataFrame(salida).join(top, how="outer").join(denom, how="outer")
    r["cobertura"] = (r[["peso_energia", "peso_capital", "peso_habilidades"]].min(axis=1).fillna(0) / r.denominador).clip(0, 1)
    r["peso_top"] = (r.peso_top / r.denominador).clip(0, 1)
    return r.drop(columns=["peso_energia", "peso_capital", "peso_habilidades", "denominador"]).reset_index(names="hs92")


def confianza(cobertura: float, peso_top: float) -> str:
    """alta: casi todo el producto llega a una industria y el reparto no es ambiguo; sin_dato: ninguna industria."""
    if not cobertura or pd.isna(cobertura) or cobertura <= 0:
        return "sin_dato"
    if cobertura >= 0.8 and peso_top >= 0.8:
        return "alta"
    return "media" if cobertura >= 0.4 else "baja"


def valor_peso_baci(anios: tuple[int, ...] = ANIOS_PESO, zip_ruta=BACI_ZIP) -> pd.DataFrame:
    """Por HS6: valor y toneladas con peso informado (BACI trae valor en miles de USD y peso en toneladas)."""
    acum = []
    with zipfile.ZipFile(zip_ruta) as z:
        for a in anios:
            with z.open(f"BACI_HS92_Y{a}_V202601.csv") as f:
                for trozo in pd.read_csv(f, usecols=["k", "v", "q"], dtype={"k": str}, chunksize=3_000_000):
                    t = trozo[trozo.q > 0]
                    acum.append(t.groupby("k").agg(valor_con_peso=("v", "sum"), toneladas=("q", "sum")))
    g = pd.concat(acum).groupby(level=0).sum()
    g["valor_peso_usd_kg"] = g.valor_con_peso / g.toneladas  # miles de USD por tonelada = USD por kg
    return g.rename_axis("hs92").reset_index()


def agregar_hs4(hs6: pd.DataFrame, valor: pd.Series) -> pd.DataFrame:
    """HS6 -> HS4: promedio de cada intensidad ponderado por el valor mundial exportado (solo con dato)."""
    d = hs6.assign(hs4=hs6.hs92.str[:4], valor=hs6.hs92.map(valor).fillna(0.0))
    salida = {}
    for v in VARIABLES:
        ok = d[d[v].notna() & (d.valor > 0)]
        g = ok.assign(wv=ok.valor * ok[v]).groupby("hs4")
        salida[v] = g.wv.sum() / g.valor.sum()
    tot = d.groupby("hs4").valor.sum()
    salida["cobertura"] = (d.assign(c=d.valor * d.cobertura.fillna(0)).groupby("hs4").c.sum() / tot).where(tot > 0)
    salida["peso_top"] = (d.assign(c=d.valor * d.peso_top.fillna(0)).groupby("hs4").c.sum() / tot).where(tot > 0)
    p = d.groupby("hs4")[["valor_con_peso", "toneladas"]].sum(min_count=1)
    salida["valor_peso_usd_kg"] = p.valor_con_peso / p.toneladas
    salida["valor_mundial"] = tot
    r = pd.DataFrame(salida).reset_index()
    r["confianza"] = [confianza(c, t) for c, t in zip(r.cobertura, r.peso_top, strict=True)]
    return r


def construir() -> tuple[pd.DataFrame, pd.DataFrame]:
    nber = pd.read_csv(NBER, dtype={"naics": str})
    naics = intensidades_naics(nber)
    codigos = set(pd.read_csv(RAIZ / "data" / "clean" / "puente_hs92_sector.csv", dtype=str).hs92)
    hs6 = promedio_por_cadena(hs92_a_hs12(codigos), hs12_a_naics(), naics)
    hs6 = pd.DataFrame({"hs92": sorted(codigos)}).merge(hs6, on="hs92", how="left")
    hs6["cobertura"] = hs6.cobertura.fillna(0.0)
    hs6 = hs6.merge(valor_peso_baci(), on="hs92", how="left")
    hs6["confianza"] = [confianza(c, t) for c, t in zip(hs6.cobertura, hs6.peso_top, strict=True)]
    hs6["nota"] = ""
    hs6.loc[hs6.hs92 == ENERGIA, "nota"] = "energía eléctrica: se excluye del comercio"
    hs6.loc[hs6.hs92 == NO_ESPECIFICADO, "nota"] = "no es un producto"
    hs4 = agregar_hs4(hs6, valor_mundial(ANIOS_PESO))
    return hs6, hs4


def main() -> None:
    hs6, hs4 = construir()
    hs6.to_parquet(SALIDA_HS6, index=False)
    hs4.to_parquet(SALIDA_HS4, index=False)
    hs4.to_csv(SALIDA_HS4_CSV, index=False, encoding="utf-8")
    v = hs4.valor_mundial.sum()
    por = hs4.groupby("confianza").valor_mundial.sum() / v
    print(f"{len(hs6)} productos HS6; {len(hs4)} productos HS4; valor mundial por confianza: "
          f"{ {k: round(float(x), 3) for k, x in por.items()} }")


if __name__ == "__main__":
    main()
