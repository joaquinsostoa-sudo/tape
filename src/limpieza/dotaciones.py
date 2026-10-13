"""Dotaciones por país a_ckt (tarea 1.5): capital humano, crédito, energía y logística, estandarizadas por año.

Fuentes (todas ya descargadas): Penn World Table 10.01 (capital humano `hc`, hasta 2019) y WDI (matrícula, crédito,
electricidad, LPI, población y PIB per cápita). La muestra son los países del catálogo de BACI (los agregados
regionales de WDI se descartan).

Capas y transformaciones (por revisar, ver docs/dotaciones.md):
- capital_humano = `hc` de PWT (índice basado en años de escolaridad y retornos); alternativas: matrícula terciaria y secundaria.
- credito = log del crédito interno al sector privado (% PIB).
- energia = menos el log del precio de la electricidad (centavos de USD por kWh, Doing Business 2016-2020), promediado
  2014-2019: precio bajo = mejor dotación, igual que en las demás capas (más es mejor). Es una característica estable
  del país: se aplica el mismo valor a todos los años (anacrónico para las ventanas anteriores a 2014; ver docs/dotaciones.md).
  El consumo eléctrico per cápita (que mide uso, no costo) y la proporción hidroeléctrica quedan como variables
  alternativas (`z_consumo_electrico`, `z_hidro`).
- logistica = índice de desempeño logístico (LPI, 1 a 5). Solo hay ediciones en 2007, 2010, 2012, 2014, 2016, 2018 y
  2022: cada edición se arrastra hacia adelante hasta la siguiente, nunca hacia atrás (sin fuga de información), así que
  antes de 2007 queda vacío.
- Cada capa se estandariza por año (media 0, desvío 1) y se guarda también su percentil. No se imputa nada: la muestra
  definitiva de países (D8) se fija al armar el panel.

FIX 2026-10-12: paises_baci lee el CSV suelto si no hay zip. No hace falta
copiar los 8,7 GB de BACI: solo se usa `country_codes_V202601.csv`.
"""
from __future__ import annotations

import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
WDI = RAIZ / "data" / "raw" / "wdi"
PWT = RAIZ / "data" / "raw" / "pwt" / "pwt1001.xlsx"
BACI_ZIP = RAIZ / "data" / "raw" / "baci" / "BACI_HS92_V202601.zip"
BACI_CSV_PAISES = RAIZ / "data" / "raw" / "baci" / "country_codes_V202601.csv"
SALIDA = RAIZ / "data" / "clean" / "dotaciones.parquet"
SALIDA_CORTES = RAIZ / "data" / "clean" / "dotaciones_cortes.csv"
SALIDA_POBLACION = RAIZ / "data" / "clean" / "poblacion_pais.csv"  # versionada: filtro D8 sin reconstruir todo
ANIOS = range(1990, 2025)
CORTES = (2000, 2005, 2010, 2015, 2019, 2024)
INDICADORES = {
    "matricula_terciaria": "SE.TER.ENRR", "matricula_secundaria": "SE.SEC.ENRR",
    "credito_privado_pib": "FS.AST.PRVT.GD.ZS", "consumo_electrico_pc": "EG.USE.ELEC.KH.PC",
    "acceso_electricidad": "EG.ELC.ACCS.ZS", "lpi_edicion": "LP.LPI.OVRL.XQ",
    "poblacion": "SP.POP.TOTL", "pib_pc_ppa": "NY.GDP.PCAP.PP.KD",
    "hidro": "EG.ELC.HYRO.ZS", "precio_electricidad_db": "IC.ELC.PRI.KH.DB1619",
}
CAPAS = {  # capa -> columna base ya transformada
    "capital_humano": "hc", "credito": "log_credito", "energia": "menos_log_precio", "logistica": "lpi",
}
EXTRAS = {"consumo_electrico": "log_consumo_electrico", "hidro": "hidro"}  # alternativas de energía, solo con z
ANIOS_PRECIO = range(2014, 2020)  # el precio de Doing Business existe solo en estos años


def paises_baci(zip_ruta=BACI_ZIP) -> set[str]:
    """Catálogo de países de BACI. FIX: lee el CSV suelto si no hay zip."""
    if BACI_CSV_PAISES.exists():
        return set(pd.read_csv(BACI_CSV_PAISES).country_iso3.dropna())
    with zipfile.ZipFile(zip_ruta) as z, z.open("country_codes_V202601.csv") as f:
        return set(pd.read_csv(f).country_iso3.dropna())


def nombres_economias(carpeta: Path = WDI) -> dict[str, str]:
    """Nombre oficial de cada economía (iso3 -> nombre), tomado de un indicador de WDI de cobertura completa."""
    ruta = next(carpeta.glob("wdi_SP.POP.TOTL_p*.json"))
    return {r["countryiso3code"]: r["country"]["value"] for r in json.loads(ruta.read_text(encoding="utf-8"))[1]
            if r["countryiso3code"]}


