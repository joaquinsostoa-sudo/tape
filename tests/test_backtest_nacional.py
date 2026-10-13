import numpy as np
import pandas as pd
import pytest

from src.modelos import backtest_nacional as bt

CAPAS = ["energia", "capital_humano", "capital_fisico", "logistica"]


def test_las_ventanas_de_entrenamiento_solo_incluyen_resultados_ya_conocidos():
    assert bt.ventanas_previas(2000) == []
    assert bt.ventanas_previas(2005) == [2000]  # el resultado de 2000 (RCA de 2005) se conoce justo en 2005
    assert bt.ventanas_previas(2010) == [2000, 2005]
    assert bt.ventanas_previas(2015) == [2000, 2005, 2010]


def test_la_densidad_se_estandariza_con_el_entrenamiento():
    ent = pd.DataFrame({"densidad": [0.0, 1.0, 2.0]})
    pru = pd.DataFrame({"densidad": [10.0]})
    e, p = bt.estandarizar_densidad(ent, pru)
    assert e.d_z.mean() == pytest.approx(0.0) and e.d_z.std() == pytest.approx(1.0)
    assert p.d_z.iloc[0] == pytest.approx((10.0 - 1.0) / 1.0)  # la escala no incluye la ventana de prueba


def test_prior_de_producto_y_productos_nunca_vistos():
    ent = pd.DataFrame({"hs4": ["a", "a", "b", "b"], "E": [1, 0, 0, 0]})
    pru = pd.DataFrame({"hs4": ["a", "b", "c"]})
    assert bt.prior_producto(ent, pru) == pytest.approx([0.5, 0.0, 0.25])  # "c" no se vio: tasa general


def test_precision_por_pais_a_mano_y_sin_paises_sin_entradas():
    pru = pd.DataFrame({"iso3": ["A"] * 4 + ["B"] * 3, "hs4": list("wxyz") + list("wxy"),
                        "E": [1, 0, 0, 1, 0, 0, 0]})
    s = np.array([0.9, 0.8, 0.1, 0.2, 0.5, 0.4, 0.3])
    p = bt.precision_por_pais(pru, s, 2)
    assert list(p.index) == ["A"] and p["A"] == pytest.approx(0.5)  # B no tiene entradas: no cuenta


def _panel(ra_importa: bool, semilla: int = 0, n_c: int = 40, n_p: int = 60):
    rng = np.random.default_rng(semilla)
    filas = []
    for anio in (2000, 2005, 2010):
        cef, pef = rng.normal(0, .5, n_c), rng.normal(-2.0, .6, n_p)
        for c in range(n_c):
            for p in range(n_p):
                d = rng.normal()
                ra = rng.normal(size=4)
                eta = cef[c] + pef[p] + 0.8 * d + (1.5 * ra[0] if ra_importa else 0.0)
                filas.append((f"c{c}", f"p{p}", anio, d, *ra, int(rng.random() < 1 / (1 + np.exp(-eta)))))
    return pd.DataFrame(filas, columns=["iso3", "hs4", "anio", "densidad", *(f"ra_{c}" for c in CAPAS), "E"])


def test_el_backtest_detecta_que_las_capas_ayudan_cuando_de_verdad_ayudan():
    res = bt.evaluar_ventana(_panel(ra_importa=True), 2010)
    dif, lo, _ = bt.auc_pr_bootstrap(res["prueba"], res["puntajes"]["capas"], res["puntajes"]["densidad_sola"], reps=30)
    assert dif > 0.02 and lo > 0


def test_el_backtest_no_inventa_mejoras_cuando_las_capas_no_importan():
    res = bt.evaluar_ventana(_panel(ra_importa=False, semilla=1), 2010)
    dif, lo, hi = bt.auc_pr_bootstrap(res["prueba"], res["puntajes"]["capas"], res["puntajes"]["densidad_sola"], reps=30)
    assert lo < 0.0 < hi or abs(dif) < 0.01


def test_sin_fuga_las_etiquetas_de_la_ventana_de_prueba_no_cambian_las_predicciones():
    df = _panel(ra_importa=True, semilla=2)
    base = bt.evaluar_ventana(df, 2010)["puntajes"]
    otro = df.copy()
    prueba = otro.anio == 2010
    otro.loc[prueba, "E"] = np.random.default_rng(9).permutation(otro.loc[prueba, "E"].to_numpy())
    cambiado = bt.evaluar_ventana(otro, 2010)["puntajes"]
    for modelo in ("densidad_sola", "capas", "prior_producto"):
        assert cambiado[modelo] == pytest.approx(base[modelo])
