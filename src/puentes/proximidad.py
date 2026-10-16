"""Proximidad geográfica del pool de capital humano (D30).

La gente no siempre trabaja donde vive o estudió: lo que hay en un distrito también es pool para los cercanos. Para el distrito j y una oferta v_i en cada distrito i:

    pool_j(s) = Σ_i exp(−d_ji / s) × v_i

con d_ji la distancia en línea recta entre los puntos de ciudad de los distritos (Censo 2022) y s = 15, 30 y 60 km (30 es la principal; la escala no se puede calibrar porque la
EPHC no trae traslado al trabajo). Es **disponibilidad** y no ocupación: una persona cuenta en varios distritos, así que los pools de distintos distritos no se suman.
Ofertas: (1) graduados de técnico y grado por sector, transversales y total; (2) sedes de educación superior; (3) PEA con secundaria completa (PEA × escolaridad estimada, D29);
(4) establecimientos de salud. Dos índices sin elegir uno: v1 (`base_capital_humano.py`) y v2 (promedio de percentiles de los pools de PEA con secundaria, salud y graduados transversales).

Salidas: `data/clean/proximidad_distrito.csv`, `data/clean/proximidad_graduados_sector.csv` y `data/clean/proximidad_control.csv`. Uso: uv run python -m src.puentes.proximidad
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import base_capital_humano as bc
from .taxonomia_tape import RAIZ
from .titulos_instituciones import (
    ajustar_distritos,
    leer_aneaes,
    leer_campus,
    leer_distritos,
    palabras,
)

BASE_CH = RAIZ / "data" / "clean" / "base_capital_humano_distrito.csv"
POR_SECTOR = RAIZ / "data" / "clean" / "titulos_sector_distrito.csv"
SALIDA = RAIZ / "data" / "clean" / "proximidad_distrito.csv"
SALIDA_SECTOR = RAIZ / "data" / "clean" / "proximidad_graduados_sector.csv"
SALIDA_CONTROL = RAIZ / "data" / "clean" / "proximidad_control.csv"
ESCALAS = (15, 30, 60)
ESCALA_PRINCIPAL = 30
ESCENARIOS = ("principal", "parejo")


def pesos(dist: np.ndarray, escala: float) -> np.ndarray:
    """Matriz de pesos exp(−d / escala). Donde falta la distancia (distrito sin coordenadas) el peso es 0."""
    w = np.exp(-np.asarray(dist, dtype=float) / escala)
    return np.nan_to_num(w, nan=0.0)


def pool(dist: np.ndarray, oferta: np.ndarray, escala: float) -> np.ndarray:
    """Pool de cada distrito: suma de la oferta de todos los distritos con el peso por distancia. Los distritos sin coordenadas quedan en NaN."""
    p = pesos(dist, escala) @ np.nan_to_num(np.asarray(oferta, dtype=float), nan=0.0)
    sin = np.isnan(dist).all(axis=1)
    return np.where(sin, np.nan, p)


def sedes_por_distrito(base: pd.DataFrame) -> pd.DataFrame:
    """Número de sedes de educación superior por distrito: pares (institución, distrito) distintos del listado del MEC 2018 y ANEAES (una institución cuenta una vez por distrito)."""
    dist = leer_distritos()
    mec, _ = ajustar_distritos(leer_campus(), dist)
    mec = bc.a_clave_base(mec, "nombre_departamento", "nombre_distrito", base)[["base", "dep", "clave"]]
    ane, _ = leer_aneaes(dist)
    claves = set(zip(base["dep"], base["clave"], strict=True))
    ane = ane[[(d, c) in claves for d, c in zip(ane["dep"], ane["clave"], strict=True)]][["base", "dep", "clave"]]
    x = pd.concat([mec, ane], ignore_index=True)
    canon: dict[frozenset[str], str] = {}
    x["inst"] = [canon.setdefault(palabras(b), b) for b in x["base"]]
    n = x.drop_duplicates(["inst", "dep", "clave"]).groupby(["dep", "clave"]).size().rename("sedes_propias").reset_index()
    return n


def percentil_pool(s: pd.Series) -> pd.Series:
    """Percentil entre distritos de un pool (mayor es mejor); empates al valor más bajo, igual que en la base (D29)."""
    return bc.percentil(s)


def construir() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    base = bc.distritos_base()
    ch = pd.read_csv(BASE_CH)
    ch["dep"] = [bc.departamento(v) for v in ch["departamento"]]
    ch["clave"] = [bc.llave(v) for v in ch["distrito"]]
    x = base.merge(ch[["dep", "clave", "escolaridad_pct", "salud_establecimientos_en_distrito", "indice_principal", "indice_parejo", "parcial"]], on=["dep", "clave"], how="left")
    x = x.merge(sedes_por_distrito(base), on=["dep", "clave"], how="left").fillna({"sedes_propias": 0})
    x = x.reset_index(drop=True)
    coord = x[["lat", "lon"]].to_numpy(dtype=float)
    D = bc.distancia_km(coord[:, 0], coord[:, 1], coord[:, 0], coord[:, 1])
    # graduados: técnico y grado, cada título una vez (totales) y transversales
    tot = pd.read_csv(bc.TOTALES, dtype={"unidad_2011": str}).fillna("")
    tot = tot[tot["nivel"].isin(["tecnico", "grado"]) & (tot["distrito"] != "")]
    tot = bc.a_clave_base(tot, "departamento", "distrito", base)
    for esc in ESCENARIOS:
        e = tot[tot["escenario"] == esc]
        a = e.groupby(["dep", "clave"])["titulos"].sum().rename(f"grad_propios_{esc}")
        b = e[e["tipo"] == "transversal"].groupby(["dep", "clave"])["titulos"].sum().rename(f"transversal_propios_{esc}")
        x = x.merge(a.reset_index(), on=["dep", "clave"], how="left").merge(b.reset_index(), on=["dep", "clave"], how="left")
    x = x.fillna({c: 0 for c in x.columns if c.startswith(("grad_propios", "transversal_propios"))})
    x["pea_secundaria_propia"] = x["pea"] * x["escolaridad_pct"] / 100
    ofertas = {"sedes": x["sedes_propias"].to_numpy(), "pea_secundaria": x["pea_secundaria_propia"].to_numpy(),
               "salud": x["salud_establecimientos_en_distrito"].fillna(0).to_numpy()}
    for esc in ESCENARIOS:
        ofertas[f"grad_{esc}"] = x[f"grad_propios_{esc}"].to_numpy()
        ofertas[f"transversal_{esc}"] = x[f"transversal_propios_{esc}"].to_numpy()
    for s in ESCALAS:
        for nombre, v in ofertas.items():
            x[f"pool_{nombre}_{s}"] = pool(D, v, s)
    # distancia a la sede de educación superior más cercana
    con_sede = x["sedes_propias"].to_numpy() > 0
    x["dist_sede_km"] = np.where(np.isnan(D).all(axis=1), np.nan, np.nanmin(np.where(con_sede[None, :], D, np.inf), axis=1)).round(1)
    # índices v2 (pools accesibles)
    for s in ESCALAS:
        for esc in ESCENARIOS:
            partes = pd.DataFrame({"a": bc.percentil(x[f"pool_pea_secundaria_{s}"]), "b": bc.percentil(x[f"pool_salud_{s}"]), "c": bc.percentil(x[f"pool_transversal_{esc}_{s}"])})
            x[f"indice_v2_{s}_{esc}"], x[f"partes_v2_{s}_{esc}"] = bc.indice(partes)
    x["pea_secundaria_incompleta"] = x["escolaridad_pct"].isna()
    # pools por sector (técnico y grado, cuenta completa)
    sec = pd.read_csv(POR_SECTOR, dtype={"unidad_2011": str}).fillna("")
    sec = sec[sec["nivel"].isin(["tecnico", "grado"]) & (sec["distrito"] != "") & (sec["sector_id"] != "")]
    sec = bc.a_clave_base(sec, "departamento", "distrito", base)
    filas = []
    idx = {(d, c): i for i, (d, c) in enumerate(zip(x["dep"], x["clave"], strict=True))}
    for (sector, esc), g in sec.groupby(["sector_id", "escenario"]):
        v = np.zeros(len(x))
        for d, c, t in zip(g["dep"], g["clave"], g["titulos"], strict=True):
            if (d, c) in idx:
                v[idx[(d, c)]] += t
        for s in ESCALAS:
            p = pool(D, v, s)
            filas.append(pd.DataFrame({"sector_id": sector, "escenario": esc, "escala_km": s, "departamento": x["departamento"], "distrito": x["distrito"], "propios": v.round(2), "pool": np.round(p, 2)}))
    por_sector = pd.concat(filas, ignore_index=True)
    por_sector = por_sector[(por_sector["propios"] > 0) | (por_sector["pool"].fillna(0) > 0)]
    # control
    ctrl = control(x, D)
    cols = (["departamento", "distrito", "poblacion", "pea", "escolaridad_pct", "sedes_propias", "dist_sede_km", "pea_secundaria_incompleta"]
            + [c for c in x.columns if c.startswith(("grad_propios", "transversal_propios", "pool_", "indice_v2_", "partes_v2_"))]
            + ["indice_principal", "indice_parejo", "parcial"])
    return x[cols].round(3), por_sector, ctrl


def control(x: pd.DataFrame, D: np.ndarray) -> pd.DataFrame:
    """Controles: con escala casi cero el pool coincide con la oferta propia; correlación de rangos del índice v2 entre escalas; distritos que cambian más de 10 puntos de percentil."""
    filas = []
    v = x["grad_propios_principal"].to_numpy()
    filas.append({"control": "pool con escala 0,01 km frente a la oferta propia (diferencia máxima)", "valor": float(np.nanmax(np.abs(pool(D, v, 0.01) - v)))})
    a, b, c = (x[f"indice_v2_{s}_principal"] for s in ESCALAS)
    filas += [{"control": "correlación de rangos del índice v2 entre 15 y 30 km", "valor": float(a.corr(b, method="spearman"))},
              {"control": "correlación de rangos del índice v2 entre 30 y 60 km", "valor": float(b.corr(c, method="spearman"))},
              {"control": "correlación de rangos del índice v2 entre 15 y 60 km", "valor": float(a.corr(c, method="spearman"))},
              {"control": "distritos que cambian más de 10 puntos de índice v2 entre 15 y 60 km", "valor": float(((a - c).abs() > 10).sum())},
              {"control": "correlación de rangos entre el índice v1 y el v2 (30 km)", "valor": float(x["indice_principal"].corr(b, method="spearman"))},
              {"control": "distritos con graduados transversales propios (sede principal)", "valor": float((x["transversal_propios_principal"] > 0).sum())}]
    for s in ESCALAS:
        filas.append({"control": f"distritos con pool transversal > 0 a escala {s} km (sede principal)", "valor": float((x[f"pool_transversal_principal_{s}"] > 0.5).sum())})
    return pd.DataFrame(filas)


def main() -> None:
    x, por_sector, ctrl = construir()
    x.to_csv(SALIDA, index=False, encoding="utf-8")
    por_sector.to_csv(SALIDA_SECTOR, index=False, encoding="utf-8")
    ctrl.to_csv(SALIDA_CONTROL, index=False, encoding="utf-8")
    print(f"distritos {len(x)} | filas por sector {len(por_sector):,}")
    print(ctrl.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
