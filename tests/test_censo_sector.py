import pandas as pd
import pytest

from src.puentes import censo_sector as cs
from src.puentes.taxonomia_tape import ISIC4_CLASES, sectores_de_clase

pytestmark = pytest.mark.skipif(not ISIC4_CLASES.exists(), reason="falta la concordancia CIIU de la ONU en data/raw/concordancias")


@pytest.fixture(scope="module")
def clases():
    return cs.clases_ciiu4()


def _sectores(filas):
    return {f["sector_id"]: f["peso"] for f in filas}


def test_codigo_de_un_solo_sector_es_alta_y_pesa_uno(clases):
    f = cs.mapear("141", clases)
    assert len(f) == 1 and f[0]["confianza"] == "alta" and f[0]["peso"] == 1.0 and f[0]["sector_id"] == sectores_de_clase("1410")[0]


def test_grupo_que_reparte_entre_dos_sectores_es_media_y_los_pesos_suman_uno(clases):
    f = cs.mapear("106", clases)  # molinería (1061) y almidones (1062)
    assert {x["confianza"] for x in f} == {"media"} and len(f) == 2 and sum(x["peso"] for x in f) == pytest.approx(1.0)


def test_residual_de_dos_digitos_con_varios_sectores_es_baja(clases):
    f = cs.mapear("10", clases)
    assert {x["confianza"] for x in f} == {"baja"} and len(f) > 2 and sum(x["peso"] for x in f) == pytest.approx(1.0)


def test_desviaciones_del_censo_usan_el_nombre_de_la_rama(clases):
    assert _sectores(cs.mapear("107", clases)) == {sectores_de_clase("1080")[0]: 1.0}  # alimentos para animales
    assert {x["confianza"] for x in cs.mapear("109", clases)} == {"baja"}
    assert all(x["origen"] == "desviacion" for x in cs.mapear("112", clases))
    assert cs.mapear("202", clases)[0]["sector_id"] == sectores_de_clase("2011")[0]  # biocombustibles como en el puente HS


def test_codigo_nacional_sin_grupo_internacional_baja_a_la_division_y_media(clases):
    f = cs.mapear("610", clases)  # telecomunicaciones: la CIIU internacional tiene 611, 612, 613 y 619
    assert len(f) == 1 and f[0]["confianza"] == "media" and "división" in f[0]["nota"]


def test_comercio_usa_los_prefijos_de_la_taxonomia(clases):
    f = cs.mapear("471", clases)
    assert f[0]["origen"] == "taxonomia" and f[0]["sector_id"] != "" and sum(x["peso"] for x in f) == pytest.approx(1.0)


def test_los_pesos_de_cada_codigo_suman_uno(clases):
    ramas = pd.DataFrame({"ciiu": ["141", "106", "109", "471", "10"], "rama": list("abcde"), "ue": [1.0] * 5})
    p = cs.construir(ramas, clases)
    assert (p.groupby("ciiu_censo").peso.sum().sub(1).abs() < 1e-4).all()


def test_por_distrito_conserva_las_unidades_y_marca_el_residual(clases):
    ramas = pd.DataFrame({"departamento": ["C"] * 3, "distrito": ["D"] * 3, "sector": ["Industria", "Industria", "Comercio"], "ciiu": ["106", "", "471"], "rama": ["m", "otras", "c"],
                          "ue": [10.0, 4.0, 6.0], "po": [20.0, 8.0, 12.0], "po_h": [10.0, 4.0, 6.0], "po_m": [10.0, 4.0, 6.0], "remuneraciones": [1.0, 1.0, 1.0], "gastos": [1.0, 1.0, 1.0], "ingresos": [1.0, 1.0, 1.0]})
    p = cs.construir(ramas, clases)
    d = cs.por_distrito(ramas, p)
    assert d.ue.sum() == pytest.approx(20.0) and d.po.sum() == pytest.approx(40.0)
    assert d[d.sector_id == "RESIDUAL_INDUSTRIA"].ue.iloc[0] == 4.0
