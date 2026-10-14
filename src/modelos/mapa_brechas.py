"""Mapa de brechas de compatibilidad: para todos los productos HS4, cuánto está Paraguay (o cualquier país) por debajo de quienes ya los producen, dotación por dotación.

Para un año t, con los países D8 y la presencia D13 (RCA ≥ 1 sostenido):
1. Posición de cada país en cada dotación: percentil entre los países de la muestra (0 = el menos dotado, 100 = el más dotado). Dotaciones (12): capital humano, capital
   por trabajador, logística, electricidad barata, mano de obra barata, impuesto bajo a las utilidades, tierra, agua y las reservas de petróleo, gas, carbón y minerales (el PIB per
   cápita no entra al índice).
2. Referencia por producto y dotación: mediana del percentil de los productores, sin el propio país, de dos formas: contra TODOS los productores y contra los de INGRESO
   SIMILAR (el mismo tercio de PIB per cápita). Con menos de `MINIMO` productores en la referencia de ingreso similar se usa la de todos y se marca.
3. Brecha = max(0, referencia − posición del país). Índice de incompatibilidad = promedio de las brechas de las dotaciones con dato (al menos 6 de 8); además, el cuello de botella
   (la dotación de mayor brecha) y el número de dotaciones fuera de tolerancia.
4. Tolerancia por dotación y por bloque de productos (Lall): percentil 75 de las brechas observadas en los pares país-producto del bloque que YA tienen presencia (países del mismo
   tercio de ingreso que el país), con un piso de `PISO_TOLERANCIA` puntos; con menos de `MIN_PARES` pares se usa la de todos los bloques. Así una dotación irrelevante para un bloque
   (las reservas para el cacao) no genera brechas falsas y una relevante (las reservas para los minerales) sí. Un producto es *compatible* si ninguna dotación supera su tolerancia (o si el índice no supera el percentil 75 del índice en esos pares). Variante: tolerancia
   calibrada solo con los productos que el país ya exporta.
5. Ámbitos: todos los productos, o solo los CERCANOS que todavía no exporta (RCA < 0,5, densidad en el cuartil superior de los no exportados).
Validación con un país dejado afuera: la referencia de cada país se calcula sin él; AUC de «menos el índice» para distinguir lo que exporta de lo que no, frente a la densidad.

Descriptivo: no prueba que cerrar una brecha lleve a producir. Uso: uv run python -m src.modelos.mapa_brechas
"""
from __future__ import annotations

import argparse
import warnings

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold

from src.modelos.bloques_dotaciones import dotaciones_del_anio, terciles
from src.modelos.densidad_np import densidad, matriz_presencia, proximidad
from src.modelos.logit_nacional import CLEAN, MODELO, calcular_rca, paises_elegibles, presencia

PAIS = "PRY"
CAPAS = {"hc": "Capital humano", "log_capital_trabajador": "Capital por trabajador", "lpi": "Logística (LPI)", "menos_log_precio": "Electricidad barata",
         "menos_log_salario": "Mano de obra barata", "menos_impuesto_utilidades": "Impuesto bajo a las utilidades", "log_tierra": "Tierra cultivable", "log_agua": "Agua dulce",
         "l_petroleo": "Reservas de petróleo", "l_gas": "Reservas de gas", "l_carbon": "Reservas de carbón", "riqueza_mineral": "Reservas de minerales"}
MINIMO = 5  # productores mínimos en una referencia
MIN_CAPAS = 9  # dotaciones con dato para calcular el índice (de 12)
MIN_PARES = 150  # pares con presencia mínimos para calibrar la tolerancia de un bloque
PISO_TOLERANCIA = 5.0
ANIO = 2019


def posiciones(dot: pd.DataFrame, paises: list[str], anio: int) -> pd.DataFrame:
    """Percentil (0 a 100) de cada país de `paises` en cada dotación; vacío donde no hay dato. Filas en el orden de `paises`."""
    d = dot[(dot.anio == anio) & dot.iso3.isin(paises)].set_index("iso3").reindex(paises)
    return d[list(CAPAS)].rank(pct=True) * 100


