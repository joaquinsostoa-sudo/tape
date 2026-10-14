"""Clasificación tecnológica de Lall (2000) llevada a productos HS4 (HS92), con confianza por fila.

Fuente: Lall, S. (2000), «The Technological Structure and Performance of Developing Country Manufactured Exports, 1985-98», QEH Working Paper 44
(Anexo, Tabla 1: 230 códigos SITC Rev.2 de 3 dígitos en diez subgrupos). Se lee del PDF por la posición de las tres columnas de la página.
Puente: SITC Rev.2 (4 dígitos) → SITC Rev.3 → HS92 (6 dígitos) con los pesos de las tablas de conversión del Atlas (cada código de origen suma 1); el voto
de cada clase para un HS6 es la suma de los productos de los dos pesos. Se agrega a HS4 con el valor mundial de cada HS6.

Clases (12): los diez subgrupos de Lall, con los primarios (PP) y las manufacturas basadas en recursos «otras» (RB2) divididos entre lo agropecuario y los
minerales y la energía. Bloques (6, decisión de presentación del cuadro de dotaciones, no de Lall): primarios agropecuarios, minerales y energía,
manufacturas agropecuarias, manufacturas de minerales, manufactura liviana, manufactura pesada y de tecnología media, manufactura de tecnología alta.
Confianza: alta (la clase o el bloque ganador reúne ≥ 0,8 de lo clasificado), media (0,5 a 0,8), baja (< 0,5); `sin_clasificar` si más de la mitad de la masa cae
en códigos que Lall no incluye (transacciones especiales, oro no monetario, etc.).

Salida: data/clean/clasificacion_lall_hs4.csv. Uso: uv run python -m src.puentes.clasificacion_lall
"""
from __future__ import annotations

import re

import pandas as pd

from src.descargas.comun import RAW

RAIZ = RAW.parents[1]
PDF = RAW / "clasificaciones_producto" / "lall" / "qehwps44.pdf"
CONV = RAW / "concordancias" / "atlas_conversion_hs"
PUENTE_SECTOR = RAIZ / "data" / "clean" / "puente_hs92_sector.csv"
SALIDA = RAIZ / "data" / "clean" / "clasificacion_lall_hs4.csv"
# (página, columna) -> [(posición vertical de inicio, subgrupo)]; los encabezados del Anexo, Tabla 1 fijan dónde cambia el subgrupo
_COLUMNAS_X = [68, 225, 382]
_ENCABEZADOS = {
    (34, 0): [(0, "PP")], (34, 1): [(0, "RB1"), (430, "RB2")], (34, 2): [(0, "LT1"), (320, "LT2")],
    (35, 0): [(0, "MT1"), (165, "MT2")], (35, 1): [(0, "MT3")], (35, 2): [(0, "HT1"), (230, "HT2")],
}
_PREFIJOS_PP_MINERAL = ("27", "3", "68")  # primarios que son minerales, combustibles y metales no ferrosos (SITC 27x, 3xx, 68x)
_RB2_MINERAL = {"281", "282", "286", "287", "288", "289", "323", "334", "335"}  # minerales metálicos, chatarra, coque y derivados del petróleo
BLOQUE_DE_CLASE = {
    "PP_agro": "primarios_agropecuarios", "PP_mineral": "minerales_y_energia", "RB1": "manufacturas_agropecuarias",
    "RB2_mineral": "minerales_y_energia", "RB2_otras": "manufacturas_de_minerales", "LT1": "manufactura_liviana",
    "LT2": "manufactura_liviana", "MT1": "manufactura_pesada_media_tec", "MT2": "manufactura_pesada_media_tec",
    "MT3": "manufactura_pesada_media_tec", "HT1": "manufactura_alta_tec", "HT2": "manufactura_alta_tec",
}


def clase(sitc2: str, subgrupo: str) -> str:
    """Clase de 12 categorías de un código SITC Rev.2 de 3 dígitos."""
    if subgrupo == "PP":
        return "PP_mineral" if sitc2.startswith(_PREFIJOS_PP_MINERAL) else "PP_agro"
    if subgrupo == "RB2":
        return "RB2_mineral" if sitc2 in _RB2_MINERAL else "RB2_otras"
    return subgrupo


