"""Lista de sectores candidatos de un país (D1, opción a): puntuación por producto agregada a sector TAPE.

1. Se entrena el modelo de la tarea 1.11 (logit con efectos fijos de país, de producto y de ventana, y la densidad) con las ventanas de resultado conocido (2000, 2005, 2010 y 2015).
2. Se puntúan los **candidatos** del país en el año de corte (2024 por defecto): productos HS4 con RCA < 0,5 y sin presencia D13; φ y densidad con datos de los 5 años que terminan en el corte (D3).
   La ventana del corte es desconocida para el modelo (no cambia el orden dentro del país).
3. La puntuación del sector es la media de las puntuaciones de sus productos candidatos ponderada por el comercio mundial del producto (el peso de un HS4 en un sector es la fracción de su valor
   mundial que el puente HS → sector asigna a ese sector); respaldo: el máximo y el conteo de productos del sector entre los `TOP` mejores candidatos del país.
Son puntuaciones que ordenan candidatos, no probabilidades calibradas (D16).

Uso: uv run python -m src.modelos.candidatos_sector [--pais PRY] [--corte 2024]
"""
from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

from src.modelos import backtest_nacional as bt
from src.modelos.logit_nacional import CLEAN, MODELO, VENTANAS, H, construir_datos

TOP = 100
PAIS = "PRY"
CORTE = 2024


def pesos_producto_sector(puente: pd.DataFrame) -> pd.DataFrame:
    """Peso de cada HS4 en cada sector: fracción del valor mundial del HS4 que el puente asigna al sector (suma ≤ 1 por HS4; lo no mapeado a ningún sector no pesa)."""
    p = puente.assign(peso=puente.peso.astype(float), v=pd.to_numeric(puente.valor_mundial, errors="coerce").fillna(0.0), hs4=puente.hs92.str[:4])
    total = p.drop_duplicates("hs92").groupby("hs4").v.sum()
    p = p[p.sector_id.notna() & (p.sector_id != "")]
    num = p.assign(m=p.peso * p.v).groupby(["hs4", "sector_id"]).m.sum().reset_index()
    num["w"] = num.m / num.hs4.map(total).replace(0, np.nan)
    return num.dropna(subset=["w"])[["hs4", "sector_id", "w"]]


def valor_mundial_hs4(puente: pd.DataFrame) -> pd.Series:
    """Valor mundial de cada HS4 según el puente HS92 → sector (suma de los HS92 distintos del HS4)."""
    p = puente.drop_duplicates("hs92").assign(v=lambda d: pd.to_numeric(d.valor_mundial, errors="coerce").fillna(0.0), hs4=lambda d: d.hs92.str[:4])
    return p.groupby("hs4").v.sum()


def pesos_comercio(puente: pd.DataFrame) -> pd.DataFrame:
    """Pesos de D1 para promediar un requisito del producto en el sector (D37): `w` = fracción del HS4 asignada al sector por el valor mundial del HS4. Mismas columnas que `pesos_producto_sector`."""
    w = pesos_producto_sector(puente)
    return w.assign(w=w.w * w.hs4.map(valor_mundial_hs4(puente)).fillna(0.0))


def agregar_sector(cand: pd.DataFrame, pesos: pd.DataFrame, valor: pd.Series, top: int = TOP) -> pd.DataFrame:
    """Por sector: media ponderada, máximo, conteo en el top, producto líder y cuántos candidatos y productos tiene. `cand` trae hs4, puntaje y presente (bool); `valor` = comercio mundial por HS4."""
    c = cand.assign(valor=cand.hs4.map(valor).fillna(0.0))
    c["en_top"] = False
    c.loc[~c.presente, "en_top"] = c.loc[~c.presente, "puntaje"].rank(ascending=False, method="first") <= top  # el rango es entre candidatos
    m = pesos.merge(c, on="hs4", how="inner")
    m["peso_total"] = m.w * m.valor
    filas = []
    for s, g in m.groupby("sector_id"):
        no_pres = g[~g.presente]
        fila = {"sector_id": s, "productos_en_el_sector": len(g), "productos_presentes": int(g.presente.sum()), "productos_candidatos": len(no_pres)}
        if len(no_pres) and no_pres.peso_total.sum() > 0:
            lider = no_pres.loc[no_pres.puntaje.idxmax()]
            fila |= {"puntaje_medio": float(np.average(no_pres.puntaje, weights=no_pres.peso_total)), "puntaje_max": float(lider.puntaje), "producto_lider": lider.hs4,
                     "n_en_top": int(no_pres.en_top.sum())}
        else:
            fila |= {"puntaje_medio": np.nan, "puntaje_max": np.nan, "producto_lider": "", "n_en_top": 0}
        filas.append(fila)
    return pd.DataFrame(filas).sort_values("puntaje_medio", ascending=False, na_position="last").reset_index(drop=True)


