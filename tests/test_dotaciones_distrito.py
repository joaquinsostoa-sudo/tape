import numpy as np
import pandas as pd

from src.puentes import dotaciones_distrito as dd
from src.puentes import exigencia_capas as ec


def test_el_pool_de_puntos_pesa_cada_punto_por_su_distancia():
    distritos = np.array([[0.0, 0.0], [0.0, 1.0], [np.nan, np.nan]])
    puntos = np.array([[0.0, 0.0]])                                      # un punto en el primer distrito
    p = dd.pool_puntos(distritos, puntos, np.array([100.0]), 111.195)    # un grado de longitud en el ecuador = 111,195 km
    assert p[0] == 100.0 and abs(p[1] - 100.0 * np.exp(-1.0)) < 1e-3
    assert np.isnan(p[2])                                                # sin coordenadas: no recibe


def test_la_distancia_minima_toma_el_punto_mas_cercano_y_deja_nan_sin_coordenadas():
    distritos = np.array([[0.0, 0.0], [0.0, 2.0], [np.nan, np.nan]])
    puntos = np.array([[0.0, 0.0], [0.0, 3.0]])
    d = dd.distancia_minima(distritos, puntos)
    assert d[0] == 0.0 and abs(d[1] - 111.195) < 0.05 and np.isnan(d[2])
    assert np.isnan(dd.distancia_minima(distritos, np.empty((0, 2)))).all()


def test_potencia_por_subestacion_promedia_los_anios_y_suma_las_dos_redes():
    pot = pd.DataFrame({"subestacion": ["A", "A", "A", "A", "B"], "red": ["23kV", "23kV", "220/66kV", "220/66kV", "23kV"], "anio": [2026, 2028, 2026, 2030, 2027],
                        "potencia_disp_mw": [10.0, 20.0, 100.0, 999.0, 5.0]})          # 2030 queda afuera de 2026-2028
    sub = pd.DataFrame({"nombre": ["A", "B", "C"], "lat": [0, 1, 2], "lon": [0, 1, 2], "nivel_tension": ["220 kV", "23 kV", "23 kV"]})
    r = dd.potencia_por_subestacion(pot, sub).set_index("nombre")
    assert r.loc["A", "mw_23kv"] == 15.0 and r.loc["A", "mw_220_66kv"] == 100.0 and r.loc["A", "mw_total"] == 115.0
    assert r.loc["B", "mw_total"] == 5.0 and r.loc["C", "mw_total"] == 0.0            # sin dato = 0, no se inventa


def _pesos():
    return pd.DataFrame({"hs4": ["a", "b", "c", "d"], "sector_id": ["S09", "S09", "S40", "S01"], "w": [3.0, 1.0, 1.0, 1.0]})


def _req():
    return pd.DataFrame({"hs4": ["a", "b", "c", "d"], "energia": [0.01, 0.03, 0.05, np.nan], "capital": [100.0, 300.0, 500.0, np.nan], "valor_peso_usd_kg": [0.5, 2.0, 100.0, 1.0]})


def test_la_media_ponderada_por_sector_pesa_por_w():
    x = _pesos().merge(_req(), on="hs4")
    m = ec.media_ponderada(x, "energia")
    assert abs(m.loc["S09", "energia"] - (0.01 * 3 + 0.03 * 1) / 4) < 1e-12 and m.loc["S09", "n_energia"] == 2
    assert "S01" not in m.index                                                      # sin dato de energía: no aparece, no se imputa


def test_exigencia_de_energia_y_logistica_contra_la_mediana_de_los_productos():
    tax = pd.DataFrame({"sector_id": ["S01", "S09", "S40"], "nombre": ["x", "y", "z"]})
    o = ec.exigencia_capas(_req(), _pesos(), tax).set_index("sector_id")
    assert o.loc["S09", "exige_energia"] == "no" and o.loc["S40", "exige_energia"] == "si"     # mediana de la energía = 0,03
    assert o.loc["S01", "exige_energia"] == ""                                                  # agro: el NBER no lo cubre
    assert o.loc["S09", "exige_logistica"] == "si" and o.loc["S40", "exige_logistica"] == "no"  # bajo valor por kilo exige logística
    assert o.loc["S01", "exige_logistica"] == "si"                                              # el valor por kilo sí existe para el agro


def test_recursos_exigen_los_sectores_agropecuarios_y_de_primera_transformacion():
    assert {"S01", "S07", "S09", "S21", "S23", "S24"} <= set(ec.RECURSOS)
    assert not ({"S08", "S22", "S25", "S31", "S40", "S64"} & set(ec.RECURSOS))


def test_los_sectores_de_recursos_tienen_clase_de_tierra_o_estan_marcados_sin_medida():
    clases = [s for secs in ec.CLASE_TIERRA.values() for s in secs]
    assert len(clases) == len(set(clases))                                  # un sector no puede tener dos clases
    assert set(clases) | set(ec.SIN_MEDIDA) == set(ec.RECURSOS)             # la lista de D33 queda cubierta, y nada fuera de ella
    assert not (set(clases) & set(ec.SIN_MEDIDA))
    assert set(ec.CLASE_TIERRA) == set(dd.CLASES_TIERRA)                     # las clases de los requisitos son las que se miden por distrito


def test_exigencia_de_recursos_marca_con_medida_y_sin_medida():
    tax = pd.DataFrame({"sector_id": ["S01", "S07", "S09", "S22", "S40"], "nombre": list("abcde")})
    pesos = pd.DataFrame({"hs4": ["a"], "sector_id": ["S40"], "w": [1.0]})
    req = pd.DataFrame({"hs4": ["a"], "energia": [0.01], "capital": [100.0], "valor_peso_usd_kg": [10.0]})
    o = ec.exigencia_capas(req, pesos, tax).set_index("sector_id")
    assert o.loc["S01", "clase_tierra"] == "agricultura" and o.loc["S01", "recursos_con_medida"] == "si"
    assert o.loc["S09", "clase_tierra"] == "pastura"
    assert o.loc["S07", "clase_tierra"] == "" and o.loc["S07", "recursos_con_medida"] == "no" and o.loc["S07", "exige_recursos"] == "si"   # en la lista, sin medida
    assert o.loc["S22", "exige_recursos"] == "no" and o.loc["S22", "recursos_con_medida"] == ""                                                # confecciones no exige recursos
