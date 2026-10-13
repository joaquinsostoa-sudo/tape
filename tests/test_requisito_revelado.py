import numpy as np
import pandas as pd
import pytest

from src.modelos import requisito_revelado as rr


def _a():
    return pd.DataFrame({"iso3": ["A", "B", "C", "D"], "a_energia": [1.0, 3.0, 0.5, 2.5]})


def _pres():
    return pd.DataFrame({"iso3": ["A", "B", "A"], "hs4": ["x", "x", "y"]})  # x: A y B producen; y: solo A


def _grilla():
    return pd.DataFrame({"iso3": ["A", "C", "D", "C"], "hs4": ["x", "x", "x", "y"]})


def test_faltante_a_mano_con_mediana_de_los_productores():
    f = rr.faltantes(_pres(), _a(), _grilla(), minimo=2).set_index(["iso3", "hs4"])
    assert f.loc[("C", "x"), "f_energia"] == pytest.approx(1.5)  # mediana(1; 3) = 2; el país tiene 0,5
    assert f.loc[("D", "x"), "f_energia"] == 0.0  # por encima de la referencia: no hay faltante
    assert f.loc[("C", "x"), "fmedia_energia"] == pytest.approx(1.5) and f.loc[("C", "x"), "fp25_energia"] == pytest.approx(1.0)
    assert f.loc[("D", "x"), "fdist_energia"] == pytest.approx(0.5)  # la distancia absoluta sí penaliza el exceso


def test_el_propio_pais_sale_de_su_referencia_y_sin_productores_suficientes_queda_vacio():
    f = rr.faltantes(_pres(), _a(), _grilla(), minimo=2).set_index(["iso3", "hs4"])
    assert np.isnan(f.loc[("A", "x"), "f_energia"])  # sin A solo queda un productor: menos del mínimo
    assert np.isnan(f.loc[("C", "y"), "f_energia"])  # "y" tiene un solo productor
    uno = rr.faltantes(_pres(), _a(), _grilla(), minimo=1).set_index(["iso3", "hs4"])
    assert uno.loc[("A", "x"), "f_energia"] == pytest.approx(2.0)  # referencia = B = 3; el país tiene 1


def test_pais_sin_dato_de_la_capa_no_cuenta_y_queda_vacio():
    a = _a().assign(a_energia=[np.nan, 3.0, np.nan, 2.5])
    f = rr.faltantes(_pres(), a, _grilla(), minimo=1).set_index(["iso3", "hs4"])
    assert np.isnan(f.loc[("C", "x"), "f_energia"])  # C sin dato
    assert f.loc[("D", "x"), "f_energia"] == pytest.approx(0.5)  # la referencia usa solo a B (3,0); D tiene 2,5
    assert rr.CAPAS_REVELADAS[-1] == "pib"  # el control de ingreso va al final
