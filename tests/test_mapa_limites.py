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
