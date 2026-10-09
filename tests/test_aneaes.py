from datetime import date

import pytest

from src.limpieza import aneaes


def test_normalizar_encabezado_quita_br_y_espacios():
    assert aneaes.normalizar_encabezado("Sede/Filial/<br>Campus") == "sede/filial/campus"
    assert aneaes.normalizar_encabezado("Nro.<br>resolución") == "nro.resolución"


def test_todos_los_encabezados_conocidos_tienen_nombre():
    assert aneaes.NOMBRES[aneaes.normalizar_encabezado("Fecha de<br>resolución")] == "fecha_resolucion"


def test_serial_a_fecha():
    assert aneaes.serial_a_fecha(43145.0).date() == date(2018, 2, 14)
    assert aneaes.serial_a_fecha("") is None


@pytest.fixture(scope="module")
def df():
    try:
        return aneaes.cargar()
    except FileNotFoundError:
        pytest.skip("faltan los .xls de data/raw/aneaes")


def test_conteos_por_nivel_y_acreditacion(df):
    c = df.groupby(["nivel", "acreditada"]).size().to_dict()
    assert c == {("grado", True): 567, ("grado", False): 52,
                 ("posgrado", True): 168, ("posgrado", False): 5}


def test_fechas_segun_acreditacion(df):
    acr, no = df[df.acreditada], df[~df.acreditada]
    assert acr.fecha_inicio.notna().all() and acr.fecha_resolucion.isna().all()
    assert no.fecha_resolucion.notna().all() and no.fecha_inicio.isna().all()
    assert (acr.fecha_fin > acr.fecha_inicio).all()