def leer_lall(pdf: str | None = None) -> pd.DataFrame:
    """Los 230 códigos SITC Rev.2 de 3 dígitos del Anexo, Tabla 1, con su subgrupo y su clase (sitc2, nombre, subgrupo, clase)."""
    import pdfplumber

    filas = []
    with pdfplumber.open(str(pdf or PDF)) as doc:
        for n in (34, 35):
            palabras = doc.pages[n - 1].extract_words()
            for w in palabras:
                if re.fullmatch(r"\d{3}", w["text"]) and round(w["x0"]) in _COLUMNAS_X:
                    c = _COLUMNAS_X.index(round(w["x0"]))
                    limite = _COLUMNAS_X[c + 1] - 3 if c < 2 else 10_000
                    nombre = " ".join(p["text"] for p in sorted(palabras, key=lambda p: p["x0"])
                                      if abs(p["top"] - w["top"]) < 2.5 and w["x0"] < p["x0"] < limite)
                    sub = [g for y0, g in _ENCABEZADOS[(n, c)] if w["top"] >= y0][-1]
                    filas.append((w["text"], nombre, sub, clase(w["text"], sub)))
    return pd.DataFrame(filas, columns=["sitc2", "nombre", "subgrupo", "clase"]).drop_duplicates("sitc2").reset_index(drop=True)


def votos_hs6(lall: pd.DataFrame, sitc2_a_3: pd.DataFrame, sitc3_a_hs: pd.DataFrame) -> pd.DataFrame:
    """Para cada HS92 de 6 dígitos, la masa que cae en cada clase de Lall (columnas) y en `sin_clasificar`; cada fila suma 1."""
    grupo = dict(zip(lall.sitc2, lall.clase, strict=True))
    q = sitc2_a_3[sitc2_a_3.weight > 0].copy()
    q["clase"] = q.source_sitc2.str[:3].map(grupo).fillna("sin_clasificar")
    m = q.merge(sitc3_a_hs[sitc3_a_hs.weight > 0], left_on="target_sitc3", right_on="source_sitc3", suffixes=("_a", "_b"))
    m["v"] = m.weight_a * m.weight_b
    v = m.groupby(["target_hs92", "clase"]).v.sum().unstack(fill_value=0.0)
    return v.div(v.sum(axis=1), axis=0)


def _confianza(participacion: pd.Series) -> pd.Series:
    return pd.cut(participacion, [-1, 0.5, 0.8, 2], labels=["baja", "media", "alta"], right=False).astype(str)


def a_hs4(votos: pd.DataFrame, valor_hs6: pd.Series) -> pd.DataFrame:
    """Agrega a HS4 con el valor mundial de cada HS6 (peso 1 si no se conoce) y asigna la clase y el bloque ganadores con su confianza."""
    peso = valor_hs6.reindex(votos.index).fillna(0.0)
    peso = peso.where(peso > 0, 1.0)
    pond = votos.mul(peso, axis=0)
    pond["hs4"] = pond.index.str[:4]
    suma = pond.groupby("hs4").sum()
    total = suma.sum(axis=1)
    cl = suma.drop(columns="sin_clasificar", errors="ignore")
    bl = cl.T.groupby(cl.columns.map(BLOQUE_DE_CLASE)).sum().T
    out = pd.DataFrame({"hs4": suma.index})
    out["clase"], out["participacion_clase"] = cl.idxmax(axis=1).to_numpy(), (cl.max(axis=1) / cl.sum(axis=1)).to_numpy()
    out["bloque"], out["participacion_bloque"] = bl.idxmax(axis=1).to_numpy(), (bl.max(axis=1) / bl.sum(axis=1)).to_numpy()
    out["parte_sin_clasificar"] = (1 - cl.sum(axis=1) / total).to_numpy()
    out["confianza_clase"], out["confianza_bloque"] = _confianza(out.participacion_clase), _confianza(out.participacion_bloque)
    sin = out.parte_sin_clasificar > 0.5
    out.loc[sin, ["clase", "bloque"]] = "sin_clasificar"
    out.loc[sin, ["confianza_clase", "confianza_bloque"]] = "baja"
    return out.reset_index(drop=True)


def main() -> None:
    lall = leer_lall()
    s23 = pd.read_csv(CONV / "sitc2_to_sitc3.csv", dtype={"source_sitc2": str, "target_sitc3": str})
    s3h = pd.read_csv(CONV / "sitc3_to_hs92.csv", dtype={"source_sitc3": str, "target_hs92": str})
    valor = pd.read_csv(PUENTE_SECTOR, dtype={"hs92": str}).drop_duplicates("hs92").set_index("hs92").valor_mundial.astype(float)
    out = a_hs4(votos_hs6(lall, s23, s3h), valor)
    out.to_csv(SALIDA, index=False)
    print(f"{len(out)} productos HS4; bloques: {out.bloque.value_counts().to_dict()}")
    print(f"confianza del bloque: {out.confianza_bloque.value_counts().to_dict()}; de la clase: {out.confianza_clase.value_counts().to_dict()}")


if __name__ == "__main__":
    main()
