"""Base de capital humano por distrito (D29): escolaridad, red de salud y carreras transversales, con un índice de pesos iguales.

Tres partes, declaradas en `docs/supuestos.md` (D29) antes de construir:
1. **Escolaridad**: % estimado de adultos de 25 a 64 años con 12 o más años de estudio. Tasa urbana y rural de cada departamento (EPHC 2022-2025 agrupadas) pesadas con el
   % urbano de la matrícula 2023 del distrito. Es una estimación (supone igual tasa en todos los distritos de un departamento y área); la EPHC no cubre Boquerón ni Alto Paraguay.
2. **Red de salud**: distancia en km al establecimiento de salud más cercano del mapa MIC (red parcial: 212 establecimientos).
3. **Carreras transversales**: títulos transversales de técnico y grado 2013-2025 por 1.000 habitantes, en los dos escenarios de sede (D17).
Índice = promedio de los percentiles entre distritos de las tres partes (la distancia, invertida; los empates toman el valor más bajo); si falta una parte se promedian las disponibles y queda marcado `parcial`.

Salidas: `data/clean/base_capital_humano_distrito.csv` y `data/clean/base_capital_humano_control.csv`. Uso: uv run python -m src.puentes.base_capital_humano
"""
from __future__ import annotations

import glob
from pathlib import Path

import numpy as np
import pandas as pd

from .distritos import departamento, llave, normalizar
from .taxonomia_tape import RAIZ
from .titulos_instituciones import ajustar_distritos

CIUDADES = RAIZ / "data" / "clean" / "ciudades_mic.csv"
SALUD = RAIZ / "data" / "clean" / "mic_salud_localizados.csv"
TOTALES = RAIZ / "data" / "clean" / "titulos_distrito.csv"
MATRICULAS = RAIZ / "data" / "raw" / "mec_escuelas" / "matriculaciones_departamentos_distritos_20261015.csv"
EPHC = RAIZ / "data" / "raw" / "ephc"
SALIDA = RAIZ / "data" / "clean" / "base_capital_humano_distrito.csv"
SALIDA_CONTROL = RAIZ / "data" / "clean" / "base_capital_humano_control.csv"
ANIOS_EPHC = (2022, 2023, 2024, 2025)
EDAD = (25, 64)
ANIOS_SECUNDARIA = 12
RADIO_TIERRA_KM = 6371.0088


def distritos_base(ruta: Path = CIUDADES) -> pd.DataFrame:
    """Los 263 distritos del Censo 2022 (ciudades del mapa MIC) con su clave: dep, clave, departamento, distrito, poblacion, lat, lon, dep_codigo."""
    c = pd.read_csv(ruta)
    return pd.DataFrame({
        "dep": [departamento(x) for x in c["departamento"]], "clave": [llave(x) for x in c["ciudad"]], "departamento": c["departamento"],
        "distrito": c["ciudad"], "dep_codigo": c["dep_codigo"], "poblacion": c["poblacion_2022"], "lat": c["lat"], "lon": c["lon"],
    })


def palabras_contenidas(nombre: str, candidatos: dict[str, str]) -> str | None:
    """Clave del único candidato cuyas palabras contienen las del nombre o están contenidas en ellas («Yegros» y «Fulgencio Yegros»). None si no hay uno solo."""
    a = set(normalizar(nombre).split()) - {"DE", "DEL", "LA", "EL"}
    hits = []
    for clave, otro in candidatos.items():
        b = set(normalizar(otro).split()) - {"DE", "DEL", "LA", "EL"}
        if a and b and (a <= b or b <= a):
            hits.append(clave)
    return hits[0] if len(hits) == 1 else None


def a_clave_base(df: pd.DataFrame, col_dep: str, col_dist: str, base: pd.DataFrame) -> pd.DataFrame:
    """Agrega las columnas dep y clave de la base a un DataFrame con departamento y distrito escritos de otra manera: nombre exacto, palabras contenidas y similitud."""
    x = df.assign(dep=[departamento(v) for v in df[col_dep]], nombre_distrito=df[col_dist], clave=[llave(v) for v in df[col_dist]])
    conocidas = set(zip(base["dep"], base["clave"], strict=True))
    claves = []
    for dep, nombre, clave in zip(x["dep"], x["nombre_distrito"], x["clave"], strict=True):
        if (dep, clave) not in conocidas:
            cand = dict(zip(base.loc[base["dep"] == dep, "clave"], base.loc[base["dep"] == dep, "distrito"], strict=True)) if "distrito" in base else {}
            clave = palabras_contenidas(nombre, cand) or clave
        claves.append(clave)
    x["clave"] = claves
    x, _ = ajustar_distritos(x, base[["dep", "clave"]].drop_duplicates())
    return x