def _mediana(x: np.ndarray) -> np.ndarray:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        return np.nanmedian(x, axis=0)


def referencias(pct: np.ndarray, m: np.ndarray, grupo: np.ndarray, minimo: int = MINIMO) -> dict:
    """Referencias (países × productos × dotaciones) contra todos los productores y contra los de ingreso similar, sin el propio país, y cuántos productores sustentan cada una.

    `pct`: percentiles (países × dotaciones); `m`: presencia (países × productos, 0/1); `grupo`: tercio de ingreso de cada país (0, 1, 2)."""
    n_c, n_p = m.shape
    k = pct.shape[-1]
    ref_t = np.full((n_c, n_p, k), np.nan, np.float32)
    ref_g = np.full((n_c, n_p, k), np.nan, np.float32)
    n_t = np.zeros((n_c, n_p), np.int16)
    n_g = np.zeros((n_c, n_p), np.int16)
    for p in range(n_p):
        s = np.flatnonzero(m[:, p])
        if len(s) == 0:
            continue
        base = pct if pct.ndim == 2 else pct[:, p, :]  # con 3 dimensiones, la posición depende del producto
        ref_t[:, p, :], n_t[:, p] = _mediana(base[s]), len(s)
        for c in s:  # el propio país sale de su referencia
            otros = s[s != c]
            if len(otros):
                ref_t[c, p, :], n_t[c, p] = _mediana(base[otros]), len(otros)
            else:
                ref_t[c, p, :], n_t[c, p] = np.nan, 0
        for g in np.unique(grupo):
            filas = np.flatnonzero(grupo == g)
            sg = s[grupo[s] == g]
            if len(sg):
                ref_g[filas, p, :], n_g[filas, p] = _mediana(base[sg]), len(sg)
            for c in sg:
                otros = sg[sg != c]
                if len(otros):
                    ref_g[c, p, :], n_g[c, p] = _mediana(base[otros]), len(otros)
                else:
                    ref_g[c, p, :], n_g[c, p] = np.nan, 0
    ref_t[n_t < minimo] = np.nan
    usar_todos = n_g < minimo  # con pocos productores de ingreso similar se usa la referencia de todos
    ref_g_final = np.where(usar_todos[..., None], ref_t, ref_g)
    return {"todos": ref_t, "ingreso_similar": ref_g_final, "n_todos": n_t, "n_similar": n_g, "similar_con_respaldo": usar_todos & (n_t >= minimo)}


def brechas(pct: np.ndarray, ref: np.ndarray) -> np.ndarray:
    """Brecha (países × productos × dotaciones) = max(0, referencia − posición); vacía donde falta la referencia o el dato del país."""
    return np.maximum(0.0, ref - (pct[:, None, :] if pct.ndim == 2 else pct))


def indice(gap: np.ndarray, min_capas: int = MIN_CAPAS) -> np.ndarray:
    """Promedio de las brechas de las dotaciones con dato (al menos `min_capas`); vacío si hay menos."""
    con_dato = (~np.isnan(gap)).sum(axis=2)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        prom = np.nanmean(gap, axis=2)
    return np.where(con_dato >= min_capas, prom, np.nan)


def tolerancias(gap: np.ndarray, idx: np.ndarray, mascara: np.ndarray, bloque: np.ndarray, n_bloques: int, piso: float = PISO_TOLERANCIA,
                min_pares: int = MIN_PARES) -> tuple[np.ndarray, np.ndarray]:
    """Tolerancias por bloque (filas 0 a n_bloques - 1) y global (última fila): percentil 75 de la brecha de cada dotación y del índice entre los pares marcados por `mascara`
    (pares que ya tienen presencia), con un piso de `piso` puntos. Un bloque con menos de `min_pares` pares usa la tolerancia global. Devuelve (dotaciones, índice)."""
    k = gap.shape[2]
    tol, tol_idx = np.full((n_bloques + 1, k), np.nan), np.full(n_bloques + 1, np.nan)

    def calcular(sel: np.ndarray) -> tuple[np.ndarray, float]:
        if sel.sum() == 0:
            return np.full(k, np.nan), np.nan
        return np.maximum(np.nanpercentile(gap[sel], 75, axis=0), piso), float(max(np.nanpercentile(idx[sel], 75), piso))

    valido = mascara & ~np.isnan(idx)
    tol[n_bloques], tol_idx[n_bloques] = calcular(valido)
    for b in range(n_bloques):
        sel = valido & (bloque == b)[None, :]
        tol[b], tol_idx[b] = calcular(sel) if sel.sum() >= min_pares else (tol[n_bloques], tol_idx[n_bloques])
    return tol, tol_idx


