"""
Test de las 3 hipotesis sobre las capas (tarea 1.9).

Test 1 - Capa por capa CON efectos fijos de pais y producto.
Test 2 - PCA de las 4 capas CON efectos fijos.
Test 3 - Capas SIN efectos fijos de pais (solo efectos de producto).

Uso:
    python -m src.modelos.test_capas --db RUTA --dotaciones RUTA
"""

import argparse
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA

from src.modelos.logit_disperso import LogitEfectosFijos
from src.modelos.evaluacion import precision_at_k, auc_pr

VENTANAS = [
    (2000, 2005, "densidad_1995_1999"),
    (2005, 2010, "densidad_2000_2004"),
    (2010, 2015, "densidad_2005_2009"),
    (2015, 2020, "densidad_2010_2014"),
]
CAPAS = ["capital_humano", "credito", "energia", "logistica"]


def cargar_dotaciones(ruta: Path) -> pd.DataFrame:
    if str(ruta).endswith(".csv"):
        return pd.read_csv(ruta)
    return pd.read_parquet(ruta)


def cargar_panel(con, t0, t1, tabla_dens, dot, puente):
    df = con.execute(f"""
        SELECT p.country, p.product, p.E, d.densidad
        FROM panel_{t0}_{t1} p
        LEFT JOIN {tabla_dens} d
          ON p.country = d.country AND p.product = d.product
        WHERE d.densidad IS NOT NULL
    """).fetchdf()

    if len(df) == 0:
        return None

    mapa = dict(zip(puente.codigo_baci, puente.iso3))
    df["iso3"] = df["country"].map(mapa)

    cols_dot = [f"z_{c}" for c in CAPAS]
    dot_t0 = dot[dot.anio == t0][["iso3", *cols_dot]]
    df = df.merge(dot_t0, on="iso3", how="left")

    # Imputar NaN con 0 (media de las capas estandarizadas)
    for c in cols_dot:
        df[c] = df[c].fillna(0.0)

    df["densidad_z"] = (df["densidad"] - df["densidad"].mean()) / df["densidad"].std()
    df["densidad_z"] = df["densidad_z"].fillna(0.0)

    return df


def test_capa_por_capa(df):
    resultados = {}
    m0 = LogitEfectosFijos(["densidad_z"], ["country", "product"], C=10).ajustar(df, "E")
    p0 = m0.predecir(df)
    resultados["M0_densidad"] = {
        "p20": precision_at_k(df["E"].values, p0, k=20),
        "auc_pr": auc_pr(df["E"].values, p0),
    }
    for capa in CAPAS:
        col = f"z_{capa}"
        if df[col].isna().all():
            resultados[f"M_{capa}"] = None
            continue
        modelo = LogitEfectosFijos(["densidad_z", col], ["country", "product"], C=10).ajustar(df, "E")
        p = modelo.predecir(df)
        resultados[f"M_{capa}"] = {
            "p20": precision_at_k(df["E"].values, p, k=20),
            "auc_pr": auc_pr(df["E"].values, p),
            "coef": modelo.coeficientes[col],
        }
    cols = [f"z_{c}" for c in CAPAS if not df[f"z_{c}"].isna().all()]
    if cols:
        m_all = LogitEfectosFijos(["densidad_z", *cols], ["country", "product"], C=10).ajustar(df, "E")
        p_all = m_all.predecir(df)
        resultados["M5_todas"] = {
            "p20": precision_at_k(df["E"].values, p_all, k=20),
            "auc_pr": auc_pr(df["E"].values, p_all),
        }
    return resultados


def test_pca(df):
    cols = [f"z_{c}" for c in CAPAS]
    mat = df[cols].fillna(df[cols].mean())
    pca = PCA(n_components=4)
    comps = pca.fit_transform(mat)
    df_pca = df.copy()
    df_pca["pc1"] = comps[:, 0]
    df_pca["pc2"] = comps[:, 1]
    df_pca["pc3"] = comps[:, 2]
    loadings = pd.DataFrame(pca.components_.T, columns=["PC1", "PC2", "PC3", "PC4"], index=cols)
    m_pca2 = LogitEfectosFijos(["densidad_z", "pc1", "pc2"], ["country", "product"], C=10).ajustar(df_pca, "E")
    p_pca2 = m_pca2.predecir(df_pca)
    m_pca3 = LogitEfectosFijos(["densidad_z", "pc1", "pc2", "pc3"], ["country", "product"], C=10).ajustar(df_pca, "E")
    p_pca3 = m_pca3.predecir(df_pca)
    return {
        "loadings": loadings,
        "var_explicada": pca.explained_variance_ratio_,
        "M6_pca2": {"p20": precision_at_k(df_pca["E"].values, p_pca2, k=20), "auc_pr": auc_pr(df_pca["E"].values, p_pca2)},
        "M6_pca3": {"p20": precision_at_k(df_pca["E"].values, p_pca3, k=20), "auc_pr": auc_pr(df_pca["E"].values, p_pca3)},
    }


