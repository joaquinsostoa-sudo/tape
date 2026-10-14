"""Extensión de la prueba de corte transversal con todos los recursos naturales (declarada el 2026-10-13, commit `cbf086b`, ver `docs/supuestos.md`).

Términos nuevos (cada uno = tipo de producto × dotación física del país, estandarizada dentro de la muestra de cada año):
agua dulce (productos de tierra), hidro (intensidad energética × proporción hidroeléctrica), petróleo, gas y carbón (reservas por persona) y
minerales (participación en las reservas mundiales del USGS, estandarizada dentro de cada mineral; países ausentes = sin dato).

Uso: uv run python -m src.modelos.recursos
"""
from __future__ import annotations

import argparse
import re

import numpy as np
import pandas as pd

from src.modelos.logit_nacional import CLEAN, MODELO, RAIZ, VENTANAS, construir_datos, z
from src.modelos.presente import COLS_M, agregar_tierra, ajustar_con_ll, es_de_tierra

USGS = RAIZ / "data" / "raw" / "usgs_mcs" / "696a75d5d4be0228872d3bf8.csv"
ENERGIA = RAIZ / "data" / "raw" / "reservas_energia"
MINERALES = {  # HS4 -> mineral del USGS
    "2601": "Iron Ore", "2602": "Manganese", "2603": "Copper", "2604": "Nickel", "2606": "Bauxite", "2607": "Lead", "2608": "Zinc",
    "2609": "Tin", "2610": "Chromium", "2611": "Tungsten", "2613": "Molybdenum", "2614": "Titanium Mineral Concentrates",
    "2504": "Graphite (Natural)", "2510": "Phosphate Rock", "2528": "Boron", "3104": "Potash", "7106": "Silver", "7108": "Gold",
}
ENERGETICOS = {"petroleo": ({"2709", "2710"}, "petroleo_reservas_probadas.csv", "oil_reserves_m3"),
               "gas": ({"2711"}, "gas_reservas_probadas.csv", "gas_reserves_m3"),
               "carbon": ({"2701", "2704"}, "carbon_reservas_probadas.csv", "coal_reserves_tonnes")}
ALIAS_PAIS = {"Bolivia": "BOL", "Burma": "MMR", "Congo (Kinshasa)": "COD", "Korea, North": "PRK", "Korea, Republic of": "KOR",
              "Laos": "LAO", "Russia": "RUS", "Tanzania": "TZA", "Turkey": "TUR", "United States": "USA"}
NUEVOS = ["ra_agua", "ra_hidro", "ra_petroleo", "ra_gas", "ra_carbon", "ra_mineral"]


def limpiar_valor(s) -> float:
    """Valor numérico de una celda del USGS: quita comas y los signos «>» y «<»; «Small», «—», «s», «W» o vacío quedan vacíos."""
    if pd.isna(s):
        return np.nan
    t = re.sub(r"[,>< ]", "", str(s))
    try:
        return float(t)
    except ValueError:
        return np.nan


def _familia(detalle: str) -> str:
    """Quita la marca «rounded» del detalle de la estadística (la fila «World total» viene como «<detalle>: rounded»)."""
    return re.sub(r"[,:]? ?rounded", "", detalle).strip()


def participacion_reservas(usgs: pd.DataFrame, puente: pd.DataFrame) -> pd.DataFrame:
    """Participación de cada país en las reservas mundiales de cada mineral (commodity, iso3, share).

    Por mineral se usa la familia de reservas con más países con dato; el total mundial es la fila «World total» (o la suma de los países)."""
    r = usgs[usgs.Statistics == "Reserves"].copy()
    r["valor"] = r.Value.map(limpiar_valor)
    r["familia"] = r.Statistics_detail.map(_familia)
    nombres = {re.sub(r"[^a-z]", "", n.lower()): i for n, i in zip(puente.nombre, puente.iso3, strict=True)}
    filas = []
    for mineral, g in r.groupby("Commodity"):
        paises = g[~g.Country.isin(["World total", "Other countries"]) & g.valor.notna()]
        if paises.empty:
            continue
        fam = paises.groupby("familia").Country.nunique().sort_values(ascending=False, kind="stable").index[0]
        p = paises[paises.familia == fam]
        total = g[(g.Country == "World total") & (g.familia == fam)].valor.dropna()
        total = float(total.iloc[0]) if len(total) else float(p.valor.sum())
        for pais, v in zip(p.Country, p.valor, strict=True):
            iso = ALIAS_PAIS.get(pais) or nombres.get(re.sub(r"[^a-z]", "", pais.lower()))
            if iso and total > 0:
                filas.append((mineral, iso, min(v / total, 1.0)))
    out = pd.DataFrame(filas, columns=["commodity", "iso3", "share"])
    return out.groupby(["commodity", "iso3"], as_index=False).share.sum()


