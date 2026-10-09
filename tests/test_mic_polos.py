import json

import pandas as pd
import pytest

from src.limpieza import mic_polos as m


@pytest.fixture(scope="module")
def datos():
    if not m.JSON_POLOS.exists():
        pytest.skip("falta el JSON de polos en data/raw/mic_mapa")
    return json.loads(m.JSON_POLOS.read_text(encoding="utf-8"))


def test_jerarquia_de_afi(datos):
    a = m.afi(datos)
    assert len(a) == 6987
    assert a.capa.nunique() == 1  # el visor no devuelve datos para "Polo industrial"
    assert (a.zona.nunique(), a.subregion.nunique(), a.polo.nunique(), a.nodo.nunique()) == (5, 5, 21, 42)
    assert a.lat.between(-27.7, -19.2).all() and a.lon.between(-62.7, -54.2).all()


def test_cada_nodo_pertenece_a_un_solo_polo(datos):
    j = m.jerarquia(m.afi(datos))
    assert j.nodo.is_unique and j.puntos.sum() == 6987


def test_centros_snpp(datos):
    if not m.CIUDADES.exists():
        pytest.skip("falta ciudades_mic.csv")
    s = m.snpp(datos, pd.read_csv(m.CIUDADES))
    assert len(s) == 53
    assert s.ubicacion.value_counts().to_dict() == {"propia": 30, "ciudad": 22, "sin_ubicacion": 1}
    # El visor ubica el centro de Encarnación en Alto Paraná: queda sin ubicación hasta confirmarlo
    assert s[s.ubicacion == "sin_ubicacion"].ciudad.item() == "ENCARNACION"
    con = s[s.ubicacion != "sin_ubicacion"]
    assert con.lat.between(-27.7, -19.2).all() and con.lon.between(-62.7, -54.2).all()
