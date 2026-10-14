import numpy as np
import pytest

from src.modelos import mapa_limites as ml


def _datos():
    """8 países, 2 dotaciones; el producto 0 lo hacen los 4 más dotados en la dotación 0 (relevancia total); la dotación 1 no importa."""
    pct = np.array([[10.0, 50], [20, 90], [30, 10], [40, 60], [60, 20], [70, 80], [80, 40], [90, 70]])
    m = np.zeros((8, 1), dtype=int)
    m[[4, 5, 6, 7], 0] = 1
    return pct, m


def test_relevancia_es_uno_cuando_separa_perfecto_y_cero_cuando_no():
    pct, m = _datos()
    rel, signo = ml.relevancia(pct, m, minimo=3)
    assert rel[0, 0] == pytest.approx(1.0) and signo[0, 0] == 1.0
    assert rel[0, 1] < 0.5  # la dotación 1 no separa
    sin = ml.relevancia(pct, m, minimo=5)[0]
    assert np.isnan(sin[0, 0])  # con 4 productores y mínimo 5 no hay relevancia


def test_relevancia_signo_negativo_si_los_productores_tienen_menos():
    pct, m = _datos()
    rel, signo = ml.relevancia(100 - pct, m, minimo=3)
    assert signo[0, 0] == -1.0 and rel[0, 0] == pytest.approx(1.0)


def test_limite_duro_solo_en_dotacion_relevante_y_bajo_el_percentil_10():
    pct, m = _datos()
    rel, signo = ml.relevancia(pct, m, minimo=3)
    duro = ml.limites_duros(pct[0], pct, m, 0, rel, signo, minimo=3)
    assert duro[0, 0] and not duro[0, 1]  # país 0 (10) está bajo el p10 de 60-90; la dotación 1 es irrelevante
    alto = ml.limites_duros(pct[6], pct, m, 6, rel, signo, minimo=3)
    assert not alto[0, 0]  # un productor bien dotado no tiene límite


def test_exceso_solo_en_dotaciones_irrelevantes():
    pct, m = _datos()
    rel, _ = ml.relevancia(pct, m, minimo=3)
    ref = np.full((8, 1, 2), 50.0)
    exc = ml.exceso_indice(pct, ref, rel)
    assert exc[1, 0] == pytest.approx(40.0)  # país 1: dotación 1 en 90 contra 50, la 0 es relevante y no cuenta
    assert exc[2, 0] == 0.0  # país 2 está por debajo en la dotación irrelevante


def test_deficit_ponderado_a_mano():
    gap = np.array([[[40.0, 10.0]]])
    rel = np.array([[1.0, 0.25]])
    signo = np.array([[1.0, 1.0]])
    assert ml.deficit_ponderado(gap, rel, signo)[0, 0] == pytest.approx((40 + 2.5) / 1.25)
    assert ml.deficit_ponderado(gap, rel, -signo)[0, 0] == 0.0  # sin dotaciones con signo +, nada pesa


def test_ausencia_de_reservas_marca_limite_solo_si_casi_todos_los_productores_las_tienen():
    share = np.array([[0.0], [0.0], [0.3], [0.2], [0.1], [0.4], [0.0]])
    m = np.zeros((7, 1), dtype=int)
    m[[2, 3, 4, 5], 0] = 1
    assert ml.limite_ausencia(share, m, 0, minimo=3)[0]  # los 4 productores tienen reservas
    m[6, 0] = 1
    assert ml.limite_ausencia(share, m, 0, minimo=3)[0]  # 4 de 5 = 80 % sigue marcando
    m[1, 0] = 1
    assert not ml.limite_ausencia(share, m, 0, minimo=3)[0]  # 4 de 6 = 67 % ya no
    share[0, 0] = 0.1
    assert not ml.limite_ausencia(share, m, 0, minimo=3)[0]  # con reservas no hay límite por ausencia


def test_posicion_especifica_usa_el_mineral_del_producto_y_deja_vacio_el_resto():
    import pandas as pd

    pct = np.array([[10.0, 20.0], [30.0, 40.0], [50.0, 60.0]])
    min_ = pd.DataFrame({"commodity": ["Copper", "Copper"], "iso3": ["b", "c"], "share": [0.1, 0.5]})
    pct3, share = ml.pct_especifico(pct, ["a", "b", "c"], ["2603", "0101"], min_, k=1)
    assert share[:, 0].tolist() == [0.0, 0.1, 0.5] and np.isnan(share[:, 1]).all()
    assert pct3[2, 0, 1] == 100.0 and np.isnan(pct3[:, 1, 1]).all() and pct3[0, 0, 0] == 10.0


def test_estado_marca_sin_dato_de_reservas_solo_si_no_hay_limite_duro():
    import pandas as pd

    tabla = pd.DataFrame({"hs4": ["2602", "2602", "0801", "0801"], "n_limites_duros": [0, 1, 0, 0], "compatible": [True, False, True, False]})
    assert ml.estado(tabla).tolist() == ["sin dato confiable de reservas", "límite duro", "compatible", "déficit alto"]
