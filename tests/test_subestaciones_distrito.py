import pandas as pd
import pytest

from src.puentes import subestaciones_distrito as m


@pytest.fixture(scope="module")
def df():
    if not m.ENTRADA.exists() or not m.ADM2.exists():
        pytest.skip("faltan la tabla de subestaciones o los límites administrativos")
    return m.localizar(pd.read_csv(m.ENTRADA))


def test_todas_las_subestaciones_tienen_departamento_y_distrito(df):
    assert len(df) == 104
    assert df.departamento.notna().all() and df.distrito.notna().all()


def test_casos_conocidos(df):
    por = df.set_index("nombre")
    # los límites escriben los nombres en mayúsculas y sin tilde
    assert por.loc["SE220kV_VALLEMI-1", "departamento"] == "CONCEPCION"
    assert por.loc["GEN-ITAIPU", "departamento"] == "ALTO PARANA"
    # la represa está sobre el río, en el límite entre Misiones e Itapúa: cae en uno u otro según el límite
    assert por.loc["GEN-YACYRETA", "departamento"] in {"MISIONES", "ITAPUA"}
