import numpy as np
import pandas as pd

from src.puentes import matcheo_bien_nuevo as mb


def test_percentil_del_requisito_es_el_porcentaje_de_productos_con_requisito_menor():
    s = pd.Series([0.1, 0.2, 0.3, 0.4])
    assert mb.percentil_requisito(0.3, s) == 50.0
    assert mb.percentil_requisito(0.05, s) == 0.0
    assert mb.percentil_requisito(0.5, s) == 100.0


def test_los_vecinos_son_los_presentes_mas_proximos_y_solo_con_phi_positivo():
    productos = ["a", "b", "c", "d", "e"]
    phi = np.array([[0.0, 0.5, 0.2, 0.9, 0.0], [0.5, 0, 0, 0, 0], [0.2, 0, 0, 0, 0], [0.9, 0, 0, 0, 0], [0, 0, 0, 0, 0]])
    v = mb.vecinos(phi, productos, presentes=["b", "c", "d", "e"], bien="a", k=3)
    assert list(v["hs4"]) == ["d", "b", "c"] and list(v["phi"]) == [0.9, 0.5, 0.2]      # "e" tiene φ 0 con el bien y no entra
    assert "a" not in v["hs4"].tolist()


def test_el_peldano_es_la_diferencia_de_percentiles_y_nunca_negativo():
    req = pd.Series({"bien": 0.40, "v1": 0.10, "v2": 0.20, "otro1": 0.30, "otro2": 0.50})
    vec = pd.DataFrame({"hs4": ["v1", "v2"], "phi": [0.5, 0.5]})
    p = mb.peldano(0.40, vec, req)
    assert p["pct_bien"] == 60.0 and p["paso"] > 0 and p["vecinos_con_dato"] == 2
    # si los vecinos exigen más que el bien, el peldaño es 0 y no se baja el umbral
    vec2 = pd.DataFrame({"hs4": ["otro2"], "phi": [1.0]})
    assert mb.peldano(0.40, vec2, req)["paso"] == 0.0
    # sin vecinos con dato
    assert mb.peldano(0.40, pd.DataFrame({"hs4": ["z"], "phi": [1.0]}), req)["paso"] == 0.0


def test_la_referencia_son_los_distritos_con_industria_en_algun_sector_de_los_vecinos():
    claves = [("A", "1"), ("A", "2"), ("B", "3")]
    pres = {"S10": {("A", "1")}, "S11": {("B", "3")}}
    assert list(mb.referencia({"S10", "S11"}, pres, claves)) == [True, False, True]
    assert not mb.referencia({"S99"}, pres, claves).any()


def test_la_densidad_pesa_los_vecinos_por_phi_y_solo_cuenta_manufactura():
    claves = [("A", "1"), ("A", "2")]
    pres = {"S10": {("A", "1")}, "S11": {("A", "1"), ("A", "2")}, "S01": {("A", "2")}}
    d = mb.densidad({"p": 3.0, "q": 1.0, "r": 5.0}, {"p": "S10", "q": "S11", "r": "S01"}, pres, claves)
    assert np.allclose(d, [1.0, 0.25])                                  # S01 es agro: no cuenta; A1 tiene p y q, A2 solo q


def _distritos(n=30):
    return pd.DataFrame({"p_base": np.arange(n, dtype=float), "p_especifico": np.arange(n, dtype=float), "pool": np.arange(n, dtype=float) * 10})


def test_umbrales_c_suman_el_peldano_solo_a_la_formacion_y_con_tope_100():
    d = _distritos()
    mask = np.array([True] * 20 + [False] * 10)
    u = mb.umbrales_c(d, mask, paso=30.0)
    assert u["base"] == np.quantile(np.arange(20.0), 0.10)
    assert u["especifico"] == np.quantile(np.arange(20.0), 0.10) + 30.0
    assert mb.umbrales_c(d, mask, paso=500.0)["especifico"] == 100.0


def test_con_menos_de_10_distritos_de_referencia_se_usa_la_mediana_y_se_avisa():
    d = _distritos()
    mask = np.array([True] * 5 + [False] * 25)
    u = mb.umbrales_c(d, mask, paso=0.0)
    assert u["base"] == d["p_base"].median() and "solo 5" in u["referencia"]


def test_el_cruce_con_la_densidad():
    cat = pd.Series(["lista", "lista", "falta base", "faltan ambas", "sin dato"])
    dens = pd.Series([0.9, 0.0, 0.8, 0.1, 0.9])
    assert list(mb.cruce(cat, dens, 0.5)) == ["candidato", "capacidad sin uso", "qué desarrollar", "no es candidato", "sin dato"]
