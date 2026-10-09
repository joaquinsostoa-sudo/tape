import json

import pandas as pd
import pytest

from src.limpieza import mic_salud as m
from src.puentes import salud_distrito as s


@pytest.fixture(scope="module")
def df():
    if not m.JSON_SALUD.exists():
        pytest.skip("falta el JSON de salud en data/raw/mic_mapa")
    return m.establecimientos(json.loads(m.JSON_SALUD.read_text(encoding="utf-8")))


def test_conteos(df):
    assert len(df) == 212
    assert df.institucion.value_counts().to_dict() == {"IPS": 138, "MSPBS": 74}
    assert df.prestador.value_counts().to_dict() == {"IPS": 82, "MSPBS": 74, "CONVENIO": 43, "TERCERIZADO": 13}


def test_cinco_sin_coordenadas_todos_msp_en_san_pedro(df):
    sin = df[df.lat.isna()]
    assert len(sin) == 5
    assert set(sin.institucion) == {"MSPBS"} and set(sin.dep_codigo) == {2}


def test_coordenadas_dentro_de_paraguay(df):
    c = df.dropna(subset=["lat"])
    assert c.lat.between(-27.7, -19.2).all() and c.lon.between(-62.7, -54.2).all()


def test_ubicacion_por_ciudad_cubre_a_los_cinco(df):
    if not s.CIUDADES.exists() or not s.ADM2.exists():
        pytest.skip("faltan la tabla de ciudades o los límites")
    out = s.localizar(df, pd.read_csv(s.CIUDADES))
    assert out.ubicacion.value_counts().to_dict() == {"propia": 207, "ciudad": 5}
    assert out.distrito.notna().sum() >= 210