def test_sin_efectos_fijos(df):
    resultados = {}
    m0 = LogitEfectosFijos(["densidad_z"], ["product"], C=10).ajustar(df, "E")
    p0 = m0.predecir(df)
    resultados["M0_sin_FE"] = {
        "p20": precision_at_k(df["E"].values, p0, k=20),
        "auc_pr": auc_pr(df["E"].values, p0),
    }
    for capa in CAPAS:
        col = f"z_{capa}"
        if df[col].isna().all():
            continue
        modelo = LogitEfectosFijos(["densidad_z", col], ["product"], C=10).ajustar(df, "E")
        p = modelo.predecir(df)
        resultados[f"M_{capa}_sin_FE"] = {
            "p20": precision_at_k(df["E"].values, p, k=20),
            "auc_pr": auc_pr(df["E"].values, p),
            "coef": modelo.coeficientes[col],
        }
    cols = [f"z_{c}" for c in CAPAS if not df[f"z_{c}"].isna().all()]
    if cols:
        m_all = LogitEfectosFijos(["densidad_z", *cols], ["product"], C=10).ajustar(df, "E")
        p_all = m_all.predecir(df)
        resultados["M5_todas_sin_FE"] = {
            "p20": precision_at_k(df["E"].values, p_all, k=20),
            "auc_pr": auc_pr(df["E"].values, p_all),
        }
    return resultados


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--dotaciones", required=True)
    args = ap.parse_args()

    dot_path = Path(args.dotaciones)
    if not dot_path.exists():
        print(f"ERROR: no existe {dot_path}")
        return

    dot = cargar_dotaciones(dot_path)
    print(f"Dotaciones: {dot.iso3.nunique()} paises x {dot.anio.nunique()} anios")
    print(f"Anios disponibles: {sorted(dot.anio.unique())}")

    con = duckdb.connect(args.db, read_only=True)
    puente = con.execute("SELECT * FROM read_csv_auto('data/clean/puente_paises_baci.csv')").fetchdf()
    print(f"Puente BACI-ISO3: {len(puente)} paises")

    for t0, t1, tabla_dens in VENTANAS:
        print(f"\n{'='*70}")
        print(f"VENTANA {t0} -> {t1}")
        print(f"{'='*70}")

        if t0 not in dot.anio.values:
            print(f"  (sin dotaciones para {t0})")
            continue

        df = cargar_panel(con, t0, t1, tabla_dens, dot, puente)
        if df is None or len(df) == 0:
            print("  (sin filas)")
            continue

        print(f"\nn = {len(df):,}, entradas = {int(df['E'].sum()):,} ({100*df['E'].mean():.2f}%)")
        print(f"Paises con dotaciones: {df['iso3'].notna().sum():,} ({100*df['iso3'].notna().mean():.1f}%)")

        print(f"\n--- TEST 1: capa por capa CON efectos fijos ---")
        r1 = test_capa_por_capa(df)
        p20_base = r1["M0_densidad"]["p20"]
        print(f"  M0 densidad sola          p@20 = {p20_base:.4f}  AUC-PR = {r1['M0_densidad']['auc_pr']:.4f}")
        for key, val in r1.items():
            if key == "M0_densidad" or val is None:
                continue
            delta = val["p20"] - p20_base
            coef_str = f"coef = {val['coef']:+.4f}" if "coef" in val else ""
            marca = " <<<" if abs(delta) > 0.005 else ""
            print(f"  {key:26s} p@20 = {val['p20']:.4f}  AUC-PR = {val['auc_pr']:.4f}  {coef_str}{marca}")

        print(f"\n--- TEST 2: PCA CON efectos fijos ---")
        r2 = test_pca(df)
        print("  Loadings:")
        print(r2["loadings"].round(3).to_string().replace("\n", "\n  "))
        print(f"  Varianza: PC1={r2['var_explicada'][0]:.1%}, PC2={r2['var_explicada'][1]:.1%}, PC1+PC2={r2['var_explicada'][:2].sum():.1%}")
        print(f"  densidad + PC1 + PC2       p@20 = {r2['M6_pca2']['p20']:.4f}  AUC-PR = {r2['M6_pca2']['auc_pr']:.4f}")
        print(f"  densidad + PC1 + PC2 + PC3 p@20 = {r2['M6_pca3']['p20']:.4f}  AUC-PR = {r2['M6_pca3']['auc_pr']:.4f}")

        print(f"\n--- TEST 3: capas SIN efectos fijos de pais ---")
        r3 = test_sin_efectos_fijos(df)
        p20_base3 = r3["M0_sin_FE"]["p20"]
        print(f"  M0 densidad sola sin FE    p@20 = {p20_base3:.4f}  AUC-PR = {r3['M0_sin_FE']['auc_pr']:.4f}")
        for key, val in r3.items():
            if key == "M0_sin_FE":
                continue
            delta = val["p20"] - p20_base3
            coef_str = f"coef = {val['coef']:+.4f}" if "coef" in val else ""
            marca = " <<<" if abs(delta) > 0.005 else ""
            print(f"  {key:26s} p@20 = {val['p20']:.4f}  AUC-PR = {val['auc_pr']:.4f}  {coef_str}{marca}")

    con.close()
    print(f"\n{'='*70}")
    print("FIN")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()