def tasa_secundaria_ephc(anios: tuple[int, ...] = ANIOS_EPHC, raiz: Path = EPHC) -> pd.DataFrame:
    """% de adultos de 25 a 64 años con 12 o más años de estudio, por departamento (código EPHC) y área (1 urbana, 6 rural), años agrupados y ponderados por FACTOR."""
    partes = []
    for a in anios:
        archivos = glob.glob(str(raiz / str(a) / "REG02*"))
        if not archivos:
            continue
        d = pd.read_csv(archivos[0], sep=";", encoding="latin-1", usecols=lambda c: c in {"DPTO", "AREA", "P02", "FACTOR"} or c.upper().endswith("OEST"))
        est = next(c for c in d.columns if c.upper().endswith("OEST"))
        d = d.rename(columns={est: "anios"}).assign(anio=a)
        for c in ("DPTO", "AREA", "P02", "FACTOR", "anios"):
            d[c] = pd.to_numeric(d[c], errors="coerce")
        partes.append(d)
    d = pd.concat(partes, ignore_index=True)
    d = d[d["P02"].between(*EDAD) & d["anios"].notna() & (d["anios"] < 90) & d["FACTOR"].notna()]
    d = d.assign(sec=(d["anios"] >= ANIOS_SECUNDARIA).astype(float), pesada=lambda x: x["sec"] * x["FACTOR"])
    g = d.groupby(["DPTO", "AREA"]).agg(pesada=("pesada", "sum"), factor=("FACTOR", "sum"), n=("sec", "size")).reset_index()
    g["tasa"] = 100 * g["pesada"] / g["factor"]
    tot = d.groupby("DPTO").agg(pesada=("pesada", "sum"), factor=("FACTOR", "sum")).reset_index()
    tot["tasa_dep"] = 100 * tot["pesada"] / tot["factor"]
    g = g.merge(tot[["DPTO", "tasa_dep"]], on="DPTO")
    return g[["DPTO", "AREA", "tasa", "tasa_dep", "n"]].rename(columns={"DPTO": "dep_codigo", "AREA": "area"})


def porcentaje_urbano_matricula(ruta: Path = MATRICULAS) -> pd.DataFrame:
    """% de la matrícula 2023 de cada distrito que está en establecimientos urbanos (todos los niveles y tipos de gestión)."""
    m = pd.read_csv(ruta)
    m = m.assign(total=m["cantidad_matriculados_hombre"] + m["cantidad_matriculados_mujer"])
    g = m.groupby(["nombre_departamento", "nombre_distrito", "nombre_zona"])["total"].sum().unstack(fill_value=0).reset_index()
    g["matricula"] = g.get("Urbana", 0) + g.get("Rural", 0)
    g["urbano"] = g.get("Urbana", 0) / g["matricula"].where(g["matricula"] > 0)
    return g[["nombre_departamento", "nombre_distrito", "matricula", "urbano"]]


def escolaridad_distrito(urbano: float, tasa_urbana: float, tasa_rural: float) -> float:
    """Tasa del distrito = % urbano × tasa urbana del departamento + (1 − % urbano) × tasa rural. Si falta el área que pesa algo, no hay estimación."""
    if pd.isna(urbano):
        return float("nan")
    if urbano > 0 and pd.isna(tasa_urbana) or urbano < 1 and pd.isna(tasa_rural):
        return float("nan")
    return float((urbano * (tasa_urbana if urbano > 0 else 0.0)) + ((1 - urbano) * (tasa_rural if urbano < 1 else 0.0)))


def distancia_km(lat: np.ndarray, lon: np.ndarray, lat2: np.ndarray, lon2: np.ndarray) -> np.ndarray:
    """Distancia en línea recta (fórmula de Haversine) entre cada punto (lat, lon) y cada punto (lat2, lon2): matriz de n × m, en km."""
    a1, o1, a2, o2 = (np.radians(np.asarray(v, dtype=float)) for v in (lat, lon, lat2, lon2))
    da = a2[None, :] - a1[:, None]
    do = o2[None, :] - o1[:, None]
    h = np.sin(da / 2) ** 2 + np.cos(a1)[:, None] * np.cos(a2)[None, :] * np.sin(do / 2) ** 2
    return 2 * RADIO_TIERRA_KM * np.arcsin(np.sqrt(h))


def percentil(s: pd.Series, mayor_es_mejor: bool = True) -> pd.Series:
    """Percentil (0 a 100) entre los distritos: el 0 es el peor y el 100 el mejor. Los empates toman el valor más bajo, de modo que una masa de distritos con cero
    (por ejemplo sin graduados) queda abajo y no a mitad de tabla. Con mayor_es_mejor=False se invierte (la distancia a salud)."""
    v = s if mayor_es_mejor else -s
    n = int(v.notna().sum())
    return 100 * (v.rank(method="min", na_option="keep") - 1) / (n - 1)


