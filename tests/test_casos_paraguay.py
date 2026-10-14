import numpy as np
import pandas as pd
import pytest

from src.modelos import casos_paraguay as cp


def test_percentil_de_rango_a_mano():
    s = pd.Series([0.9, 0.5, 0.5, 0.1], index=["a", "b", "c", "d"])
    assert cp.percentil_de_rango(s, "a") == 0.0  # primero
    assert cp.percentil_de_rango(s, "b") == pytest.approx(2 / 3)  # empate con c: el peor puesto del empate
    assert cp.percentil_de_rango(s, "d") == 1.0


def test_conjuntos_de_casos_desde_el_puente():
    p = pd.DataFrame({"hs92": ["020110", "020120", "210690", "854430", "220710", "151800"], "peso": ["1", "1", "1", "1", "1", "1"],
                      "valor_mundial": ["90", "10", "100", "5", "7", "3"], "sector_id": ["S09", "S09", "S17", "S40", "S19", "S11"],
                      "marca": [None, None, None, "arnes", "biocombustible_posible", "biocombustible_posible"]})
    c = cp.conjuntos_de_casos(p)
    assert c == {"arneses": ["8544"], "frigorificos": ["0201"], "biocombustibles": ["1518", "2207"]}


def test_eventos_solo_cuentan_entradas_de_paraguay_en_los_productos_del_caso():
    pru = pd.DataFrame({"iso3": ["PRY"] * 4 + ["ARG"] * 4, "hs4": ["8544", "0201", "2207", "0101"] * 2, "E": [1, 0, 1, 0, 1, 1, 1, 1]})
    res = {"prueba": pru, "puntajes": {"densidad_sola": np.array([0.1, 0.9, 0.5, 0.2, 0, 0, 0, 0]), "capas": np.array([0.9, 0.1, 0.5, 0.2, 0, 0, 0, 0])}}
    ev = cp.eventos_ventana(res, {"arneses": ["8544"], "frigorificos": ["0201"], "biocombustibles": ["2207"]}, 2010)
    assert sorted(ev.hs4) == ["2207", "8544"]  # 0201 no es entrada; Argentina no cuenta
    a = ev.set_index("hs4")
    assert a.loc["8544", "puesto_densidad_sola"] == 4 and a.loc["8544", "puesto_capas"] == 1
    assert a.loc["2207", "percentil_densidad_sola"] == pytest.approx(1 / 3)  # solo 0201 tiene mayor puntaje: 1 de 3 pasos


def test_veredicto_marca_el_diez_por_ciento_y_pide_la_mitad():
    ev = pd.DataFrame({"percentil_densidad_sola": [0.05, 0.5, 0.9], "percentil_capas": [0.5, 0.05, 0.02]})
    v = cp.veredicto(ev)
    assert v == {"eventos": 3, "marcados_densidad": 1, "marcados_capas": 2, "anticipaba": 0.0}
    assert cp.veredicto(pd.DataFrame({"percentil_densidad_sola": [0.05, 0.9], "percentil_capas": [0.5, 0.5]}))["anticipaba"] == 1.0
    assert cp.veredicto(pd.DataFrame())["eventos"] == 0
