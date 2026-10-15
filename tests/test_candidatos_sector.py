import numpy as np
import pandas as pd
import pytest

from src.modelos import candidatos_sector as cs


def _puente():
    return pd.DataFrame({"hs92": ["010110", "010120", "020110", "020120", "020130"], "peso": ["1", "1", "0.5", "1", "1"], "valor_mundial": ["60", "40", "100", "100", "100"],
                         "sector_id": ["S03", "S03", "S09", "S09", "S10"]})


def test_pesos_producto_sector_son_fracciones_del_valor_mundial():
    p = _puente()
    p = pd.concat([p, pd.DataFrame({"hs92": ["020110"], "peso": ["0.5"], "valor_mundial": ["100"], "sector_id": ["S10"]})], ignore_index=True)  # 020110 se reparte 50/50
    w = cs.pesos_producto_sector(p).set_index(["hs4", "sector_id"]).w
    assert w[("0101", "S03")] == pytest.approx(1.0)
    assert w[("0201", "S09")] == pytest.approx((0.5 * 100 + 100) / 300)  # 0201 tiene 3 HS6 de valor 100: 050110(0,5) + 020120(1) en S09
    assert w[("0201", "S10")] == pytest.approx((0.5 * 100 + 100) / 300)


def test_agregar_sector_media_ponderada_maximo_conteo_y_excluye_los_presentes():
    pesos = pd.DataFrame({"hs4": ["0101", "0102", "0103", "0104"], "sector_id": ["A"] * 4, "w": [1.0, 1.0, 1.0, 1.0]})
    cand = pd.DataFrame({"hs4": ["0101", "0102", "0103", "0104"], "puntaje": [0.10, 0.30, 0.90, 0.05], "presente": [False, False, True, False]})
    valor = pd.Series({"0101": 100.0, "0102": 300.0, "0103": 1e6, "0104": 100.0})
    s = cs.agregar_sector(cand, pesos, valor, top=2).iloc[0]
    assert s.puntaje_medio == pytest.approx((0.10 * 100 + 0.30 * 300 + 0.05 * 100) / 500)  # el presente (0,90) no entra
    assert s.puntaje_max == 0.30 and s.producto_lider == "0102"
    assert s.productos_en_el_sector == 4 and s.productos_presentes == 1 and s.productos_candidatos == 3
    assert s.n_en_top == 2  # top = 2 entre los candidatos (0,30 y 0,10); el presente no ocupa lugar


def test_sector_sin_candidatos_queda_vacio_y_al_final():
    pesos = pd.DataFrame({"hs4": ["0101", "0201"], "sector_id": ["A", "B"], "w": [1.0, 1.0]})
    cand = pd.DataFrame({"hs4": ["0101", "0201"], "puntaje": [0.0, 0.2], "presente": [True, False]})
    s = cs.agregar_sector(cand, pesos, pd.Series({"0101": 10.0, "0201": 10.0}))
    assert s.sector_id.tolist() == ["B", "A"] and np.isnan(s.iloc[1].puntaje_medio) and s.iloc[1].n_en_top == 0


def test_ventanas_conocidas_no_ve_el_futuro():
    assert cs.ventanas_conocidas(2024) == (2000, 2005, 2010, 2015)
    assert cs.ventanas_conocidas(2019) == (2000, 2005, 2010)  # la ventana 2015 termina en 2020: todavía no se conoce
    assert cs.ventanas_conocidas(2004) == ()
