import numpy as np
import pandas as pd
import pytest

from src.modelos import mundlak as mk
from src.modelos import paises_excluidos as pe


def _prueba():
    paises = ["PRY", "AAA", "BBB", "CCC", "DDD"]
    pib = [0.0, 0.1, -0.2, 1.5, -0.1]  # distancias a PRY: 0,1 / 0,2 / 1,5 / 0,1 (empate con AAA)
    return pd.DataFrame({"iso3": np.repeat(paises, 2), "a_pib": np.repeat(pib, 2), "hs4": ["0101", "0102"] * 5})


def test_comparables_son_los_mas_cercanos_sin_paraguay_y_con_desempate_estable():
    assert pe.comparables(_prueba(), n=3) == ["AAA", "DDD", "BBB"]  # empate 0,1: AAA antes que DDD por código
    with pytest.raises(KeyError):
        pe.comparables(_prueba().query("iso3 != 'PRY'"))


def test_sorteo_es_reproducible_y_nunca_incluye_a_paraguay():
    a, b = pe.sorteo(_prueba(), np.random.default_rng(1), n=3), pe.sorteo(_prueba(), np.random.default_rng(1), n=3)
    assert a == b and "PRY" not in a and len(set(a)) == 3


def test_metricas_y_resumen_a_mano():
    filas = pd.DataFrame({"iso3": ["A"] * 4 + ["B"] * 4, "hs4": list("abcd") * 2, "E": [1, 0, 0, 0, 0, 1, 0, 0]})
    s = {"mundlak_densidad": np.array([0.9, 0.1, 0.1, 0.1, 0.1, 0.2, 0.1, 0.1]), "mundlak_capas": np.array([0.1, 0.9, 0.1, 0.1, 0.1, 0.2, 0.1, 0.1])}
    m = pe.metricas_por_pais(filas, s, k=1)
    assert m.loc["A", "mundlak_densidad"] == 1.0 and m.loc["A", "mundlak_capas"] == 0.0 and m.loc["B", "base"] == 0.25
    r = pe.resumen(m)
    assert r["tasa_base"] == pytest.approx(0.25) and r["lift_mundlak_densidad"] == pytest.approx(1.0 / 0.25)  # densidad: 1,0 en ambos países
    assert r["p20_mundlak_capas"] == pytest.approx(0.5)


def test_predecir_retenidos_devuelve_solo_los_retenidos_y_no_los_usa_para_entrenar():
    rng = np.random.default_rng(0)
    paises = [f"P{i}" for i in range(8)]
    filas = []
    for anio in (2000, 2005):
        for p in paises:
            for h in range(30):
                filas.append({"anio": anio, "iso3": p, "hs4": f"{h:04d}", "E": int(rng.random() < 0.1), "d_z": rng.normal()})
    d = pd.DataFrame(filas)
    for c in mk.COLS_A + mk.COLS_R + mk.COLS_RA:
        d[c] = rng.normal(size=len(d))
    ent, pru = d[d.anio == 2000].copy(), d[d.anio == 2005].copy()
    f, s = pe.predecir_retenidos({"entrenamiento": ent, "prueba": pru}, ["P0", "P1"])
    assert set(f.iso3) == {"P0", "P1"} and len(f) == 60 and all(len(v) == 60 for v in s.values()) and set(s) == set(pe.MODELOS)
