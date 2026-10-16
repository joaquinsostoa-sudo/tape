import pandas as pd
import pytest

from src.limpieza import mapbiomas as mb


def _cobertura():
    f = [("ALTO PARANA", "ITAKYRY", "3.2 Agriculture", 100.0, 80.0, 90.0), ("ALTO PARANA", "ITAKYRY", "3.1 Pasture", 50.0, 40.0, 45.0),
         ("ALTO PARANA", "ITAKYRY", "1.1 Closed Natural Woodlands", 30.0, 30.0, 30.0), ("ALTO PARANA", "ITAKYRY", "1.3 Flooded Natural Woodlands", 20.0, 20.0, 20.0),
         ("ALTO PARANA", "ITAKYRY", "5. Water bodies", 0.0, 0.0, 0.0)]
    return pd.DataFrame(f, columns=["territory_level_3", "territory_level_4", "class_level_2", "y2023", "y2021", "y2022"])


def test_agrupar_suma_las_clases_del_mismo_grupo_y_la_superficie_total_es_la_suma_de_todas():
    a = mb.agrupar(_cobertura().assign(y2021=lambda d: d["y2021"])).iloc[0]
    assert a["ha_agricultura_2023"] == 100.0 and a["ha_pastura_2023"] == 50.0
    assert a["ha_bosque_natural_2023"] == 50.0                        # 1.1 más 1.3
    assert a["ha_total"] == 200.0 and a["pct_agricultura"] == 50.0 and a["pct_pastura"] == 25.0


def test_el_promedio_de_la_agricultura_usa_2021_a_2023():
    a = mb.agrupar(_cobertura().assign(y2023=lambda d: d["y2023"])).iloc[0]
    assert abs(a["ha_agricultura_prom_2021_2023"] - (80.0 + 90.0 + 100.0) / 3) < 1e-9


def test_una_clase_desconocida_no_se_ignora_en_silencio():
    d = _cobertura()
    d.loc[0, "class_level_2"] = "9.9 Clase nueva"
    with pytest.raises(ValueError, match="clases sin grupo"):
        mb.agrupar(d)
