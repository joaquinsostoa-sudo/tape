import pandas as pd
import pytest

from src.modelos import backtest_sector as bs


def _puente():
    return pd.DataFrame({
        "hs92": ["010111", "010119", "010119", "271600", "999999"],
        "sector_id": ["S03", "S03", "S04", "S99", None],
        "peso": ["1.0", "0.25", "0.75", "1.0", None],
        "marca": [None, None, None, "excluir_energia_binacional", None],
        "valor_mundial": ["100", "300", "300", "500", "100"]})


def test_pesos_hs4_a_mano_con_varios_sectores_y_masa_sin_mapear():
    w = bs.pesos_hs4_sector(_puente()).set_index(["hs4", "sector_id"]).w
    # HS4 0101: HS6 por 100 y 300 (total 400). S03 recibe 100·1 + 300·0,25 = 175; S04 recibe 300·0,75 = 225
    assert w["0101", "S03"] == pytest.approx(175 / 400) and w["0101", "S04"] == pytest.approx(225 / 400)
    assert w.loc["0101"].sum() == pytest.approx(1.0)
    assert "2716" not in set(w.index.get_level_values(0))  # la energía binacional no reparte nada
    assert "9999" not in set(w.index.get_level_values(0))  # un HS6 sin sector no genera peso


def test_exportaciones_del_sector_suman_las_hs4_ponderadas_y_excluyen_la_energia():
    w = bs.pesos_hs4_sector(_puente())
    expo = pd.DataFrame({"anio": 2000, "iso3": ["A", "A", "A"], "hs4": ["0101", "2716", "9999"], "x": [400.0, 1000.0, 50.0]})
    s = bs.exportaciones_sector(expo, w).set_index("sector_id").x
    assert s["S03"] == pytest.approx(175.0) and s["S04"] == pytest.approx(225.0)
    assert s.sum() == pytest.approx(400.0)  # solo el HS4 0101 tiene sector; 2716 y 9999 no aportan