def indice(partes: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Promedio simple de las partes disponibles y cuántas partes hay. Si falta alguna, el índice se calcula con las demás y se marca parcial."""
    return partes.mean(axis=1, skipna=True), partes.notna().sum(axis=1)


def construir() -> tuple[pd.DataFrame, pd.DataFrame]:
    base = distritos_base()
    tasas = tasa_secundaria_ephc()
    # escolaridad
    mat = a_clave_base(porcentaje_urbano_matricula(), "nombre_departamento", "nombre_distrito", base)[["dep", "clave", "matricula", "urbano"]]
    x = base.merge(mat, on=["dep", "clave"], how="left")
    urb = tasas[tasas["area"] == 1].set_index("dep_codigo")["tasa"]
    rur = tasas[tasas["area"] == 6].set_index("dep_codigo")["tasa"]
    x["tasa_urbana_dep"] = x["dep_codigo"].map(urb)
    x["tasa_rural_dep"] = x["dep_codigo"].map(rur)
    x["escolaridad_pct"] = [escolaridad_distrito(u, a, b) for u, a, b in zip(x["urbano"], x["tasa_urbana_dep"], x["tasa_rural_dep"], strict=True)]
    x["confianza_escolaridad"] = np.where(x["escolaridad_pct"].notna(), "media", "")
    # salud
    s = pd.read_csv(SALUD)
    d = distancia_km(x["lat"].to_numpy(), x["lon"].to_numpy(), s["lat"].to_numpy(), s["lon"].to_numpy())
    x["salud_km"] = d.min(axis=1).round(1)
    x["salud_establecimientos_en_distrito"] = 0
    if "distrito" in s.columns:
        sd = a_clave_base(s.dropna(subset=["distrito", "departamento_geo"]) if "departamento_geo" in s.columns else s, "departamento_geo" if "departamento_geo" in s.columns else "departamento", "distrito", base)
        cuenta = sd.groupby(["dep", "clave"]).size().rename("n").reset_index()
        x = x.merge(cuenta, on=["dep", "clave"], how="left")
        x["salud_establecimientos_en_distrito"] = x.pop("n").fillna(0).astype(int)
    # carreras transversales
    t = pd.read_csv(TOTALES, dtype={"unidad_2011": str}).fillna("")
    t = t[(t["tipo"] == "transversal") & t["nivel"].isin(["tecnico", "grado"]) & (t["distrito"] != "")]
    t = a_clave_base(t, "departamento", "distrito", base)
    piv = t.groupby(["dep", "clave", "escenario"])["titulos"].sum().unstack(fill_value=0).reset_index()
    x = x.merge(piv, on=["dep", "clave"], how="left")
    for esc in ("principal", "parejo"):
        x[f"transversal_x1000_{esc}"] = (x.pop(esc).fillna(0) if esc in x else 0) / x["poblacion"] * 1000
    # percentiles e índice
    x["p_escolaridad"] = percentil(x["escolaridad_pct"])
    x["p_salud"] = percentil(x["salud_km"], mayor_es_mejor=False)
    for esc in ("principal", "parejo"):
        x[f"p_transversal_{esc}"] = percentil(x[f"transversal_x1000_{esc}"])
        x[f"indice_{esc}"], x[f"partes_{esc}"] = indice(x[["p_escolaridad", "p_salud", f"p_transversal_{esc}"]])
    x["parcial"] = x["partes_principal"] < 3
    cols = ["departamento", "distrito", "poblacion", "matricula", "urbano", "tasa_urbana_dep", "tasa_rural_dep", "escolaridad_pct", "confianza_escolaridad",
            "salud_km", "salud_establecimientos_en_distrito", "transversal_x1000_principal", "transversal_x1000_parejo", "p_escolaridad", "p_salud",
            "p_transversal_principal", "p_transversal_parejo", "indice_principal", "indice_parejo", "partes_principal", "parcial"]
    out = x[cols].round(3)
    # control: promedio de las tasas de los distritos (pesado por población) frente a la tasa departamental de la EPHC
    ok = x[x["escolaridad_pct"].notna()]
    ctrl = ok.groupby(["dep_codigo", "departamento"]).apply(
        lambda g: pd.Series({"estimado_ponderado": np.average(g["escolaridad_pct"], weights=g["poblacion"]), "distritos": len(g)}), include_groups=False).reset_index()
    ctrl = ctrl.merge(tasas.drop_duplicates("dep_codigo")[["dep_codigo", "tasa_dep"]], on="dep_codigo", how="left")
    ctrl["diferencia"] = ctrl["estimado_ponderado"] - ctrl["tasa_dep"]
    return out, ctrl.round(2)


def main() -> None:
    out, ctrl = construir()
    out.to_csv(SALIDA, index=False, encoding="utf-8")
    ctrl.to_csv(SALIDA_CONTROL, index=False, encoding="utf-8")
    print(f"distritos {len(out)} | con escolaridad {int(out['escolaridad_pct'].notna().sum())} | índice parcial {int(out['parcial'].sum())}")
    print("control (diferencia entre el estimado ponderado y la EPHC departamental, en puntos):")
    print(ctrl.to_string(index=False))


if __name__ == "__main__":
    main()
