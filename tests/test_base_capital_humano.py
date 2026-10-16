import numpy as np
import pandas as pd

from src.puentes import base_capital_humano as bc


def test_escolaridad_del_distrito_pesa_la_tasa_urbana_y_la_rural():
    assert bc.escolaridad_distrito(0.5, 60.0, 30.0) == 45.0
    assert bc.escolaridad_distrito(1.0, 60.0, float("nan")) == 60.0          # todo urbano: no necesita la tasa rural (Asunción)
    assert bc.escolaridad_distrito(0.0, 60.0, 30.0) == 30.0
    assert np.isnan(bc.escolaridad_distrito(0.4, 60.0, float("nan")))        # pesa un área sin tasa: no se inventa
    assert np.isnan(bc.escolaridad_distrito(float("nan"), 60.0, 30.0))


def test_distancia_haversine_a_mano():
    d = bc.distancia_km(np.array([0.0, 0.0]), np.array([0.0, 0.0]), np.array([0.0, 0.0]), np.array([1.0, 2.0]))
    assert d.shape == (2, 2)
    assert abs(d[0, 0] - 111.195) < 0.01                                     # un grado de longitud en el ecuador
    assert abs(d[0, 1] - 2 * 111.195) < 0.02
    assert (d.min(axis=1) >= 0).all()


def test_percentil_los_empates_toman_el_valor_mas_bajo():
    s = pd.Series([0, 0, 0, 0, 5, 10])
    p = bc.percentil(s)
    assert list(p[:4]) == [0.0] * 4                                          # los ceros quedan abajo, no a mitad de tabla
    assert p.iloc[5] == 100.0 and p.iloc[4] == 80.0
    d = bc.percentil(pd.Series([1.0, 5.0, 20.0]), mayor_es_mejor=False)       # la distancia menor es la mejor
    assert list(d) == [100.0, 50.0, 0.0]
    assert bc.percentil(pd.Series([1.0, np.nan, 3.0])).isna().tolist() == [False, True, False]


def test_indice_con_pesos_iguales_y_parcial_si_falta_una_parte():
    partes = pd.DataFrame({"a": [90.0, 60.0], "b": [30.0, 30.0], "c": [60.0, np.nan]})
    idx, n = bc.indice(partes)
    assert list(idx) == [60.0, 45.0]                                         # (90+30+60)/3 y (60+30)/2
    assert list(n) == [3, 2]


def test_palabras_contenidas_empareja_nombres_largos_y_cortos_solo_si_es_unico():
    cand = {"FULGENCIOYEGROS": "Fulgencio Yegros", "MAYORJULIO": "Mayor Julio Dionisio Otaño", "SANPEDRO": "San Pedro"}
    assert bc.palabras_contenidas("YEGROS", cand) == "FULGENCIOYEGROS"
    assert bc.palabras_contenidas("MAYOR OTANO", cand) == "MAYORJULIO"
    assert bc.palabras_contenidas("SAN PEDRO DEL YCUAMANDYJU", cand) == "SANPEDRO"
    assert bc.palabras_contenidas("NOMBRE QUE NO ESTA", cand) is None
    ambiguo = {"A": "San Juan del Norte", "B": "San Juan del Sur"}
    assert bc.palabras_contenidas("SAN JUAN", ambiguo) is None               # dos candidatos: no se adivina
