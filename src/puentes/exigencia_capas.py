"""¿Qué sectores exigen cada capa? Requisitos del bien por capa (D33), además de la formación específica (D28).

Nivel sector, media ponderada por el comercio mundial de cada producto como en D1 (`candidatos_sector.pesos_producto_sector`):
- **Energía**: intensidad energética (costo de energía / valor de envíos, NBER-CES). Exige si es ≥ la mediana de los productos con dato. Solo manufactura (el NBER no cubre agro, minería ni servicios).
- **Logística**: valor por kilo (BACI), en escala logarítmica. Un bien de bajo valor por kilo es pesado y depende más de la logística: exige si está por debajo de la mediana de los productos.
- **Recursos**: exige si el sector es agropecuario (S01 a S07) o de primera transformación (S09 a S21, S23 y S24). Lista elegida por Claude, ajustable.
- **Capital**: intensidad de capital (NBER-CES), **solo informativa** («inversión inicial exigida»): no es una capa distrital (la reemplaza la densidad).
Los sectores sin dato no se clasifican y no se imputan. Confianza según cuántos productos del sector tienen dato (10 o más alta, de 3 a 9 media, 1 o 2 baja).

Salida: `data/clean/exigencia_capas_sector.csv`. Uso: uv run python -m src.puentes.exigencia_capas
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..modelos.candidatos_sector import pesos_producto_sector
from .exigencia_sector import MANUFACTURA, confianza
from .taxonomia_tape import RAIZ

C = RAIZ / "data" / "clean"
SALIDA = C / "exigencia_capas_sector.csv"
RECURSOS = tuple([f"S{i:02d}" for i in range(1, 8)] + [f"S{i:02d}" for i in range(9, 22)] + ["S23", "S24"])


def media_ponderada(x: pd.DataFrame, valor: str) -> pd.DataFrame:
    """Media ponderada de `valor` por sector (peso w) y número de productos con dato."""
    y = x.dropna(subset=[valor])
    y = y[y["w"] > 0].assign(vw=lambda d: d[valor] * d["w"])
    g = y.groupby("sector_id").agg(vw=("vw", "sum"), w=("w", "sum"), n=("hs4", "nunique"))
    return pd.DataFrame({valor: g["vw"] / g["w"], f"n_{valor}": g["n"]})


def exigencia_capas(req: pd.DataFrame, pesos: pd.DataFrame, taxonomia: pd.DataFrame) -> pd.DataFrame:
    """Una fila por sector con el requisito de cada capa, si la exige y la confianza. `req` trae hs4, energia, capital y valor_peso_usd_kg; `pesos`, hs4, sector_id y w."""
    r = req.assign(log_valor_peso=np.log10(req["valor_peso_usd_kg"].where(req["valor_peso_usd_kg"] > 0)))
    med_energia, med_logvp = float(r["energia"].median()), float(r["log_valor_peso"].median())
    x = pesos.merge(r[["hs4", "energia", "capital", "log_valor_peso"]], on="hs4")
    manu = x[x["sector_id"].isin(MANUFACTURA)]
    out = taxonomia[["sector_id", "nombre"]].copy()
    for col, base in (("energia", manu), ("capital", manu), ("log_valor_peso", x)):
        out = out.merge(media_ponderada(base, col).reset_index(), on="sector_id", how="left")
    tiene = out["energia"].notna()
    out["exige_energia"] = np.where(tiene, np.where(out["energia"] >= med_energia, "si", "no"), "")
    out["confianza_energia"] = [confianza(int(n)) if t else "" for n, t in zip(out["n_energia"].fillna(0), tiene, strict=True)]
    tvp = out["log_valor_peso"].notna()
    out["exige_logistica"] = np.where(tvp, np.where(out["log_valor_peso"] <= med_logvp, "si", "no"), "")
    out["confianza_logistica"] = [confianza(int(n)) if t else "" for n, t in zip(out["n_log_valor_peso"].fillna(0), tvp, strict=True)]
    out["exige_recursos"] = np.where(out["sector_id"].isin(RECURSOS), "si", "no")
    out["capital_k_usd_trabajador"] = out["capital"].round(1)
    out["valor_peso_usd_kg"] = (10 ** out["log_valor_peso"]).round(2)
    out["mediana_energia_productos"] = round(med_energia, 4)
    out["mediana_valor_peso_productos"] = round(10 ** med_logvp, 2)
    return out.drop(columns=["capital", "log_valor_peso", "n_capital"]).round({"energia": 4})


def main() -> None:
    pu = pd.read_csv(C / "puente_hs92_sector.csv", dtype={"hs92": str})
    for c in ("peso", "valor_mundial"):
        pu[c] = pd.to_numeric(pu[c], errors="coerce")
    req = pd.read_csv(C / "requisitos_producto_hs4.csv", dtype={"hs4": str})
    o = exigencia_capas(req, pesos_producto_sector(pu), pd.read_csv(C / "taxonomia_sectores_tape.csv"))
    ex = pd.read_csv(C / "exigencia_formacion_sector.csv", dtype=str).fillna("")[["sector_id", "habilidades", "exige_formacion"]]
    o = o.merge(ex.rename(columns={"habilidades": "habilidades_nber"}), on="sector_id", how="left")
    o.to_csv(SALIDA, index=False, encoding="utf-8")
    print(f"medianas de los productos: energía {o['mediana_energia_productos'].iloc[0]} | valor por kilo USD {o['mediana_valor_peso_productos'].iloc[0]}")
    for capa in ("energia", "logistica", "recursos"):
        c = f"exige_{capa}"
        print(f"{capa}: exigen {int((o[c] == 'si').sum())} | no exigen {int((o[c] == 'no').sum())} | sin dato {int((o[c] == '').sum())}")
    m = o[o["sector_id"].isin(MANUFACTURA)]
    print("\nmanufactura: exige energía / logística / formación / recursos")
    print(m[["sector_id", "nombre", "energia", "exige_energia", "valor_peso_usd_kg", "exige_logistica", "exige_formacion", "exige_recursos", "capital_k_usd_trabajador"]].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
