import json

import pytest

from src.limpieza import mic_rutas as m


@pytest.fixture(scope="module")
def datos():
    if not m.JSON_RUTAS.exists():
        pytest.skip("falta el JSON de rutas en data/raw/mic_mapa")
    return json.loads(m.JSON_RUTAS.read_text(encoding="utf-8"))


def test_un_hito_por_km_de_ruta(datos):
    r, h = m.rutas_km(datos), m.hitos(datos)
    assert len(r) == 22 and r.km.sum() == 9107 == len(h)
    por_ruta = h.groupby("ruta_codigo").size()
    assert (por_ruta == r.set_index("ruta_codigo").km).all()


def test_py01_va_de_asuncion_a_encarnacion(datos):
    h = m.hitos(datos)
    py01 = h[h.ruta_codigo == "PY01"]
    assert py01.km_hito.min() == 0 and py01.km_hito.max() == 413
    assert py01[py01.km_hito == 0].departamento.item() == "100- CAPITAL"


def test_fronteras(datos):
    f = m.fronteras(datos)
    assert f.tipo.value_counts().to_dict() == {"RIO": 2578, "FRONTERA SECA": 1455}
    assert f.lat.between(-27.7, -19.2).all() and f.lon.between(-62.7, -54.2).all()
