"""Exporta el diagnóstico multi-capa (D36, D37) y los contornos de los distritos para la herramienta web (`web/tapeapp/src/data/`).

Salidas:
- `distritos_geo.json`: contorno simplificado de los distritos que tienen polígono propio (geoBoundaries ADM2, límites de 2012; D38).
- `diagnostico.json`: distritos (capas, producción, ubicación), sectores (capas exigidas, umbrales, complejidad, situación en el país) y celdas sector × distrito (clase del mapa,
  brechas, margen, nivel de política, estados por capa, escalón).
Los distritos creados después de 2012 no tienen polígono propio: se dibujan como un punto sobre el polígono de su padre y llevan `poligono = false`.

Uso: uv run python -m src.herramienta.exportar_diagnostico
"""
from __future__ import annotations

import json
import re
import unicodedata

import numpy as np
import pandas as pd
from shapely.geometry import MultiPolygon, mapping, shape
from shapely.geometry.polygon import orient

from ..puentes import base_capital_humano as bc
from ..puentes import diagnostico_multicapa as dm
from ..puentes.taxonomia_tape import RAIZ

ADM2 = RAIZ / "data" / "raw" / "limites_admin" / "geoBoundaries-PRY-ADM2.geojson"
SALIDA = RAIZ / "web" / "tapeapp" / "src" / "data"
TOLERANCIA = 0.002      # grados (unos 200 m): simplificación del contorno
DECIMALES = 4
CAPAS_DISTRITO = {"base": "indice_v2_30_principal", "energia": "idx_energia_30", "logistica": "idx_logistica_30", "agricultura": "idx_recursos_agricultura_30",
                  "pastura": "idx_recursos_pastura_30", "plantacion_forestal": "idx_recursos_plantacion_forestal_30"}
ESTADO_COD = {dm.SIN: "0", dm.CERCA: "1", dm.CON: "2"}
CLASES = ("sin brechas", "cerca del umbral", "una brecha", "dos o más brechas", "no apto por recursos", "datos incompletos", "sin referencia")
BANDA_RELATIVA = 10.0
MIN_SE_PRODUCE = 10
MIN_PRODUCE_POCO = 5


def normalizar(s: str) -> str:
    """Minúsculas, sin tildes ni signos (para cruzar nombres de distritos)."""
    t = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]", "", t)


def clase_celda(fila: pd.Series) -> int:
    """Clase del mapa de calor (D38, opción 3A): cinco clases ordenadas más datos incompletos y sin referencia."""
    if fila["situacion"] == "sin referencia":
        return 6
    if fila["situacion"] == "datos incompletos":
        return 5
    if fila["situacion"] == "no apto por recursos" or fila["apto_recursos"] is False or fila["apto_recursos"] == 0:
        return 4
    if fila["n_brechas"] >= 2:
        return 3
    if fila["n_brechas"] == 1:
        return 2
    return 1 if fila["n_cerca"] >= 1 else 0


def tercio(pct: pd.Series) -> pd.Series:
    """Simple / intermedia / compleja según el percentil de PCI del sector (tercios); vacío sin dato."""
    return pd.Series(np.where(pct.isna(), "", np.where(pct < 100 / 3, "simple", np.where(pct < 200 / 3, "intermedia", "compleja"))), index=pct.index)


def orientar(geom):
    """Anillos exteriores en sentido horario e interiores antihorario, que es lo que espera d3-geo (al revés, el polígono se dibuja como el mundo menos el distrito)."""
    if geom.geom_type == "Polygon":
        return orient(geom, sign=-1.0)
    return MultiPolygon([orient(p, sign=-1.0) for p in geom.geoms])


