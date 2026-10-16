import numpy as np
import pandas as pd

from src.fase2 import densidad_territorial as dt
from src.fase2 import presencia as pr
from src.fase2 import prueba_densidad as pd_


def test_lq_a_mano_dentro_de_la_manufactura():
    e = pd.DataFrame({"A": [8.0, 2.0], "B": [2.0, 8.0]}, index=["d1", "d2"])      # dos distritos, dos sectores
    l = pr.lq(e)
    assert abs(l.loc["d1", "A"] - (8 / 10) / (10 / 20)) < 1e-12 and abs(l.loc["d1", "B"] - (2 / 10) / (10 / 20)) < 1e-12
    assert pr.presencia_lq(e).loc["d1", "A"] and not pr.presencia_lq(e).loc["d1", "B"]      # 1,6 > 1,5 y 0,4 no


def test_un_distrito_sin_establecimientos_no_tiene_presencia_ni_rompe_el_lq():
    e = pd.DataFrame({"A": [0.0, 3.0], "B": [0.0, 1.0]}, index=["vacio", "d2"])
    assert not pr.presencia_lq(e).loc["vacio"].any()


def test_presencia_alterna_es_al_menos_una_unidad():
    e = pd.DataFrame({"A": [0.4, 1.0], "B": [0.5, 3.0]}, index=["d1", "d2"])
    assert pr.presencia_alterna(e, 0.5).loc["d1"].tolist() == [False, True]
    assert pr.presencia_alterna(e, 1.0).loc["d2"].tolist() == [True, True]


def test_la_densidad_pesa_los_otros_sectores_por_phi_y_no_cuenta_al_propio():
    pres = pd.DataFrame({"A": [True, False], "B": [True, True], "C": [False, False]}, index=["d1", "d2"])
    phi = pd.DataFrame([[0.0, 0.8, 0.2], [0.8, 0.0, 0.4], [0.2, 0.4, 0.0]], index=list("ABC"), columns=list("ABC"))
    d = dt.densidad(pres, phi)
    # d1, sector C: (φ_CA·1 + φ_CB·1) / (φ_CA + φ_CB) = 1 ; d2, sector C: (0,2·0 + 0,4·1) / 0,6
    assert abs(d.loc["d1", "C"] - 1.0) < 1e-12 and abs(d.loc["d2", "C"] - 0.4 / 0.6) < 1e-12
    # d1, sector A: no cuenta que A esté presente en d1; solo B (φ 0,8) y C (0,2): (0,8·1 + 0,2·0) / 1,0
    assert abs(d.loc["d1", "A"] - 0.8) < 1e-12
    phi_con_diagonal = phi + np.eye(3)                       # una diagonal distinta de cero no cambia nada
    assert np.allclose(dt.densidad(pres, phi_con_diagonal).values, d.values)


def test_el_auc_tiene_los_valores_conocidos():
    y = np.array([0, 0, 1, 1])
    assert pd_.auc(np.array([0.1, 0.2, 0.8, 0.9]), y) == 1.0
    assert pd_.auc(np.array([0.9, 0.8, 0.2, 0.1]), y) == 0.0
    assert pd_.auc(np.array([0.5, 0.5, 0.5, 0.5]), y) == 0.5
    assert np.isnan(pd_.auc(np.array([1.0, 2.0]), np.array([1, 1])))


def test_las_bases_excluyen_al_propio_distrito_y_al_propio_sector():
    pres = pd.DataFrame({"A": [True, True, False], "B": [False, True, False]}, index=["d1", "d2", "d3"])
    e = pd.DataFrame({"A": [5.0, 2.0, 0.0], "B": [1.0, 3.0, 4.0]}, index=pres.index)
    b = pd_.bases(pres, e)
    assert b["prevalencia"].loc["d1", "A"] == 0.5 and b["prevalencia"].loc["d3", "A"] == 1.0     # los otros 2 distritos: d2 sí, d3 no / d1 y d2 sí
    assert b["tamano"].loc["d1", "A"] == 1.0 and b["tamano"].loc["d1", "B"] == 5.0              # establecimientos del distrito sin contar el sector


def test_el_criterio_exige_mejora_de_003_y_un_intervalo_que_excluya_el_cero():
    ok = pd.DataFrame({"metrica": ["auc_dif_prevalencia", "auc_dif_tamano"], "valor": [0.05, 0.04], "ic_inf": [0.01, 0.002], "ic_sup": [0.09, 0.08]})
    assert pd_.cumple(ok)
    poca = ok.assign(valor=[0.05, 0.02])                                     # una mejora menor a 0,03
    assert not pd_.cumple(poca)
    ancho = ok.assign(ic_inf=[0.01, -0.01])                                  # el intervalo incluye el cero
    assert not pd_.cumple(ancho)


def test_la_comparacion_detecta_que_la_densidad_perfecta_supera_a_una_base_aleatoria():
    rng = np.random.default_rng(0)
    y = pd.DataFrame(rng.random((60, 10)) < 0.3)
    dens = y.astype(float) * 0.9 + rng.random((60, 10)) * 0.05                # densidad casi perfecta
    base = pd.DataFrame(rng.random((60, 10)))
    t = pd_.comparar(y, {"densidad": dens, "azar": base}, n_boot=200).set_index("metrica")
    assert t.loc["auc_densidad", "valor"] > 0.95 and abs(t.loc["auc_azar", "valor"] - 0.5) < 0.1
    assert t.loc["auc_dif_azar", "ic_inf"] > 0.3