def leer_wdi(codigo: str, paises: set[str], carpeta: Path = WDI, nombres: dict[str, str] | None = None) -> pd.DataFrame:
    """Un indicador de WDI en formato largo (iso3, anio, valor), sin los agregados regionales.

    Algunas fuentes (Doing Business) traen además una fila por ciudad con el mismo código de país. Si hay varias filas
    para un país y año, se queda con la que lleva el nombre de la economía; si ninguna lo lleva, promedia."""
    filas = []
    for ruta in sorted(carpeta.glob(f"wdi_{codigo}_p*.json")):
        for r in json.loads(ruta.read_text(encoding="utf-8"))[1]:
            if r["value"] is not None and r["countryiso3code"] in paises:
                filas.append((r["countryiso3code"], int(r["date"]), float(r["value"]), r["country"]["value"]))
    d = pd.DataFrame(filas, columns=["iso3", "anio", "valor", "nombre"])
    if nombres is not None and d.duplicated(["iso3", "anio"]).any():
        propio = d.nombre == d.iso3.map(nombres)
        hay_propio = propio.groupby([d.iso3, d.anio]).transform("any")
        d = d[~hay_propio | propio]  # donde hay fila de la economía, solo esa; donde no, todas (se promedian)
    return d.groupby(["iso3", "anio"], as_index=False).valor.mean()


def leer_pwt(ruta: Path = PWT) -> pd.DataFrame:
    d = pd.read_excel(ruta, sheet_name="Data", usecols=["countrycode", "year", "hc"])
    return d.rename(columns={"countrycode": "iso3", "year": "anio"}).dropna(subset=["hc"])


def arrastrar_ediciones(lpi: pd.DataFrame, anios=ANIOS) -> pd.DataFrame:
    """Cada edición del LPI vale desde su año hasta la siguiente edición; nunca hacia atrás.
    Devuelve (iso3, anio, lpi, lpi_edicion_anio)."""
    salida = []
    for iso3, g in lpi.groupby("iso3"):
        g = g.sort_values("anio")
        base = pd.DataFrame({"anio": list(anios)}).merge(g.rename(columns={"anio": "edicion", "valor": "lpi"}),
                                                          left_on="anio", right_on="edicion", how="left")
        base[["lpi", "edicion"]] = base[["lpi", "edicion"]].ffill()
        base["iso3"] = iso3
        salida.append(base.rename(columns={"edicion": "lpi_edicion_anio"}))
    return pd.concat(salida, ignore_index=True)[["iso3", "anio", "lpi", "lpi_edicion_anio"]]


def log_positivo(x: pd.Series) -> pd.Series:
    """Logaritmo natural; lo que no es positivo queda vacío (no se inventa un valor)."""
    return np.log(x.where(x > 0))


def precio_promedio(df: pd.DataFrame, anios=ANIOS_PRECIO) -> pd.Series:
    """Precio de la electricidad por país: promedio de los años con dato dentro de `anios` (vacío si no hay ninguno)."""
    d = df[df.anio.isin(list(anios))]
    return d.groupby("iso3").precio_electricidad_db.mean()


def estandarizar_por_anio(df: pd.DataFrame, col: str) -> tuple[pd.Series, pd.Series]:
    """(z, percentil) de `col` dentro de cada año, solo con los países que tienen dato ese año."""
    g = df.groupby("anio")[col]
    z = (df[col] - g.transform("mean")) / g.transform("std")
    return z, g.rank(pct=True)


def construir(paises: set[str] | None = None) -> pd.DataFrame:
    paises = paises or paises_baci()
    base = pd.MultiIndex.from_product([sorted(paises), list(ANIOS)], names=["iso3", "anio"]).to_frame(index=False)
    nombres = nombres_economias()
    for nombre, codigo in INDICADORES.items():
        w = leer_wdi(codigo, paises, nombres=nombres).rename(columns={"valor": nombre})
        base = base.merge(w, on=["iso3", "anio"], how="left")
    pwt = leer_pwt().rename(columns={"hc": "hc"})
    base = base.merge(pwt, on=["iso3", "anio"], how="left")
    lpi = base[["iso3", "anio", "lpi_edicion"]].dropna(subset=["lpi_edicion"]).rename(columns={"lpi_edicion": "valor"})
    base = base.drop(columns="lpi_edicion").merge(arrastrar_ediciones(lpi), on=["iso3", "anio"], how="left")
    base["log_credito"] = log_positivo(base.credito_privado_pib)
    base["log_consumo_electrico"] = log_positivo(base.consumo_electrico_pc)
    base["precio_electricidad_kwh"] = base.iso3.map(precio_promedio(base))  # característica estable del país
    base["menos_log_precio"] = -log_positivo(base.precio_electricidad_kwh)  # barato = mejor dotación
    for capa, col in CAPAS.items():
        base[f"z_{capa}"], base[f"pct_{capa}"] = estandarizar_por_anio(base, col)
    for nombre, col in EXTRAS.items():
        base[f"z_{nombre}"], _ = estandarizar_por_anio(base, col)
    return base


def cobertura(df: pd.DataFrame, cortes=CORTES) -> pd.DataFrame:
    """Países con dato por capa y año de corte."""
    return pd.DataFrame({capa: {a: int(df[df.anio == a][f"z_{capa}"].notna().sum()) for a in cortes} for capa in CAPAS})


def main() -> None:
    df = construir()
    df.to_parquet(SALIDA, index=False)
    cols = ["iso3", "anio", *(f"z_{c}" for c in CAPAS), *(f"pct_{c}" for c in CAPAS),
            *(f"z_{e}" for e in EXTRAS), "precio_electricidad_kwh", "poblacion", "pib_pc_ppa"]
    df[df.anio.isin(CORTES)][cols].round(4).to_csv(SALIDA_CORTES, index=False, encoding="utf-8")
    df[["iso3", "anio", "poblacion"]].dropna().to_csv(SALIDA_POBLACION, index=False, encoding="utf-8")
    print(f"{df.iso3.nunique()} países ×{df.anio.nunique()} años; países con dato por capa y corte:")
    print(cobertura(df).to_string())


if __name__ == "__main__":
    main()