def clasificar(gap: np.ndarray, idx: np.ndarray, tol: np.ndarray, tol_idx: np.ndarray, bloque: np.ndarray) -> pd.DataFrame:
    """Para un país (gap: productos × dotaciones; idx: productos; bloque: índice de bloque de cada producto, con n_bloques para los sin clasificar): dotaciones fuera de la
    tolerancia de su bloque, grado (índice / tolerancia del índice del bloque) y si es compatible."""
    fila, fila_idx = tol[bloque], tol_idx[bloque]
    fuera = np.nansum(gap > fila, axis=1)
    return pd.DataFrame({"n_fuera_tolerancia": fuera, "grado": idx / fila_idx, "compatible": (fuera == 0) & (idx <= fila_idx)})


def auc_por_pais(m: np.ndarray, puntaje: np.ndarray) -> np.ndarray:
    """AUC por país del puntaje (países × productos) para distinguir los productos con presencia de los que no; vacío si el país tiene menos de 3 presencias."""
    out = np.full(m.shape[0], np.nan)
    for c in range(m.shape[0]):
        ok = ~np.isnan(puntaje[c])
        y = m[c, ok]
        if 3 <= y.sum() < len(y):
            out[c] = roc_auc_score(y, puntaje[c, ok])
    return out


def validar(m: np.ndarray, dens: np.ndarray, idx_t: np.ndarray, idx_g: np.ndarray, paises: list[str]) -> pd.DataFrame:
    """AUC (promedio entre países y de Paraguay) de la densidad, del índice contra todos y contra ingreso similar (con signo negativo) y de logits con país dejado afuera (variables estandarizadas dentro de cada país)."""
    filas = []
    for nombre, puntaje in (("densidad", dens), ("menos índice (todos)", -idx_t), ("menos índice (ingreso similar)", -idx_g)):
        a = auc_por_pais(m, puntaje)
        filas.append({"puntaje": nombre, "auc_promedio_paises": float(np.nanmean(a)), "auc_mediana": float(np.nanmedian(a)), "auc_paraguay": float(a[paises.index(PAIS)]) if PAIS in paises else np.nan,
                      "paises": int(np.sum(~np.isnan(a)))})
    n_c, n_p = m.shape
    grupos = np.repeat(np.arange(n_c), n_p)
    y = m.ravel()

    def dentro(a: np.ndarray) -> np.ndarray:
        """Estandariza dentro de cada país: lo que importa para ordenar los productos de un país es la posición relativa, no el nivel entre países."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            a = np.where(np.isnan(a), np.nanmean(a, axis=1, keepdims=True), a)
        a = np.nan_to_num(a, nan=0.0)  # países sin dato del índice: neutros
        return ((a - a.mean(axis=1, keepdims=True)) / np.where(a.std(axis=1, keepdims=True) == 0, 1.0, a.std(axis=1, keepdims=True))).ravel()

    x_d, x_t, x_g = dentro(dens), dentro(idx_t), dentro(idx_g)
    for nombre, x in (("logit: solo densidad", np.column_stack([x_d])), ("logit: densidad + índice (todos)", np.column_stack([x_d, x_t])),
                      ("logit: densidad + índice (ingreso similar)", np.column_stack([x_d, x_g])), ("logit: densidad + los dos índices", np.column_stack([x_d, x_t, x_g]))):
        pred = np.zeros(len(y))
        for tr, te in GroupKFold(5).split(x, y, grupos):
            pred[te] = LogisticRegression(max_iter=500).fit(x[tr], y[tr]).predict_proba(x[te])[:, 1]
        a = auc_por_pais(m, pred.reshape(n_c, n_p))
        filas.append({"puntaje": nombre + " (países dejados afuera)", "auc_promedio_paises": float(np.nanmean(a)), "auc_mediana": float(np.nanmedian(a)),
                      "auc_paraguay": float(a[paises.index(PAIS)]) if PAIS in paises else np.nan, "paises": int(np.sum(~np.isnan(a)))})
    return pd.DataFrame(filas)


def construir(expo: pd.DataFrame, dot: pd.DataFrame, pob: pd.DataFrame, puente: pd.DataFrame, bloques: pd.DataFrame, anio: int = ANIO, pais: str = PAIS) -> dict:
    """Todo el mapa para `pais` en `anio`: tabla por producto, tolerancias, validación y metadatos."""
    dot = dotaciones_del_anio(dot, pob, puente, anio)
    muestra = paises_elegibles(expo, pob, anio)
    rca = calcular_rca(expo)
    rca_m = rca[rca.iso3.isin(muestra)]
    pres = presencia(rca_m, anio)
    m_mat, paises, productos = matriz_presencia(pres.rename(columns={"iso3": "country", "hs4": "product"}))
    paises = [str(p) for p in paises]
    phi = proximidad(m_mat)
    dens = densidad(m_mat, phi)
    pos = posiciones(dot, paises, anio)
    pib = dot[(dot.anio == anio) & dot.iso3.isin(paises)].set_index("iso3").reindex(paises).pib_pc_ppa
    tercio = terciles(pib).reindex(paises)
    grupo = tercio.map({"bajo": 0, "medio": 1, "alto": 2}).fillna(-1).to_numpy(int)
    pct = pos.to_numpy(np.float32)
    ref = referencias(pct, m_mat, grupo)
    gap_t, gap_g = brechas(pct, ref["todos"]), brechas(pct, ref["ingreso_similar"])
    idx_t, idx_g = indice(gap_t), indice(gap_g)
    i = paises.index(pais)
    misma = (grupo == grupo[i])[:, None] & (m_mat == 1)
    nombres_bloque = sorted(b for b in bloques.bloque.dropna().unique())
    cod = {b: k for k, b in enumerate(nombres_bloque)}
    nb = len(nombres_bloque)
    bl = pd.Series(productos).map(bloques.drop_duplicates("hs4").set_index("hs4").bloque.map(cod)).fillna(nb).to_numpy(int)
    tol_t, tol_idx_t = tolerancias(gap_t, idx_t, misma, bl, nb)
    tol_g, tol_idx_g = tolerancias(gap_g, idx_g, misma, bl, nb)
    propios = np.zeros_like(m_mat, dtype=bool)
    propios[i] = m_mat[i] == 1
    tol_p, tol_idx_p = tolerancias(gap_g, idx_g, propios, bl, nb, min_pares=10**9)  # variante: solo con los productos que el propio país ya exporta
    cl_t, cl_g = clasificar(gap_t[i], idx_t[i], tol_t, tol_idx_t, bl), clasificar(gap_g[i], idx_g[i], tol_g, tol_idx_g, bl)
    cl_p = clasificar(gap_g[i], idx_g[i], tol_p, tol_idx_p, bl)
    capas = list(CAPAS)
    tabla = pd.DataFrame({"hs4": productos, "presencia": m_mat[i].astype(bool), "densidad": dens[i], "productores": ref["n_todos"][i], "productores_ingreso_similar": ref["n_similar"][i],
                          "ref_ingreso_similar_con_respaldo": ref["similar_con_respaldo"][i]})
    r_pais = rca[(rca.anio == anio) & (rca.iso3 == pais)].set_index("hs4").rca
    tabla["rca"] = tabla.hs4.map(r_pais).fillna(0.0)
    tabla = tabla.merge(bloques[["hs4", "bloque", "confianza_bloque"]], on="hs4", how="left")
    for nombre, g, ix, cl in (("todos", gap_t[i], idx_t[i], cl_t), ("ingreso_similar", gap_g[i], idx_g[i], cl_g)):
        tabla[f"indice_{nombre}"] = ix
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            argmax = np.where(np.isnan(g).all(axis=1), -1, np.nanargmax(np.where(np.isnan(g), -1.0, g), axis=1))
        tabla[f"cuello_{nombre}"] = [CAPAS[capas[a]] if a >= 0 else None for a in argmax]
        tabla[f"fuera_tolerancia_{nombre}"] = cl["n_fuera_tolerancia"].to_numpy()
        tabla[f"grado_{nombre}"] = cl["grado"].to_numpy()
        tabla[f"compatible_{nombre}"] = cl["compatible"].to_numpy()
        for j, c in enumerate(capas):
            tabla[f"brecha_{nombre}_{c}"] = g[:, j]
    tabla["compatible_propios"] = cl_p["compatible"].to_numpy()
    no_exporta = (~tabla.presencia) & (tabla.rca < 0.5)
    corte = tabla.loc[no_exporta, "densidad"].quantile(0.75)
    tabla["cercano_no_exportado"] = no_exporta & (tabla.densidad >= corte)
    val = validar(m_mat, dens, idx_t, idx_g, paises)
    filas = []
    for k, nom in enumerate(nombres_bloque + ["global"]):
        for j, c in enumerate(capas + ["indice"]):
            def valor(tt: np.ndarray, ti: np.ndarray, k: int = k, j: int = j, c: str = c) -> float:
                return float(ti[k] if c == "indice" else tt[k, j])

            filas.append({"bloque": nom, "dotacion": "índice" if c == "indice" else CAPAS[c], "tolerancia_todos": valor(tol_t, tol_idx_t),
                          "tolerancia_ingreso_similar": valor(tol_g, tol_idx_g), "tolerancia_solo_propios": valor(tol_p, tol_idx_p)})
    tol = pd.DataFrame(filas)
    return {"tabla": tabla, "tolerancias": tol, "validacion": val, "anio": anio, "pais": pais, "paises": len(paises), "corte_densidad": float(corte), "productos": len(productos)}


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--expo", default=str(MODELO / "exportaciones_hs4.parquet"))
    ap.add_argument("--anio", type=int, default=ANIO)
    ap.add_argument("--pais", default=PAIS)
    args = ap.parse_args(argv)
    r = construir(pd.read_parquet(args.expo), pd.read_parquet(CLEAN / "dotaciones.parquet"), pd.read_csv(CLEAN / "poblacion_pais.csv"),
                  pd.read_csv(CLEAN / "puente_paises_baci.csv"), pd.read_csv(CLEAN / "clasificacion_lall_hs4.csv", dtype={"hs4": str}), args.anio, args.pais)
    t = r["tabla"]
    print(f"{r['pais']} {r['anio']}: {r['paises']} países, {r['productos']} productos; con presencia: {int(t.presencia.sum())}; cercanos no exportados: {int(t.cercano_no_exportado.sum())} (densidad ≥ {r['corte_densidad']:.3f})")
    print("\nTolerancias (puntos de percentil):")
    print(r["tolerancias"].round(1).to_string(index=False))
    print("\nValidación (AUC con país dejado afuera):")
    print(r["validacion"].round(3).to_string(index=False))
    for nombre in ("todos", "ingreso_similar"):
        nuevos = t[(~t.presencia) & (t.rca < 0.5)]
        print(f"\nCompatibles contra {nombre}: {int(nuevos[f'compatible_{nombre}'].sum())} de {len(nuevos)} productos sin ventaja; entre los cercanos no exportados: "
              f"{int(t[t.cercano_no_exportado][f'compatible_{nombre}'].sum())} de {int(t.cercano_no_exportado.sum())}")
    t.to_csv(MODELO / f"mapa_brechas_{r['pais']}_{r['anio']}.csv", index=False)
    r["tolerancias"].to_csv(MODELO / f"mapa_brechas_tolerancias_{r['pais']}_{r['anio']}.csv", index=False)
    r["validacion"].to_csv(MODELO / f"mapa_brechas_validacion_{r['anio']}.csv", index=False)


if __name__ == "__main__":
    main()
