"""Puente HS92 (6 dígitos) -> CPC 2.1 -> CIIU Rev.4 -> sector TAPE, con pesos y confianza por fila.

Cadena (correspondencias oficiales, salvo el reparto de pesos cuando hay varias salidas):
  1. HS92 -> HS96 -> HS02 -> HS07 -> HS12: tablas ponderadas por valor comerciado del Atlas (Growth Lab).
     Esas tablas solo listan los códigos que cambian: los demás pasan sin cambio.
  2. HS12 -> CPC 2.1 (ONU). Si un código HS tiene varias CPC, reparto en partes iguales.
  3. CPC 2.1 -> CIIU Rev.4 (ONU). Si una CPC tiene varias clases, reparto en partes iguales.
  4. Clase CIIU -> sector TAPE: partición de `taxonomia_tape` (cada clase cae en un solo sector).
Vías: `cadena` (todo oficial), `cadena_prefijo` (un código HS12 que la ONU no lista se reparte entre sus
códigos hermanos de 4 dígitos), `regla_residuos` (CPC de residuos y chatarra, que la ONU deja sin clase
CIIU, van a la clase 3830 de recuperación de materiales), `regla_especial` (arneses) y `fallback_hs4`
(código sin cadena: se reparte como sus hermanos de partida HS4, ponderado por valor mundial).
Reglas del equipo: los arneses (HS 854430) van a Autopartes; los posibles biocombustibles se marcan por
producto HS; la electricidad (HS 271600) se marca para excluirla del comercio.
"""
from __future__ import annotations

import zipfile

import pandas as pd

from .taxonomia_tape import RAIZ, SECTORES, sectores_de_clase

CONV = RAIZ / "data" / "raw" / "concordancias" / "atlas_conversion_hs"
UNSD = RAIZ / "data" / "raw" / "concordancias" / "unsd"
BACI_ZIP = RAIZ / "data" / "raw" / "baci" / "BACI_HS92_V202601.zip"
VALORES = RAIZ / "data" / "raw" / "atlas" / "hs92_product_year_6.csv"
SALIDA = RAIZ / "data" / "clean" / "puente_hs92_sector.csv"

PASOS = [("hs92_hs96.tab", "\t"), ("hs96_to_hs02.csv", ","), ("hs02_to_hs07.csv", ","), ("hs07_to_hs12.csv", ",")]
ENERGIA = "271600"  # energía eléctrica (Itaipú y Yacyretá): se excluye del comercio
NO_ESPECIFICADO = "999999"  # mercancías no especificadas: no es un producto, no tiene sector
ARNES = "854430"  # juegos de cables para vehículos (arneses): Autopartes por decisión del equipo
CLASE_ARNES = "2930"  # partes y accesorios de vehículos automotores
BIOCOMBUSTIBLE_POSIBLE = {"220710", "220720", "151800", "382390"}  # etanol y partidas donde puede ir el biodiésel (HS92)
CLASE_RESIDUOS = "3830"  # recuperación de materiales (reciclaje)
ORDEN_VIA = {"cadena": 0, "regla_residuos": 1, "cadena_prefijo": 2}


def _leer(ruta, sep: str) -> pd.DataFrame:
    df = pd.read_csv(ruta, sep=sep, dtype=str)
    df.columns = ["source", "target", "weight"]
    return df.assign(weight=df.weight.astype(float))


def componer(a: pd.DataFrame, b: pd.DataFrame) -> pd.DataFrame:
    """Encadena dos tablas (source, target, weight): el peso del camino es el producto de los pesos."""
    m = a.merge(b, left_on="target", right_on="source", suffixes=("_a", "_b"))
    m["weight"] = m.weight_a * m.weight_b
    return (m.groupby(["source_a", "target_b"], as_index=False).weight.sum()
            .rename(columns={"source_a": "source", "target_b": "target"}))


def con_identidad(t: pd.DataFrame, codigos: set[str]) -> pd.DataFrame:
    """Las tablas de conversión solo listan los códigos que cambian: los demás pasan sin cambio."""
    faltan = sorted(set(codigos) - set(t.source))
    return pd.concat([t, pd.DataFrame({"source": faltan, "target": faltan, "weight": 1.0})], ignore_index=True)


def hs92_a_hs12(codigos: set[str]) -> pd.DataFrame:
    """Cadena HS92 -> HS12 con los códigos que no cambian tratados como identidad en cada paso."""
    t = con_identidad(_leer(CONV / PASOS[0][0], PASOS[0][1]), codigos)
    t = t[t.source.isin(codigos)]
    for nombre, sep in PASOS[1:]:
        t = componer(t, con_identidad(_leer(CONV / nombre, sep), set(t.target)))
    return t[t.weight > 0]


def repartir_igual(pares: pd.DataFrame, origen: str, destino: str) -> pd.DataFrame:
    """De una tabla de pares (origen, destino) a (source, target, weight) con partes iguales por origen."""
    p = pares[[origen, destino]].drop_duplicates()
    p["weight"] = 1.0 / p.groupby(origen)[destino].transform("size")
    return p.rename(columns={origen: "source", destino: "target"})


