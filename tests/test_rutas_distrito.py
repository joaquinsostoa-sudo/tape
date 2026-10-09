import pandas as pd
import pytest

from src.puentes import rutas_distrito as m


@pytest.fixture(scope="module")
def tabla():
    if not m.ENTRADA.exists() or not m.ADM2.exists():
        pytest.skip("faltan los hitos de rutas o los límites administrativos")
    return m.km_por_distrito(pd.read_parquet(m.ENTRADA))


def test_todos_los_km_quedan_asignados(tabla):
    assert tabla.km_ruta.sum() == 9107


def test_distritos_con_ruta(tabla):
    por = tabla.groupby("distrito").km_ruta.sum()
    assert por.max() < 400  # ningún distrito concentra más que la ruta más larga
    assert tabla.ruta_codigo.nunique() == 22
