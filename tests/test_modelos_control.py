import numpy as np
import pandas as pd
import pytest

from src.modelos import mundlak as mk
from src.modelos import xgb_control as xc

CAPAS = ["energia", "capital_humano", "capital_fisico", "logistica"]


def _panel(semilla: int = 0, n_c: int = 30, n_p: int = 50) -> pd.DataFrame:
    """Panel sintético de tres ventanas con las columnas que usan los controles (a_, r_, ra_, densidad)."""
    rng = np.random.default_rng(semilla)
    filas = []
    r = rng.normal(size=(n_p, 4))
    for anio in (2000, 2005, 2010):
        a = rng.normal(size=(n_c, 4))
        cef, pef = rng.normal(0, .5, n_c), rng.normal(-2.0, .6, n_p)
        for c in range(n_c):
            for p in range(n_p):
                d = rng.normal()
                ra = a[c] * r[p]
                eta = cef[c] + pef[p] + 0.8 * d + 0.7 * ra[0]
                filas.append((f"c{c}", f"p{p:02d}", anio, d, *a[c], *r[p], *ra, int(rng.random() < 1 / (1 + np.exp(-eta)))))
    cols = ["iso3", "hs4", "anio", "densidad", *(f"a_{c}" for c in CAPAS), *(f"r_{c}" for c in CAPAS),
            *(f"ra_{c}" for c in CAPAS), "E"]
    return pd.DataFrame(filas, columns=cols)


def test_las_medias_de_mundlak_se_calculan_dentro_de_cada_ventana():
    d = pd.DataFrame({"anio": [2000, 2000, 2005, 2005], "iso3": ["A", "A", "A", "A"], "hs4": ["x", "y", "x", "y"],
                      "d_z": [1.0, 3.0, 10.0, 20.0]})
    m = mk.agregar_medias(d)
    assert m.dbar_pais.tolist() == [2.0, 2.0, 15.0, 15.0] and m.dbar_prod.tolist() == [1.0, 3.0, 10.0, 20.0]


def test_mundlak_estandariza_con_el_entrenamiento():
    ent = pd.DataFrame({"x": [0.0, 2.0, 4.0]})
    pru = pd.DataFrame({"x": [100.0]})
    e, p = mk.estandarizar(ent, pru, ["x"])
    assert e.x.mean() == pytest.approx(0.0) and p.x.iloc[0] == pytest.approx((100.0 - 2.0) / 2.0)


def test_mundlak_corre_y_no_usa_las_etiquetas_de_la_prueba():
    df = _panel()
    base = mk.evaluar_ventana_mundlak(df, 2010)["puntajes"]
    otro = df.copy()
    prueba = otro.anio == 2010
    otro.loc[prueba, "E"] = np.random.default_rng(5).permutation(otro.loc[prueba, "E"].to_numpy())
    cambiado = mk.evaluar_ventana_mundlak(otro, 2010)["puntajes"]
    for nombre in mk.ESPECIFICACIONES:
        assert base[nombre].shape == (30 * 50,) and cambiado[nombre] == pytest.approx(base[nombre])


def test_xgboost_usa_pais_y_producto_como_categorias_y_no_usa_las_etiquetas_de_la_prueba():
    df = _panel(semilla=3)
    res = xc.evaluar_ventana_xgb(df, 2010)
    assert str(res["x_capas"].iso3.dtype) == "category" and str(res["x_capas"].hs4.dtype) == "category"
    assert set(res["puntajes"]) >= {"xgb_densidad", "xgb_capas"}
    otro = df.copy()
    prueba = otro.anio == 2010
    otro.loc[prueba, "E"] = np.random.default_rng(8).permutation(otro.loc[prueba, "E"].to_numpy())
    cambiado = xc.evaluar_ventana_xgb(otro, 2010)["puntajes"]
    assert cambiado["xgb_capas"] == pytest.approx(res["puntajes"]["xgb_capas"])


def test_shap_asigna_importancia_a_la_variable_que_importa():
    df = _panel(semilla=4, n_c=60, n_p=80)
    res = xc.evaluar_ventana_xgb(df, 2010)
    shap = xc.shap_por_grupo(res["modelo_capas"], res["x_capas"], n=2000)
    assert set(shap.index) == set(res["x_capas"].columns) and (shap >= 0).all()
    assert shap["densidad"] > shap["a_logistica"]  # la densidad pesa 0,8 en la simulación y la logística no entra
