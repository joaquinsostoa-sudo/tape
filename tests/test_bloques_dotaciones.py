import pandas as pd
import pytest

from src.modelos import bloques_dotaciones as bd


def test_rca_de_bloques_a_mano_y_sin_energia_binacional():
    expo = pd.DataFrame({"anio": 2015, "iso3": ["A", "A", "B", "B", "A"], "hs4": ["0101", "8517", "0101", "8517", "2716"], "x": [60.0, 40.0, 20.0, 80.0, 999.0]})
    bloques = pd.DataFrame({"hs4": ["0101", "8517"], "bloque": ["primarios_agropecuarios", "manufactura_alta_tec"]})
    r = bd.rca_bloques(expo, bloques, 2015).set_index(["iso3", "bloque"]).rca
    assert r["A", "primarios_agropecuarios"] == pytest.approx((60 / 100) / (80 / 200))  # la energía binacional no cuenta
    assert r["B", "manufactura_alta_tec"] == pytest.approx((80 / 100) / (120 / 200))


def test_terciles_sin_ceros_y_con_ceros():
    s = pd.Series(range(9), index=list("abcdefghi"), dtype=float) + 1
    t = bd.terciles(s)
    assert t[list("abc")].eq("bajo").all() and t[list("def")].eq("medio").all() and t[list("ghi")].eq("alto").all()
    z = pd.Series([0, 0, 0, 0, 1, 2, 3, 4, 5], index=list("abcdefghi"), dtype=float)
    tz = bd.terciles(z)
    assert tz[list("abcd")].eq("bajo").all() and tz["e"] == "medio" and tz["i"] == "alto"  # el cero es el grupo bajo; los positivos se parten por la mediana


def test_cuadro_proporcion_por_tercil_y_diferencia():
    paises = list("abcdefghi")
    dot = pd.DataFrame({"iso3": paises, "x": [1.0, 2, 3, 4, 5, 6, 7, 8, 9]})
    ventaja = pd.DataFrame({"iso3": paises, "bloque": "manufactura_alta_tec", "ventaja": [False, False, False, False, False, True, True, True, True]})
    c = bd.cuadro(ventaja, dot, "x").set_index("bloque").loc["manufactura_alta_tec"]
    assert c.pct_bajo == 0 and c.pct_medio == pytest.approx(100 / 3) and c.pct_alto == 100 and c.dif_alto_bajo == 100


def test_diferencia_dentro_de_ingreso_desaparece_cuando_el_ingreso_lo_explica_todo():
    # 12 países: la ventaja la tiene solo el tercil de ingreso más alto; la dotación crece con el ingreso
    d = pd.DataFrame({"iso3": [f"p{i}" for i in range(12)], "pib_pc_ppa": [float(i + 1) for i in range(12)], "x": [float(i + 1) for i in range(12)]})
    ventaja = pd.DataFrame({"iso3": d.iso3, "bloque": "manufactura_alta_tec", "ventaja": [False] * 8 + [True] * 4})
    r = bd.dif_dentro_de_ingreso(ventaja, d, "x").set_index("bloque").loc["manufactura_alta_tec"]
    assert r.dif_sin_control == pytest.approx(100 * 4 / 6)  # sin control: 4 de 6 países por encima de la mediana frente a 0 de 6 por debajo
    assert abs(r.dif_dentro_de_ingreso) < 1e-9  # dentro de cada tercil de ingreso ya no hay diferencia


def test_pib_de_los_paises_con_ventaja_en_cada_bloque():
    ventaja = pd.DataFrame({"iso3": list("abcd"), "bloque": "manufactura_alta_tec", "ventaja": [True, True, False, False]})
    dot = pd.DataFrame({"iso3": list("abcd"), "pib_pc_ppa": [40.0, 60.0, 10.0, 20.0]})
    r = bd.pib_por_bloque(ventaja, dot).set_index("bloque").loc["manufactura_alta_tec"]
    assert r.paises_con_ventaja == 2 and r.pib_mediano_con == 50 and r.pib_medio_con == 50 and r.pib_mediano_sin == 15
