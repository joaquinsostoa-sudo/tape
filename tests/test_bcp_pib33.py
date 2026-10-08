import pytest

from src.limpieza.bcp_pib33 import EXCEL, cargar

pytestmark = pytest.mark.skipif(not EXCEL.exists(), reason="falta el Excel del BCP en data/raw (no versionado)")


def test_33_actividades_y_rango_de_anios():
    df = cargar()
    act = df[df.tipo_fila == "actividad"]
    assert act.actividad.nunique() == 33
    assert (act.anio.min(), act.anio.max()) == (1991, 2024)
    assert set(act[act.preliminar].anio) == {2023, 2024}


def test_las_33_actividades_suman_el_valor_agregado_bruto():
    df = cargar()
    c = df[(df.precio == "corriente") & (df.anio == 2019)]
    suma = c[c.tipo_fila == "actividad"].valor_mill_gs.sum()
    vab = c[c.tipo_fila == "vab"].valor_mill_gs.iloc[0]
    assert suma == pytest.approx(vab, rel=1e-6)
