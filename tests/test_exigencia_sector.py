import pandas as pd

from src.puentes import exigencia_sector as ex


def _tax():
    return pd.DataFrame({"sector_id": ["S09", "S19", "S40", "S01", "S44"], "nombre": ["Frigoríficos", "Bebidas", "Electrónica", "Cultivos", "Reparación"]})


def test_media_ponderada_por_el_valor_mundial_y_corte_en_028():
    req = pd.DataFrame({"hs4": ["0201", "0202", "8501", "1001"], "habilidades": [0.10, 0.20, 0.40, 0.50]})
    pesos = pd.DataFrame({"hs4": ["0201", "0202", "8501", "1001"], "sector_id": ["S09", "S09", "S40", "S01"], "w": [3.0, 1.0, 1.0, 1.0]})
    o = ex.exigencia_por_sector(req, pesos, _tax()).set_index("sector_id")
    assert round(o.loc["S09", "habilidades"], 3) == 0.125               # (0,10 x 3 + 0,20 x 1) / 4
    assert o.loc["S09", "exige_formacion"] == "no" and o.loc["S40", "exige_formacion"] == "si"
    assert o.loc["S40", "productos_con_dato"] == 1 and o.loc["S40", "confianza"] == "baja"


def test_lo_que_no_es_manufactura_o_no_tiene_dato_queda_sin_clasificar_y_no_se_imputa():
    req = pd.DataFrame({"hs4": ["1001"], "habilidades": [0.50]})
    pesos = pd.DataFrame({"hs4": ["1001"], "sector_id": ["S01"], "w": [1.0]})            # S01 es agro: el NBER no lo cubre
    o = ex.exigencia_por_sector(req, pesos, _tax()).set_index("sector_id")
    for s in ("S01", "S09", "S44"):
        assert o.loc[s, "exige_formacion"] == "" and pd.isna(o.loc[s, "habilidades"]) and not o.loc[s, "cerca_del_corte"]


def test_confianza_por_productos_y_marca_de_cercania_al_corte():
    assert [ex.confianza(n) for n in (1, 2, 3, 9, 10, 100)] == ["baja", "baja", "media", "media", "alta", "alta"]
    req = pd.DataFrame({"hs4": ["a", "b"], "habilidades": [0.30, 0.20]})
    pesos = pd.DataFrame({"hs4": ["a", "b"], "sector_id": ["S19", "S09"], "w": [1.0, 1.0]})
    o = ex.exigencia_por_sector(req, pesos, _tax()).set_index("sector_id")
    assert o.loc["S19", "cerca_del_corte"] and not o.loc["S09", "cerca_del_corte"]      # 0,30 está a 0,02 del corte; 0,20 a 0,08
    assert o.loc["S19", "exige_formacion"] == "si" and o.loc["S09", "exige_formacion"] == "no"
