import pandas as pd
import pytest

from src.puentes import aduanas_distrito as m


@pytest.fixture(scope="module")
def df():
    if not m.ENTRADA.exists() or not m.ADM2.exists():
        pytest.skip("faltan los puntos de aduanas o los límites administrativos")
    return m.localizar(pd.read_csv(m.ENTRADA))


def test_casi_todos_los_puntos_tienen_distrito(df):
    assert len(df) == 35
    sin = df[df.distrito.isna()]
    # único punto fuera de los límites: un paso fronterizo sin operaciones, al otro lado del río (Nanawa)
    assert len(sin) == 1 and sin.imp_usd_cif.item() == 0


def test_el_puente_de_la_amistad_esta_en_ciudad_del_este(df):
    fila = df[df.imp_usd_cif == 2_200_968_724].iloc[0]
    assert fila.departamento == "ALTO PARANA"