PESO_CPC_COMPLETA = 3.0  # una CPC contenida entera en el código HS pesa 3 veces lo que una parcial


def hs12_a_cpc() -> pd.DataFrame:
    """HS12 -> CPC 2.1. Si un código tiene varias CPC, pesa más la que está contenida entera en él
    (marca CPC21partial = 0 de la ONU): p. ej. 0805.10 es naranja fresca (agricultura) y, en parte, fruta seca."""
    d = pd.read_csv(UNSD / "cpc21-hs2012.txt", dtype=str).drop_duplicates(["CPC21code", "HS12code"])
    d["hs12"] = d.HS12code.str.replace(".", "", regex=False)
    d["w"] = d.CPC21partial.map({"0": PESO_CPC_COMPLETA}).fillna(1.0)
    d["weight"] = d.w / d.groupby("hs12").w.transform("sum")
    return (d.rename(columns={"hs12": "source", "CPC21code": "target"})[["source", "target", "weight"]]
            .groupby(["source", "target"], as_index=False).weight.sum())


def extender_por_prefijo(destinos: set[str], cpc: pd.DataFrame) -> pd.DataFrame:
    """Para códigos HS12 que la tabla de la ONU no lista, usa los códigos hermanos que comparten prefijo.

    Se prueba primero con 5 dígitos y luego con 4. El peso de cada CPC es el promedio de sus hermanos.
    """
    conocidos = sorted(set(cpc.source))
    filas = []
    for t in sorted(destinos - set(conocidos)):
        for n in (5, 4):
            hijos = [c for c in conocidos if c.startswith(t[:n])]
            if hijos:
                break
        else:
            continue
        w = cpc[cpc.source.isin(hijos)].groupby("target").weight.sum() / len(hijos)
        filas += [{"source": t, "target": c, "weight": float(x)} for c, x in w.items()]
    return pd.DataFrame(filas, columns=["source", "target", "weight"])


def cpc_a_clase() -> tuple[pd.DataFrame, pd.DataFrame]:
    """(tabla oficial, tabla de residuos). La ONU deja sin clase ('n/a') a los residuos y chatarra (CPC 39)."""
    # keep_default_na=False: pandas leería el texto "n/a" de la ONU como dato faltante
    d = pd.read_csv(UNSD / "cpc21-isic4.txt", dtype=str, keep_default_na=False).rename(
        columns={"CPC21code": "cpc", "ISIC4code": "clase"})
    sin_clase = d.clase == "n/a"
    residuos = d[sin_clase & d.cpc.str.startswith("39")].assign(clase=CLASE_RESIDUOS)
    return (repartir_igual(d[~sin_clase], "cpc", "clase"),
            repartir_igual(residuos, "cpc", "clase") if len(residuos) else residuos)


def hs92_a_clase(codigos: set[str]) -> pd.DataFrame:
    """(hs92, clase CIIU, peso, via) sin normalizar: la suma por hs92 es la masa que alcanzó una clase."""
    t12 = hs92_a_hs12(codigos)
    cpc = hs12_a_cpc()
    ext = extender_por_prefijo(set(t12.target), cpc)
    oficial, residuos = cpc_a_clase()
    partes = []
    for via_cpc, tabla_cpc in (("cadena", cpc), ("cadena_prefijo", ext)):
        if tabla_cpc.empty:
            continue
        c1 = componer(t12, tabla_cpc)
        for via_cls, tabla_cls in (("cadena", oficial), ("regla_residuos", residuos)):
            if tabla_cls.empty:
                continue
            r = componer(c1, tabla_cls).rename(columns={"source": "hs92", "target": "clase", "weight": "peso"})
            partes.append(r.assign(via=via_cpc if via_cpc != "cadena" else via_cls))
    return pd.concat(partes, ignore_index=True)


def codigos_hs92() -> pd.DataFrame:
    with zipfile.ZipFile(BACI_ZIP) as z, z.open("product_codes_HS92_V202601.csv") as f:
        return pd.read_csv(f, dtype=str).rename(columns={"code": "hs92", "description": "descripcion"})


def valor_mundial(anios: tuple[int, ...] = (2022, 2023, 2024)) -> pd.Series:
    v = pd.read_csv(VALORES, dtype={"product_hs92_code": str}, usecols=["product_hs92_code", "year", "export_value"])
    return v[v.year.isin(anios)].groupby("product_hs92_code").export_value.mean().rename("valor_mundial")


def nivel_confianza(peso_top: float, masa: float, via: str) -> str:
    """alta solo si domina un sector, casi toda la masa llegó a una clase y la vía es oficial."""
    if masa == 0:
        return "sin_mapeo"
    if peso_top >= 0.95 and masa >= 0.95 and via == "cadena":
        return "alta"
    return "media" if peso_top >= 0.6 else "baja"