def poligonos(distritos: pd.DataFrame) -> tuple[dict, dict[str, str]]:
    """GeoJSON simplificado por distrito y, para los que no tienen polígono, el nombre de la unidad padre. Se cruza con el puente de distritos 2022 → nombre 2012 de geoBoundaries."""
    g = json.loads(ADM2.read_text(encoding="utf-8"))
    por_nombre = {normalizar(f["properties"]["shapeName"]): f for f in g["features"]}
    puente = pd.read_csv(RAIZ / "data" / "clean" / "puente_distritos_2022.csv")
    puente["dep"] = [bc.departamento(v) for v in puente["departamento"]]
    puente["clave"] = [bc.llave(v) for v in puente["distrito_2022"]]
    con2012 = puente.dropna(subset=["distrito_2012"]).drop_duplicates(["dep", "clave"]).set_index(["dep", "clave"])["distrito_2012"]
    sin = puente[puente["distrito_2012"].isna()].drop_duplicates(["dep", "clave"]).set_index(["dep", "clave"])["unidad_2011"]
    feats, padres = [], {}
    for r in distritos.itertuples():
        k = (r.dep, r.clave)
        nombre = con2012.get(k)
        f = por_nombre.get(normalizar(nombre)) if nombre is not None else None
        if f is None:
            padres[r.id] = str(sin.get(k, ""))
            continue
        geom = orientar(shape(f["geometry"]).simplify(TOLERANCIA, preserve_topology=True))
        geo = json.loads(json.dumps(mapping(geom)), parse_float=lambda x: round(float(x), DECIMALES))
        feats.append({"type": "Feature", "properties": {"id": r.id, "d": r.distrito, "dep": r.departamento}, "geometry": geo})
    return {"type": "FeatureCollection", "features": feats}, padres