def reservas_energia(pob: pd.DataFrame) -> pd.DataFrame:
    """log(1 + reservas por persona) de petróleo, gas y carbón por (iso3, anio); vacío si la fuente no cubre ese año o país."""
    out = None
    for nombre, (_, archivo, col) in ENERGETICOS.items():
        d = pd.read_csv(ENERGIA / archivo).dropna(subset=["code"])
        d = d[d.code.str.len() == 3].rename(columns={"code": "iso3", "year": "anio"})[["iso3", "anio", col]]
        d = d.merge(pob, on=["iso3", "anio"], how="inner")
        d[f"l_{nombre}"] = np.log1p(d[col] / d.poblacion)
        d = d[["iso3", "anio", f"l_{nombre}"]]
        out = d if out is None else out.merge(d, on=["iso3", "anio"], how="outer")
    return out


def _z_por_anio(df: pd.DataFrame, col: str) -> pd.Series:
    """Estandariza `col` dentro de cada año entre los países de la muestra (una vez por país-año)."""
    p = df.drop_duplicates(["anio", "iso3"])[["anio", "iso3", col]]
    p = p.assign(z=p.groupby("anio")[col].transform(z))
    return df[["anio", "iso3"]].merge(p[["anio", "iso3", "z"]], on=["anio", "iso3"], how="left").z.to_numpy()


