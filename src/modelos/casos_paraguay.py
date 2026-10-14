"""Casos de Paraguay (prueba C de la declaración del 2026-10-14 en docs/supuestos.md): ¿el modelo marcaba arneses, frigoríficos y biocombustibles antes del despegue?

Casos definidos por tablas ya existentes: arneses = HS4 8544; frigoríficos = HS4 con al menos 50 % de su masa en el sector S09 del puente HS; biocombustibles = HS4 con marca
`biocombustible_posible`. Eventos = entradas de Paraguay (D7) en esos productos en las ventanas de prueba 2005, 2010 y 2015 del backtest nacional (D2 a), con la tabla de exportaciones depurada (alcance a).
Para cada evento: percentil de rango del producto entre todas las filas de Paraguay de la ventana ordenadas por probabilidad (0 = primero) con `densidad_sola` y con `capas`. Marcado = percentil ≤ 10 %.
Criterio principal: el modelo «anticipaba» los casos si la mitad o más de los eventos quedan marcados por `densidad_sola`. Descriptivo (muy pocos eventos); sin inferencia.

Uso: uv run python -m src.modelos.casos_paraguay [--expo RUTA]
"""
from __future__ import annotations

import argparse

import pandas as pd

from src.modelos import backtest_nacional as bt
from src.modelos.logit_nacional import CLEAN, MODELO, VENTANAS, H, construir_datos

PAIS = "PRY"
UMBRAL = 0.10
ARNESES = ("8544",)
MARCAS_BIO = "biocombustible_posible"


def conjuntos_de_casos(puente: pd.DataFrame, minimo: float = 0.5) -> dict[str, list[str]]:
    """HS4 de cada caso desde el puente HS → sector: arneses (8544), frigoríficos (≥ `minimo` de la masa mapeada en S09) y biocombustibles (marca del puente)."""
    p = puente.assign(peso=puente.peso.astype(float), v=pd.to_numeric(puente.valor_mundial, errors="coerce").fillna(0.0), hs4=puente.hs92.str[:4])
    p["masa"] = p.v * p.peso
    total, s09 = p.groupby("hs4").masa.sum(), p[p.sector_id == "S09"].groupby("hs4").masa.sum()
    frig = sorted((s09 / total).dropna().loc[lambda s: s >= minimo].index)
    bio = sorted(p[p.marca.fillna("").str.contains(MARCAS_BIO)].hs4.unique())
    return {"arneses": list(ARNESES), "frigorificos": frig, "biocombustibles": bio}


def percentil_de_rango(puntajes: pd.Series, producto: str) -> float:
    """Posición del `producto` entre los candidatos ordenados de mayor a menor puntaje, en [0, 1]; 0 = primero (empates: el peor puesto)."""
    mayores = int((puntajes > puntajes[producto]).sum())
    iguales = int((puntajes == puntajes[producto]).sum())
    return (mayores + iguales - 1) / max(len(puntajes) - 1, 1)


def eventos_ventana(res: dict, casos: dict[str, list[str]], t0: int, pais: str = PAIS) -> pd.DataFrame:
    """Entradas de `pais` en los productos de `casos` en la ventana `t0`, con percentil de rango y puesto con densidad sola y capas."""
    pru = res["prueba"].reset_index(drop=True)
    marca = (pru.iso3 == pais).to_numpy()
    fila = pru[marca].reset_index(drop=True)
    filas = []
    s = {n: pd.Series(res["puntajes"][n][marca], index=fila.hs4) for n in ("densidad_sola", "capas")}
    for caso, productos in casos.items():
        for h in productos:
            if h in s["capas"].index and int(fila.loc[fila.hs4 == h, "E"].iloc[0]) == 1:
                r = {"caso": caso, "hs4": h, "ventana": t0, "candidatos": len(fila)}
                for n, ser in s.items():
                    r[f"percentil_{n}"] = percentil_de_rango(ser, h)
                    r[f"puesto_{n}"] = int((ser > ser[h]).sum()) + 1
                filas.append(r)
    return pd.DataFrame(filas)


def veredicto(ev: pd.DataFrame, umbral: float = UMBRAL) -> dict[str, float]:
    """Cuántos eventos quedan marcados (percentil ≤ umbral) con la densidad sola y con las capas, y si se cumple el criterio (la mitad o más con la densidad)."""
    if ev.empty:
        return {"eventos": 0, "marcados_densidad": 0, "marcados_capas": 0, "anticipaba": float("nan")}
    md, mc = int((ev.percentil_densidad_sola <= umbral).sum()), int((ev.percentil_capas <= umbral).sum())
    return {"eventos": len(ev), "marcados_densidad": md, "marcados_capas": mc, "anticipaba": float(md / len(ev) >= 0.5)}


def main(argv: list[str] | None = None) -> None:
    import sys

    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--expo", default=str(MODELO / "exportaciones_hs4_depurado.parquet"))
    ap.add_argument("--salida", default=str(MODELO / "casos_paraguay.csv"))
    args = ap.parse_args(argv)
    casos = conjuntos_de_casos(pd.read_csv(CLEAN / "puente_hs92_sector.csv", dtype=str))
    for k, v in casos.items():
        print(f"{k}: {len(v)} productos HS4 {v if len(v) < 25 else ''}")
    df = construir_datos(pd.read_parquet(args.expo), pd.read_parquet(CLEAN / "dotaciones.parquet"), pd.read_csv(CLEAN / "requisitos_producto_hs4.csv", dtype={"hs4": str}),
                         pd.read_csv(CLEAN / "poblacion_pais.csv"))
    ev = []
    for t in (v for v in VENTANAS if bt.ventanas_previas(v)):
        res = bt.evaluar_ventana(df, t)
        e = eventos_ventana(res, casos, t)
        n_pry = int((res["prueba"].iso3 == PAIS).sum())
        ent = int(res["prueba"][res["prueba"].iso3 == PAIS].E.sum())
        print(f"\n=== Ventana {t} → {t + H}: {n_pry} candidatos de Paraguay, {ent} entradas en total, {len(e)} en los casos")
        if len(e):
            print(e.round(3).to_string(index=False))
        ev.append(e)
    ev = pd.concat([e for e in ev if len(e)], ignore_index=True) if any(len(e) for e in ev) else pd.DataFrame()
    print("\nVeredicto:", veredicto(ev))
    ev.to_csv(args.salida, index=False)


if __name__ == "__main__":
    main()