def main() -> None:
    datos = dm.cargar()
    m = pd.read_csv(dm.M / "diagnostico_multicapa.csv", low_memory=False)
    refs = pd.read_csv(dm.M / "diagnostico_multicapa_referencias.csv")
    # distritos
    d = datos["prox"].merge(datos["dot"][["dep", "clave", "lat", "lon", *[c for c in CAPAS_DISTRITO.values() if c.startswith("idx_")]]], on=["dep", "clave"], how="left")
    d = d.assign(id=d["departamento"] + "|" + d["distrito"])
    ind = datos["ind"].groupby(["dep", "clave", "sector_id"])["n_industrias"].sum().reset_index()
    ind = ind[ind["n_industrias"] > 0]
    produce = ind.groupby(["dep", "clave"])["sector_id"].apply(sorted).to_dict()
    geo, padres = poligonos(d)
    ids_poligono = {f["properties"]["id"] for f in geo["features"]}
    lista = []
    for r in d.itertuples():
        capas = {k: (None if pd.isna(getattr(r, c)) else round(float(getattr(r, c)), 1)) for k, c in CAPAS_DISTRITO.items()}
        lista.append({"id": r.id, "departamento": r.departamento, "nombre": r.distrito, "poblacion": int(r.poblacion) if not pd.isna(r.poblacion) else None,
                      "lat": None if pd.isna(r.lat) else round(float(r.lat), 4), "lon": None if pd.isna(r.lon) else round(float(r.lon), 4),
                      "poligono": r.id in ids_poligono, "padre": padres.get(r.id, ""), "capas": capas, "produce": produce.get((r.dep, r.clave), [])})
    orden = {x["id"]: i for i, x in enumerate(lista)}
    # sectores
    s = m.groupby("sector_id").first().reset_index()
    s["pci_pct"] = s["pci_sector_pct"]
    con_ref = s["n_capas_evaluadas"] > 0
    mediana_pais = float(s.loc[con_ref, "pci_pct"].median())
    s["relativa"] = np.where(s["pci_pct"].isna(), "", np.where(s["pci_pct"] - mediana_pais > BANDA_RELATIVA, "más compleja", np.where(s["pci_pct"] - mediana_pais < -BANDA_RELATIVA, "menos compleja", "similar")))
    s["complejidad"] = tercio(s["pci_pct"])
    s["situacion_pais"] = np.where(s["n_productores_sector"] >= MIN_SE_PRODUCE, "se produce", np.where(s["n_productores_sector"] >= MIN_PRODUCE_POCO, "se produce poco", "sin referencia"))
    nombres = pd.read_csv(RAIZ / "data" / "clean" / "taxonomia_sectores_tape.csv").set_index("sector_id")["nombre"]
    sectores = []
    for r in s.itertuples():
        rr = refs[refs["sector_id"] == r.sector_id]
        umbrales = {x.capa: (None if pd.isna(x.umbral) else float(x.umbral)) for x in rr.itertuples()}
        conf = {x.capa: x.confianza for x in rr.itertuples()}
        sectores.append({"id": r.sector_id, "nombre": nombres.get(r.sector_id, r.sector_id), "capas": [c for c in r.capas_exigidas.split(",") if c] if isinstance(r.capas_exigidas, str) else [],
                         "capas_sin_dato": [c for c in str(r.capas_sin_dato).split(",") if c and c != "nan"], "n_productores": int(r.n_productores_sector), "umbrales": umbrales, "confianza": conf,
                         "pci_pct": None if pd.isna(r.pci_pct) else float(r.pci_pct), "cog_pct": None if pd.isna(r.cog_sector_pct) else float(r.cog_sector_pct),
                         "complejidad": r.complejidad, "relativa": r.relativa, "situacion_pais": r.situacion_pais, "con_referencia": bool(r.n_capas_evaluadas > 0)})
    # celdas
    cap_orden = list(dm.CAPAS)
    celdas = {}
    for sid, g in m.groupby("sector_id"):
        arr = [None] * len(lista)
        for r in g.itertuples():
            i = orden.get(f"{r.departamento}|{r.distrito}")
            if i is None:
                continue
            est = "".join(ESTADO_COD.get(getattr(r, f"{c}_estado"), "-") if isinstance(getattr(r, f"{c}_estado"), str) else "-" for c in cap_orden)
            fila = {"situacion": r.situacion, "n_brechas": r.n_brechas, "n_cerca": r.n_cerca, "apto_recursos": r.apto_recursos}
            clase = clase_celda(pd.Series(fila))
            nivel = -1 if pd.isna(r.nivel_politica) else int(r.nivel_politica)
            arr[i] = [clase, int(r.ya_produce), None if pd.isna(r.n_brechas) else int(r.n_brechas), None if pd.isna(r.margen_min) else float(r.margen_min), nivel, est,
                      None if pd.isna(r.rango_en_industria) else int(r.rango_en_industria), None if pd.isna(r.rango_en_distrito) else int(r.rango_en_distrito),
                      None if pd.isna(r.escalon_pci) else float(r.escalon_pci), r.capa_limitante if isinstance(r.capa_limitante, str) else ""]
        celdas[sid] = arr
    clase_tierra = pd.read_csv(RAIZ / "data" / "clean" / "exigencia_capas_sector.csv", dtype=str).fillna("").set_index("sector_id")["clase_tierra"]
    for x in sectores:
        x["clase_tierra"] = clase_tierra.get(x["id"], "")
    gadm = json.loads((SALIDA / "gadm41_PRY_1.json").read_text(encoding="utf-8"))
    especiales = {"asuncion": "capital", "presidentehayes": "ptehayes"}
    por_gid = {especiales.get(normalizar(f["properties"]["NAME_1"]), normalizar(f["properties"]["NAME_1"])): f["properties"]["GID_1"] for f in gadm["features"]}
    departamentos = [{"nombre": n, "gid": por_gid.get(normalizar(n), "")} for n in sorted({x["departamento"] for x in lista})]
    meta = {"version": "2026-10-17", "decisiones": "D36, D37, D38", "capas": cap_orden, "clases": list(CLASES), "mediana_pci_pais": round(mediana_pais, 1),
            "campos_celda": ["clase", "ya_produce", "n_brechas", "margen_min", "nivel_politica", "estados_por_capa", "rango_en_industria", "rango_en_distrito", "escalon_pci", "capa_limitante"],
            "aviso": "Descripción de distancias frente a quienes ya producen; no es una predicción ni una probabilidad. Resultados como asociación, no causalidad."}
    SALIDA.mkdir(parents=True, exist_ok=True)
    (SALIDA / "distritos_geo.json").write_text(json.dumps(geo, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    (SALIDA / "diagnostico.json").write_text(json.dumps({"meta": meta, "departamentos": departamentos, "distritos": lista, "sectores": sectores, "celdas": celdas}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"distritos {len(lista)} | con polígono {len(ids_poligono)} | sin polígono {len(lista) - len(ids_poligono)} (se dibujan como punto) | sectores {len(sectores)} | con referencia {int(con_ref.sum())}")
    for f in ("distritos_geo.json", "diagnostico.json"):
        print(f, round((SALIDA / f).stat().st_size / 1e6, 2), "MB")
    print("sin polígono:", [(x["nombre"], x["padre"]) for x in lista if not x["poligono"]])


if __name__ == "__main__":
    main()
