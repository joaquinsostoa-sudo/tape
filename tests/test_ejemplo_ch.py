import numpy as np
import pandas as pd

from src.puentes import ejemplo_ch as ej


def test_si_la_industria_exige_formacion_el_puntaje_promedia_las_dos_partes():
    base = pd.Series([80.0, 40.0, 60.0])
    espec = pd.Series([60.0, 20.0, 100.0])
    assert list(ej.puntaje(base, espec, exige=True)) == [70.0, 30.0, 80.0]


def test_si_no_exige_solo_cuenta_la_base_y_la_formacion_no_resta():
    base = pd.Series([80.0, 40.0])
    espec = pd.Series([0.0, 100.0])
    assert list(ej.puntaje(base, espec, exige=False)) == [80.0, 40.0]


def test_si_falta_una_parte_y_la_industria_exige_el_puntaje_no_se_inventa():
    p = ej.puntaje(pd.Series([50.0, np.nan]), pd.Series([np.nan, 50.0]), exige=True)
    assert p.isna().all()


def test_el_limitante_es_la_parte_con_menor_percentil():
    assert list(ej.limitante(pd.Series([70.0, 30.0]), pd.Series([40.0, 90.0]))) == ["formación específica", "base"]


def test_control_contra_la_poblacion_cuenta_los_distritos_con_industria_en_el_20_por_ciento_superior():
    n = 10
    d = pd.DataFrame({"poblacion": np.arange(1, n + 1) * 100, "p_base": np.arange(n) * 10.0, "p_especifico": np.arange(n) * 10.0,
                      "puntaje": np.arange(n) * 10.0, "industrias_hoy": [0, 0, 0, 0, 0, 0, 0, 0, 1, 2]})
    c = ej.control_vs_poblacion(d)
    assert c["distritos_con_industria"] == 2 and c["en_top20_puntaje"] == 2 and c["en_top20_poblacion"] == 2