def agregar_recursos(df: pd.DataFrame, dot: pd.DataFrame, energia: pd.DataFrame, minerales: pd.DataFrame, ausente_cero: bool = False) -> pd.DataFrame:
    """Agrega a `df` los seis términos nuevos (ra_*) y sus controles de ingreso (rpib_*)."""
    d = df.merge(dot[["iso3", "anio", "log_agua", "hidro"]], on=["iso3", "anio"], how="left").merge(energia, on=["iso3", "anio"], how="left")
    d["a_agua"], d["a_hidro"] = _z_por_anio(d, "log_agua"), _z_por_anio(d, "hidro")
    tierra = es_de_tierra(d.hs4).astype(float)
    d["ra_agua"], d["rpib_agua"] = tierra * d.a_agua, tierra * d.a_pib
    d["ra_hidro"] = d.r_energia * d.a_hidro
    for nombre, (productos, _, _) in ENERGETICOS.items():
        es = d.hs4.isin(productos).astype(float)
        d[f"a_{nombre}"] = _z_por_anio(d, f"l_{nombre}")
        d[f"ra_{nombre}"] = np.where(es == 1, d[f"a_{nombre}"], 0.0)  # fuera de su producto, 0; sin dato de reservas en su producto, vacío
        d[f"rpib_{nombre}"] = es * d.a_pib
    d["mineral"] = d.hs4.map(MINERALES)
    paises = d.drop_duplicates(["anio", "iso3"])[["anio", "iso3"]].drop_duplicates("iso3")[["iso3"]]
    base = minerales.assign(l=np.log1p(100 * minerales.share))
    if ausente_cero:  # sensibilidad: un país ausente del USGS tiene reservas cero de ese mineral
        grilla = pd.MultiIndex.from_product([sorted(base.commodity.unique()), paises.iso3], names=["commodity", "iso3"]).to_frame(index=False)
        base = grilla.merge(base, on=["commodity", "iso3"], how="left").assign(l=lambda x: x.l.fillna(0.0))
    base["a_min"] = base.groupby("commodity").l.transform(z)
    d = d.merge(base[["commodity", "iso3", "a_min"]], left_on=["mineral", "iso3"], right_on=["commodity", "iso3"], how="left")
    d["ra_mineral"] = np.where(d.mineral.isna(), 0.0, d.a_min)  # producto mineral de un país sin dato: vacío
    d["rpib_mineral"] = d.mineral.notna().astype(float) * d.a_pib
    return d.drop(columns=["commodity"])


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--expo", default=str(MODELO / "exportaciones_hs4.parquet"))
    ap.add_argument("--salida", default=str(MODELO / "recursos_resultados.csv"))
    args = ap.parse_args(argv)
    dot = pd.read_parquet(CLEAN / "dotaciones.parquet")
    pob = pd.read_csv(CLEAN / "poblacion_pais.csv")
    puente = pd.read_csv(CLEAN / "puente_paises_baci.csv")
    minerales = participacion_reservas(pd.read_csv(USGS, low_memory=False, encoding="cp1252"), puente)
    print(f"minerales: {minerales.commodity.nunique()} con reservas, {len(minerales)} pares mineral-país, {minerales.iso3.nunique()} países")
    df = construir_datos(pd.read_parquet(args.expo), dot, pd.read_csv(CLEAN / "requisitos_producto_hs4.csv", dtype={"hs4": str}), pob,
                         ventanas=VENTANAS, h=0, inicio_max=np.inf, revelados=False, solo_con_requisitos=False)
    df = agregar_tierra(df, dot)
    energia = reservas_energia(pob)
    modelos = {  # nombre -> (tabla, columnas, tabla con ausente = 0)
        "R1_tierra_y_agua": (["ra_tierra", "ra_agua"], False, False),
        "R2_energia_y_minerales": (["ra_petroleo", "ra_gas", "ra_carbon", "ra_mineral"], False, False),
        "M_con_hidro": ([*COLS_M, "ra_hidro"], True, False),
        "R2_ausente_cero": (["ra_petroleo", "ra_gas", "ra_carbon", "ra_mineral"], False, True),
        "R1_con_control_pib": (["ra_tierra", "ra_agua", "rpib_tierra"], False, False),  # rpib_agua sería idéntica a rpib_tierra (mismos productos)
        "R2_con_control_pib": (["ra_petroleo", "ra_gas", "ra_carbon", "ra_mineral", "rpib_petroleo", "rpib_gas", "rpib_carbon", "rpib_mineral"], False, False),
    }
    base = agregar_recursos(df, dot, energia, minerales)
    base0 = agregar_recursos(df, dot, energia, minerales, ausente_cero=True)
    filas = []
    for nombre, (cols, solo_req, cero) in modelos.items():
        d = base0 if cero else base
        d = d[d.r_energia.notna()] if solo_req else d
        for periodo, sub in [("agrupado", d), *([] if "control" in nombre or cero else [(str(t), d[d.anio == t]) for t in VENTANAS])]:
            usar = [c for c in cols if sub[c].dropna().abs().sum() > 0]  # sin columnas vacías (el carbón no existe en 2000 ni 2005)
            if sub.empty or not usar or sub[usar].dropna().empty:
                continue
            try:
                tabla, info = ajustar_con_ll(sub, usar)
            except (ValueError, np.linalg.LinAlgError) as e:
                print(f"\n== {nombre} · {periodo}: no se pudo estimar ({e})")
                continue
            print(f"\n== {nombre} · {periodo}: {info['filas']:,} filas, {info['presencias']:,} presencias, {info['paises']} países, "
                  f"mejora de log-verosimilitud {info['mejora_ll_por_mil']:.2f} por mil obs. (LR = {info['lr']:.0f})")
            print(tabla.round(4).to_string())
            filas.append(tabla.reset_index(names="variable").assign(modelo=nombre, periodo=periodo, **info))
    pd.concat(filas).to_csv(args.salida, index=False)
    print(f"\n-> {args.salida}")


if __name__ == "__main__":
    main()
