import json

import pytest

from src.limpieza import mic_red_electrica as m


@pytest.fixture(scope="module")
def datos():
    if not m.JSON_ELEC.exists():
        pytest.skip("falta el JSON de la red eléctrica en data/raw/mic_mapa")
    return json.loads(m.JSON_ELEC.read_text(encoding="utf-8"))


def test_subestaciones_dentro_de_paraguay_y_unicas(datos):
    s = m.subestaciones(datos)
    assert len(s) == 104 and s.nombre.is_unique
    assert s.lat.between(-27.7, -19.2).all() and s.lon.between(-62.7, -54.2).all()
    assert {"220 kV", "23 kV", "500 kV"} <= set(s.nivel_tension)
    assert s.nivel_tension.value_counts()[["220 kV", "23 kV", "500 kV"]].tolist() == [32, 64, 6]


def test_potencia_larga_cubre_cada_subestacion_y_anio(datos):
    p = m.potencia_larga(datos)
    assert len(p) == 104 * len(m.ANIOS_23KV) + 104 * len(m.ANIOS_220_66KV)
    assert p.potencia_disp_mw.dropna().ge(0).all()
    vacias = p[p.potencia_disp_mw.isna()]
    assert set(vacias.subestacion) == {"SE023kV_LUQUE"} and set(vacias.red) == {"220/66kV"}
    assert p.groupby(["subestacion", "red"]).anio.nunique().min() == 7


def test_potencia_2026_coincide_con_el_mapa(datos):
    """La potencia 23 kV de 2026 de la tabla debe ser la que el mapa asigna a cada subestación."""
    s = m.subestaciones(datos).set_index("nombre")
    p = m.potencia_larga(datos)
    p23 = p[(p.red == "23kV") & (p.anio == 2026)].set_index("subestacion").potencia_disp_mw
    comunes = s.index.intersection(p23.index)
    assert len(comunes) == 104
    assert (s.loc[comunes, "pd_23kv_2026_mw"].astype(float) == p23.loc[comunes]).all()


def test_lineas_tienen_cuatro_tipos(datos):
    l = m.lineas(datos)
    assert set(l.serie) == {"CENTRAL HIDROELECTRICA", "CORREDOR COMPUESTO 220 KV", "LINEA DE TRANSMISION",
                            "LINEA TRONCAL 500 KV"}
    assert l.lat.between(-27.7, -19.2).all() and l.lon.between(-62.7, -54.2).all()
