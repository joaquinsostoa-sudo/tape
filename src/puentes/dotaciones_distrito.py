"""Dotaciones por distrito distintas del capital humano: energía, logística y recursos (D33 y D35).

Cada capa tiene un equivalente territorial de lo que en el modelo nacional era un indicador por país (`docs/equivalencias_dotaciones.md`):
- **Energía**: potencia disponible (MW) de las subestaciones del mapa MIC, promedio 2026-2028 (redes 23 kV y 220/66 kV y su suma, que puede solaparse), con proximidad
  (D30: exp(−d/s), s = 15, 30 y 60 km) desde el punto de la ciudad del distrito a cada subestación; y distancia a la subestación de 220 kV o 500 kV más cercana. Mide disponibilidad, no precio.
- **Logística**: acceso a aduanas, puertos y pasos de frontera (distancia al más cercano y pool del comercio USD de los 35 puntos), km de ruta nacional del distrito y su pool, y
  distancia mínima a un polo (Asunción, Ciudad del Este, Encarnación, Puerto Central).
- **Recursos (D35)**: hectáreas de agricultura, pastura y plantación forestal de cada distrito (MapBiomas Paraguay, 2023) y su pool por proximidad; cada sector usa la clase de su materia prima.
  La medida antigua de D33 (hectáreas de fincas del Censo Agropecuario, dominadas por el Chaco) se conserva solo como `*_fincas`, descartada.
Cada índice es el promedio de los percentiles entre los 263 distritos de sus medidas (empates al valor más bajo, D29; las distancias, invertidas).
Son distancias en línea recta. El capital físico no se construye por distrito (lo reemplaza la densidad) y el crédito es un indicador del sector (D33).

Salida: `data/clean/dotaciones_distrito.csv`. Uso: uv run python -m src.puentes.dotaciones_distrito
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import base_capital_humano as bc
from .proximidad import ESCALA_PRINCIPAL, ESCALAS, pool
from .taxonomia_tape import RAIZ

C = RAIZ / "data" / "clean"
SALIDA = C / "dotaciones_distrito.csv"
ANIOS_POTENCIA = (2026, 2027, 2028)
ALTA_TENSION = ("220 kV", "500 kV")
POLOS = ("dist_asu_km", "dist_cde_km", "dist_enc_km", "dist_puerto_central_km")
CLASES_TIERRA = ("agricultura", "pastura", "plantacion_forestal")


def pool_puntos(coord_distritos: np.ndarray, coord_puntos: np.ndarray, valores: np.ndarray, escala: float) -> np.ndarray:
    """Pool de cada distrito: suma de `valores` de los puntos con el peso exp(−distancia / escala). Los distritos sin coordenadas quedan en NaN."""
    d = bc.distancia_km(coord_distritos[:, 0], coord_distritos[:, 1], coord_puntos[:, 0], coord_puntos[:, 1])
    p = np.nan_to_num(np.exp(-d / escala), nan=0.0) @ np.nan_to_num(np.asarray(valores, dtype=float), nan=0.0)
    return np.where(np.isnan(coord_distritos).any(axis=1), np.nan, p)


def distancia_minima(coord_distritos: np.ndarray, coord_puntos: np.ndarray) -> np.ndarray:
    """Distancia en km del punto de cada distrito al punto más cercano; NaN si el distrito no tiene coordenadas o no hay puntos."""
    if len(coord_puntos) == 0:
        return np.full(len(coord_distritos), np.nan)
    d = bc.distancia_km(coord_distritos[:, 0], coord_distritos[:, 1], coord_puntos[:, 0], coord_puntos[:, 1])
    return np.where(np.isnan(coord_distritos).any(axis=1), np.nan, np.where(np.isnan(d), np.inf, d).min(axis=1))


def potencia_por_subestacion(potencia: pd.DataFrame, subestaciones: pd.DataFrame, anios: tuple[int, ...] = ANIOS_POTENCIA) -> pd.DataFrame:
    """Potencia disponible media de los años dados, por subestación: MW en 23 kV, MW en 220/66 kV y su suma."""
    p = potencia[potencia["anio"].isin(anios)].groupby(["subestacion", "red"])["potencia_disp_mw"].mean().unstack()
    p = p.rename(columns={"23kV": "mw_23kv", "220/66kV": "mw_220_66kv"}).reindex(columns=["mw_23kv", "mw_220_66kv"]).fillna(0.0)
    p["mw_total"] = p["mw_23kv"] + p["mw_220_66kv"]
    return subestaciones.merge(p, left_on="nombre", right_index=True, how="left").fillna({"mw_23kv": 0.0, "mw_220_66kv": 0.0, "mw_total": 0.0})


def construir() -> pd.DataFrame:
    base = bc.distritos_base().reset_index(drop=True)
    coord = base[["lat", "lon"]].to_numpy(dtype=float)
    D = bc.distancia_km(coord[:, 0], coord[:, 1], coord[:, 0], coord[:, 1])
    x = base[["departamento", "distrito", "dep", "clave", "poblacion", "lat", "lon"]].copy()
    # energía
    sub = potencia_por_subestacion(pd.read_csv(C / "mic_potencia_disponible.csv"), pd.read_csv(C / "mic_subestaciones_localizadas.csv"))
    cs = sub[["lat", "lon"]].to_numpy(dtype=float)
    x["dist_subestacion_km"] = distancia_minima(coord, cs).round(1)
    x["dist_subestacion_220kv_km"] = distancia_minima(coord, sub.loc[sub["nivel_tension"].isin(ALTA_TENSION), ["lat", "lon"]].to_numpy(dtype=float)).round(1)
    # logística
    ad = pd.read_csv(C / "mic_aduanas_mapa_localizadas.csv")
    ca = ad[["lat", "lon"]].to_numpy(dtype=float)
    comercio = ad["imp_usd_cif"].fillna(0).to_numpy() + ad["exp_usd"].fillna(0).to_numpy()
    x["dist_aduana_km"] = distancia_minima(coord, ca).round(1)
    rutas = bc.a_clave_base(pd.read_csv(C / "mic_rutas_km_distrito.csv"), "departamento_geo", "distrito", base)
    km = rutas.groupby(["dep", "clave"])["km_ruta"].sum().rename("km_ruta_propio").reset_index()
    x = x.merge(km, on=["dep", "clave"], how="left").fillna({"km_ruta_propio": 0.0})
    ciu = pd.read_csv(C / "ciudades_mic.csv")
    x["dist_polo_min_km"] = ciu[list(POLOS)].min(axis=1).to_numpy()
    for c in POLOS:
        x[c] = ciu[c].to_numpy()
    # recursos
    fi = pd.read_csv(C / "can_fincas_distrito.csv")
    fi = pd.DataFrame({"dep": [bc.departamento(v) for v in fi["departamento"]], "clave": [bc.llave(v) for v in fi["ciudad"]], "superficie_ha": fi["superficie_ha"], "fincas": fi["fincas"]})
    x = x.merge(fi, on=["dep", "clave"], how="left")
    x["recursos_sin_dato"] = x["superficie_ha"].isna()
    mb = pd.read_csv(C / "mapbiomas_uso_distrito.csv")[["departamento", "distrito", "ha_agricultura_2023", "ha_pastura_2023", "ha_plantacion_forestal_2023", "ha_total", "pct_agricultura", "pct_pastura"]]
    x = x.merge(mb, on=["departamento", "distrito"], how="left")
    x["uso_suelo_sin_dato"] = x["ha_total"].isna()
    # pools e índices por escala
    for s in ESCALAS:
        for col in ("mw_23kv", "mw_220_66kv", "mw_total"):
            x[f"pool_{col}_{s}"] = pool_puntos(coord, cs, sub[col].to_numpy(), s)
        x[f"pool_comercio_usd_{s}"] = pool_puntos(coord, ca, comercio, s)
        x[f"pool_km_ruta_{s}"] = pool(D, x["km_ruta_propio"].to_numpy(), s)
        x[f"pool_superficie_ha_{s}"] = pool(D, x["superficie_ha"].to_numpy(), s)
        x[f"idx_energia_{s}"], _ = bc.indice(pd.DataFrame({"a": bc.percentil(x[f"pool_mw_total_{s}"]), "b": bc.percentil(x["dist_subestacion_220kv_km"], mayor_es_mejor=False)}))
        x[f"idx_logistica_{s}"], _ = bc.indice(pd.DataFrame({
            "a": bc.percentil(x[f"pool_comercio_usd_{s}"]), "b": bc.percentil(x["dist_aduana_km"], mayor_es_mejor=False),
            "c": bc.percentil(x[f"pool_km_ruta_{s}"]), "d": bc.percentil(x["dist_polo_min_km"], mayor_es_mejor=False)}))
        x[f"idx_recursos_fincas_{s}"] = bc.percentil(x[f"pool_superficie_ha_{s}"])  # descartado en D35: mide extensión
        for clase in CLASES_TIERRA:
            x[f"pool_ha_{clase}_{s}"] = pool(D, x[f"ha_{clase}_2023"].fillna(0.0).to_numpy(), s)
            x[f"idx_recursos_{clase}_{s}"] = bc.percentil(x[f"pool_ha_{clase}_{s}"]).where(~x["uso_suelo_sin_dato"])
    return x.drop(columns=["dep", "clave"]).round(3)


def main() -> None:
    x = construir()
    x.to_csv(SALIDA, index=False, encoding="utf-8")
    s = ESCALA_PRINCIPAL
    print(f"distritos {len(x)} | sin coordenadas: {int(x['lat'].isna().sum())} | sin dato de uso del suelo: {int(x['uso_suelo_sin_dato'].sum())} | con ruta nacional: {int((x['km_ruta_propio'] > 0).sum())}")
    indices = ["energia", "logistica", *[f"recursos_{c}" for c in CLASES_TIERRA]]
    for idx in indices:
        c = f"idx_{idx}_{s}"
        a, _, z = (x[f"idx_{idx}_{e}"] for e in (15, 30, 60))
        print(f"{c}: mediana {x[c].median():.1f} | más altos:", x.sort_values(c, ascending=False).head(5)["distrito"].tolist(), "| estabilidad 15 vs 60 km (rangos):", round(float(a.corr(z, method="spearman")), 2),
              "| cambian más de 10 puntos:", int(((a - z).abs() > 10).sum()))
    print("correlación de rangos entre índices (30 km) y con la población:")
    print(x[[f"idx_{i}_{s}" for i in indices] + ["poblacion"]].corr(method="spearman").round(2).to_string())


if __name__ == "__main__":
    main()
