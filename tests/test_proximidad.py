import numpy as np

from src.puentes import proximidad as px


def _distancias():
    # tres distritos en línea: A y B a 10 km, C a 100 km de A; el cuarto no tiene coordenadas
    d = np.array([[0.0, 10.0, 100.0, np.nan],
                  [10.0, 0.0, 90.0, np.nan],
                  [100.0, 90.0, 0.0, np.nan],
                  [np.nan, np.nan, np.nan, np.nan]])
    return d


def test_los_pesos_son_uno_en_el_propio_distrito_y_bajan_con_la_distancia():
    w = px.pesos(_distancias(), 30.0)
    assert w[0, 0] == 1.0 and w[1, 1] == 1.0
    assert abs(w[0, 1] - np.exp(-10 / 30)) < 1e-12
    assert w[0, 1] > w[0, 2] > 0
    assert (w[3] == 0).all() and (w[:, 3] == 0).all()                  # sin coordenadas no pesa


def test_el_pool_con_escala_casi_cero_es_la_oferta_propia():
    v = np.array([5.0, 7.0, 11.0, 3.0])
    p = px.pool(_distancias(), v, 0.01)
    assert np.allclose(p[:3], v[:3])


def test_el_pool_suma_los_vecinos_con_su_peso_y_crece_con_la_escala():
    v = np.array([0.0, 100.0, 0.0, 0.0])
    p15, p60 = px.pool(_distancias(), v, 15.0), px.pool(_distancias(), v, 60.0)
    assert abs(p15[0] - 100 * np.exp(-10 / 15)) < 1e-9                 # A recibe parte de lo de B
    assert p15[1] == 100.0
    assert p60[2] > p15[2] > 0                                          # C, lejos de B, recibe más con una escala mayor
    assert p60[0] > p15[0]


def test_un_distrito_sin_coordenadas_no_recibe_ni_aporta_pool():
    v = np.array([1.0, 2.0, 3.0, 1000.0])
    p = px.pool(_distancias(), v, 30.0)
    assert np.isnan(p[3])                                               # no recibe
    assert abs(p[0] - (1.0 + 2.0 * np.exp(-10 / 30) + 3.0 * np.exp(-100 / 30))) < 1e-9   # y los 1000 del cuarto no aportan a nadie


def test_la_disponibilidad_no_se_suma_entre_distritos():
    v = np.array([10.0, 0.0, 0.0, 0.0])
    p = px.pool(_distancias(), v, 30.0)
    assert p[0] + p[1] + p[2] > v.sum()                                 # las mismas 10 personas cuentan en varios distritos