def ventanas_conocidas(corte: int, ventanas=VENTANAS, h: int = H) -> tuple[int, ...]:
    """Ventanas de entrenamiento cuyo resultado (t0 + h) ya se conocía en el año de corte: sin esto, un corte antiguo vería el futuro."""
    return tuple(v for v in ventanas if v + h <= corte)


def puntuar_candidatos(expo: pd.DataFrame, dot: pd.DataFrame, req: pd.DataFrame, pob: pd.DataFrame, pais: str = PAIS, corte: int = CORTE) -> pd.DataFrame:
    """Puntuación (probabilidad del logit con densidad y efectos fijos, sin calibrar) de los candidatos del país en `corte`, y si el producto ya está presente."""
    ent = construir_datos(expo, dot, req, pob, ventanas=ventanas_conocidas(corte), solo_con_requisitos=False)  # todos los productos: la densidad no necesita requisitos
    pru = construir_datos(expo, dot, req, pob, ventanas=(corte,), h=0, solo_con_requisitos=False)  # h = 0: solo importa la grilla de candidatos y la densidad; E no se usa
    pru = pru[pru.iso3 == pais].assign(anio=max(VENTANAS))  # ventana desconocida: se reutiliza una conocida, que no cambia el orden dentro del país
    ent, pru = bt.estandarizar_densidad(ent.dropna(subset=["densidad"]), pru.dropna(subset=["densidad"]))
    pru = pru.assign(puntaje=bt.ajustar_y_predecir(ent, pru, ["d_z"]))
    return pru[["hs4", "densidad", "puntaje"]].assign(presente=False)


def main(argv: list[str] | None = None) -> None:
    import sys

    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pais", default=PAIS)
    ap.add_argument("--corte", type=int, default=CORTE)
    a = ap.parse_args(argv)
    expo = pd.read_parquet(MODELO / "exportaciones_hs4_depurado.parquet")
    cand = puntuar_candidatos(expo, pd.read_parquet(CLEAN / "dotaciones.parquet"), pd.read_csv(CLEAN / "requisitos_producto_hs4.csv", dtype={"hs4": str}), pd.read_csv(CLEAN / "poblacion_pais.csv"),
                              a.pais, a.corte)
    # productos presentes: los que tienen RCA ≥ 0,5 o presencia: se agregan con puntaje vacío para contarlos en el sector
    bruta = pd.read_parquet(MODELO / "exportaciones_hs4.parquet")
    valor = bruta[bruta.anio == a.corte].groupby("hs4").x.sum()
    todos = sorted(set(valor.index))
    nuevos = pd.DataFrame({"hs4": [h for h in todos if h not in set(cand.hs4)]})
    nuevos["puntaje"], nuevos["densidad"], nuevos["presente"] = np.nan, np.nan, True
    prod = pd.concat([cand, nuevos], ignore_index=True)
    pesos = pesos_producto_sector(pd.read_csv(CLEAN / "puente_hs92_sector.csv", dtype=str))
    tax = pd.read_csv(CLEAN / "taxonomia_sectores_tape.csv").set_index("sector_id")
    con_bienes = set(tax[tax.entra_en_comercio.astype(str) == "True"].index)  # los sectores de servicios no entran al espacio producto (algún HS suelto, como 4907, cae en ellos)
    s = agregar_sector(prod.assign(puntaje=prod.puntaje.fillna(0.0)), pesos[pesos.sector_id.isin(con_bienes)], valor)
    s["sector"] = s.sector_id.map(tax.nombre)
    s.to_csv(MODELO / f"candidatos_sector_{a.pais}_{a.corte}.csv", index=False)
    prod.sort_values("puntaje", ascending=False).to_csv(MODELO / f"candidatos_producto_{a.pais}_{a.corte}.csv", index=False)
    print(f"{a.pais} {a.corte}: {len(cand)} productos candidatos; {int(prod.presente.sum())} no candidatos (ya con ventaja o RCA ≥ 0,5)")
    print(s.head(20).round(4).to_string(index=False))


if __name__ == "__main__":
    main()