def construir() -> pd.DataFrame:
    codigos = codigos_hs92()
    cls = hs92_a_clase(set(codigos.hs92))
    cls["sector_id"] = cls.clase.map(lambda c: (sectores_de_clase(c) or [""])[0])
    cls = cls[cls.sector_id != ""]
    por_sector = (cls.groupby(["hs92", "sector_id", "via"], as_index=False)
                  .agg(peso=("peso", "sum"), ciiu4=("clase", lambda s: ",".join(sorted(set(s))))))
    masa = por_sector.groupby("hs92").peso.sum().rename("masa_mapeada")
    por_sector = por_sector.join(masa, on="hs92")
    por_sector["peso"] = por_sector.peso / por_sector.masa_mapeada
    # un sector puede venir por varias vías: se suma el peso y se queda la vía más degradada
    por_sector["_o"] = por_sector.via.map(ORDEN_VIA)
    por_sector = (por_sector.sort_values("_o").groupby(["hs92", "sector_id"], as_index=False)
                  .agg(peso=("peso", "sum"), ciiu4=("ciiu4", lambda s: ",".join(sorted(set(",".join(s).split(","))))),
                       masa_mapeada=("masa_mapeada", "first"), _o=("_o", "max")))
    por_sector["via"] = por_sector._o.map({v: k for k, v in ORDEN_VIA.items()})
    por_sector = por_sector.drop(columns="_o")
    por_sector = por_sector[por_sector.hs92 != ARNES]
    arnes = pd.DataFrame([{"hs92": ARNES, "sector_id": sectores_de_clase(CLASE_ARNES)[0], "peso": 1.0,
                           "ciiu4": CLASE_ARNES, "masa_mapeada": 1.0, "via": "regla_especial"}])
    t = pd.concat([por_sector, arnes], ignore_index=True)
    via_codigo = t.assign(_o=t.via.map(ORDEN_VIA).fillna(0)).groupby("hs92")._o.max().map(
        {v: k for k, v in ORDEN_VIA.items()})
    t = t.join(t.groupby("hs92").peso.max().rename("peso_top"), on="hs92").join(via_codigo.rename("via_codigo"), on="hs92")
    t["confianza"] = [nivel_confianza(p, m, v) for p, m, v in zip(t.peso_top, t.masa_mapeada, t.via_codigo, strict=True)]
    t.loc[t.via == "regla_especial", "confianza"] = "alta"
    t = t.drop(columns="via_codigo")
    # códigos sin cadena: se reparten como sus hermanos de partida HS4, ponderado por valor mundial
    v = valor_mundial()
    rel = []
    for c in sorted(set(codigos.hs92) - set(t.hs92) - {NO_ESPECIFICADO}):
        hermanos = (t[t.hs92.str[:4] == c[:4]].merge(v, left_on="hs92", right_index=True, how="left")
                    .fillna({"valor_mundial": 1.0}))
        if hermanos.empty:
            continue
        g = hermanos.groupby("sector_id").valor_mundial.sum()
        g = g / g.sum()
        rel += [{"hs92": c, "sector_id": s, "peso": float(w), "ciiu4": "", "masa_mapeada": 0.0, "via": "fallback_hs4",
                 "peso_top": float(g.max()), "confianza": "baja"} for s, w in g.items()]
    t = pd.concat([t, pd.DataFrame(rel)], ignore_index=True)
    t["marca"] = ""
    t.loc[t.hs92 == ENERGIA, "marca"] = "excluir_energia_binacional"
    t.loc[t.hs92 == ARNES, "marca"] = "arnes"
    t.loc[t.hs92.isin(BIOCOMBUSTIBLE_POSIBLE), "marca"] = "biocombustible_posible"
    t = t.merge(codigos, on="hs92", how="left").join(v, on="hs92")
    sin_mapeo = codigos[~codigos.hs92.isin(t.hs92)].assign(
        sector_id="", peso=0.0, ciiu4="", masa_mapeada=0.0, via="", peso_top=0.0, confianza="sin_mapeo", marca="")
    cols = ["hs92", "descripcion", "sector_id", "peso", "ciiu4", "confianza", "via", "masa_mapeada", "marca",
            "valor_mundial"]
    out = pd.concat([t, sin_mapeo.join(v, on="hs92")], ignore_index=True)[cols]
    out.loc[out.hs92 == NO_ESPECIFICADO, "marca"] = "no_clasificable"
    return out.sort_values(["hs92", "peso"], ascending=[True, False], ignore_index=True)


def main() -> None:
    t = construir()
    t.to_csv(SALIDA, index=False, encoding="utf-8")
    por_codigo = t.drop_duplicates("hs92")
    print(f"{por_codigo.hs92.nunique()} códigos HS92; sectores TAPE usados: "
          f"{t[t.sector_id != ''].sector_id.nunique()} de {len(SECTORES)}")
    print(por_codigo.confianza.value_counts().to_dict())
    print(t.drop_duplicates("hs92").via.value_counts().to_dict())


if __name__ == "__main__":
    main()
