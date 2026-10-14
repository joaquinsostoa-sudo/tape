import numpy as np
import pandas as pd
import pytest

from src.modelos import mapa_brechas as mb


def _mundo():
    """6 países, 1 dotación; el producto 0 lo hacen los países 3, 4 y 5 (los más dotados); el producto 1 lo hacen todos menos el 0."""
    pct = np.array([[10.0], [20.0], [30.0], [60.0], [70.0], [90.0]])
    m = np.zeros((6, 2), dtype=int)
    m[[3, 4, 5], 0] = 1
    m[1:, 1] = 1
    grupo = np.array([0, 0, 1, 1, 2, 2])
    return pct, m, grupo


def test_referencia_contra_todos_sin_el_propio_pais_y_con_minimo_de_productores():
    pct, m, grupo = _mundo()
    r = mb.referencias(pct, m, grupo, minimo=2)
    assert r["todos"][0, 0, 0] == 70.0  # país 0 no produce: mediana de 60, 70 y 90
    assert r["todos"][3, 0, 0] == 80.0 and r["n_todos"][3, 0] == 2  # país 3 produce: sin él, mediana de 70 y 90
    sin = mb.referencias(pct, m, grupo, minimo=4)
    assert np.isnan(sin["todos"][0, 0, 0])  # con 3 productores y mínimo 4 no hay referencia


def test_referencia_de_ingreso_similar_y_respaldo_en_todos_cuando_hay_pocos():
    pct, m, grupo = _mundo()
    r = mb.referencias(pct, m, grupo, minimo=1)
    assert r["ingreso_similar"][5, 0, 0] == 70.0  # país 5 (tercio alto): su par de ingreso, el 4, produce; la mediana excluye al propio país
    assert r["ingreso_similar"][0, 0, 0] == r["todos"][0, 0, 0] and r["similar_con_respaldo"][0, 0]  # nadie de su tercio produce: usa la de todos


def test_brecha_indice_y_tolerancia_a_mano():
    pct, m, grupo = _mundo()
    r = mb.referencias(pct, m, grupo, minimo=2)
    g = mb.brechas(pct, r["todos"])
    assert g[0, 0, 0] == 60.0 and g[5, 0, 0] == 0.0  # el país 0 está 60 puntos por debajo de 70; el 5 está por encima de 70 (excluyéndose)
    idx = mb.indice(g, min_capas=1)
    assert idx[0, 0] == 60.0
    bl = np.array([0, 1])
    tol, tol_idx = mb.tolerancias(g, idx, m == 1, bl, 2, piso=5.0, min_pares=1)
    assert tol[0, 0] >= 5.0 and tol_idx[2] >= 5.0  # el piso evita tolerancias de cero
    chico = mb.tolerancias(g, idx, m == 1, bl, 2, piso=5.0, min_pares=100)
    assert np.allclose(chico[0][0], chico[0][2])  # con pocos pares el bloque usa la tolerancia global
    cl = mb.clasificar(g[0], idx[0], np.array([[20.0], [20.0], [20.0]]), np.array([20.0, 20.0, 20.0]), np.array([0, 0]))
    assert cl.loc[0, "n_fuera_tolerancia"] == 1 and not cl.loc[0, "compatible"] and cl.loc[0, "grado"] == pytest.approx(3.0)


def test_auc_perfecto_cuando_el_puntaje_ordena_bien():
    m = np.array([[1, 1, 0, 0, 0], [1, 1, 1, 0, 0]])
    puntaje = np.array([[0.9, 0.8, 0.2, 0.1, 0.0], [0.9, 0.8, 0.7, 0.2, 0.1]])
    a = mb.auc_por_pais(m, puntaje)
    assert np.isnan(a[0]) and a[1] == 1.0  # con menos de 3 presencias el país queda vacío
    m2 = np.array([[1, 1, 1, 0, 0, 0]])
    assert mb.auc_por_pais(m2, np.array([[0.9, 0.8, 0.7, 0.2, 0.1, 0.0]]))[0] == 1.0
    assert mb.auc_por_pais(m2, -np.array([[0.9, 0.8, 0.7, 0.2, 0.1, 0.0]]))[0] == 0.0


def test_posiciones_son_percentiles_entre_los_paises_de_la_muestra():
    dot = pd.DataFrame({"iso3": list("abcd"), "anio": 2019, **{c: [1.0, 2.0, 3.0, 4.0] for c in mb.CAPAS}})
    p = mb.posiciones(dot, list("abcd"), 2019)
    assert p.loc["a", "hc"] == 25.0 and p.loc["d", "hc"] == 100.0
