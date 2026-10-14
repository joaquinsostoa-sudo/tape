import pandas as pd
import pytest

from src.puentes import clasificacion_lall as cl


def test_clase_divide_primarios_y_basadas_en_recursos_entre_agro_y_minerales():
    assert cl.clase("011", "PP") == "PP_agro" and cl.clase("333", "PP") == "PP_mineral" and cl.clase("681", "PP") == "PP_mineral"
    assert cl.clase("273", "PP") == "PP_mineral" and cl.clase("281", "RB2") == "RB2_mineral" and cl.clase("661", "RB2") == "RB2_otras"
    assert cl.clase("012", "RB1") == "RB1" and cl.clase("781", "MT1") == "MT1"


def _lall():
    return pd.DataFrame({"sitc2": ["011", "781", "764"], "clase": ["PP_agro", "MT1", "HT1"]})


def test_votos_a_mano_con_dos_pasos_de_conversion_y_masa_sin_clasificar():
    s23 = pd.DataFrame({"source_sitc2": ["0111", "7811", "9999"], "target_sitc3": ["0111", "7811", "9999"], "weight": [1.0, 1.0, 1.0]})
    s3h = pd.DataFrame({"source_sitc3": ["0111", "7811", "9999", "7811"], "target_hs92": ["020110", "870321", "999999", "999999"],
                        "weight": [1.0, 0.8, 1.0, 0.2]})
    v = cl.votos_hs6(_lall(), s23, s3h)
    assert v.loc["020110", "PP_agro"] == pytest.approx(1.0) and v.loc["870321", "MT1"] == pytest.approx(1.0)
    assert v.loc["999999", "MT1"] == pytest.approx(0.2 / 1.2) and v.loc["999999", "sin_clasificar"] == pytest.approx(1.0 / 1.2)  # mezcla
    assert v.sum(axis=1).tolist() == pytest.approx([1.0, 1.0, 1.0])


def test_agregacion_a_hs4_pondera_por_valor_y_marca_la_confianza_y_el_sin_clasificar():
    votos = pd.DataFrame({"PP_agro": [1.0, 0.0, 0.0, 0.0], "MT1": [0.0, 1.0, 0.6, 0.0], "HT1": [0.0, 0.0, 0.4, 0.0], "sin_clasificar": [0, 0, 0, 1.0]},
                         index=["010111", "870321", "870322", "710813"], dtype=float)
    out = cl.a_hs4(votos, pd.Series({"010111": 5.0, "870321": 3.0, "870322": 1.0, "710813": 2.0})).set_index("hs4")
    assert out.loc["0101", "clase"] == "PP_agro" and out.loc["0101", "bloque"] == "primarios_agropecuarios" and out.loc["0101", "confianza_clase"] == "alta"
    # HS4 8703: MT1 pesa 3 + 0,6 y HT1 0,4 → MT1 = 3,6 / 4,0 = 0,9 del valor clasificado
    assert out.loc["8703", "clase"] == "MT1" and out.loc["8703", "participacion_clase"] == pytest.approx(0.9)
    assert out.loc["7108", "clase"] == "sin_clasificar" and out.loc["7108", "confianza_bloque"] == "baja"


def test_lectura_del_pdf_de_lall_si_esta():
    if not cl.PDF.exists():
        pytest.skip("falta data/raw/clasificaciones_producto/lall/qehwps44.pdf")
    d = cl.leer_lall().set_index("sitc2")
    assert len(d) == 230 and d.index.is_unique
    assert d.loc["011", "subgrupo"] == "PP" and d.loc["333", "clase"] == "PP_mineral" and d.loc["012", "subgrupo"] == "RB1"
    assert d.loc["611", "subgrupo"] == "LT1" and d.loc["781", "subgrupo"] == "MT1" and d.loc["764", "subgrupo"] == "HT1"
    assert d.loc["541", "subgrupo"] == "HT2" and d.loc["711", "subgrupo"] == "MT3" and d.loc["281", "clase"] == "RB2_mineral"
