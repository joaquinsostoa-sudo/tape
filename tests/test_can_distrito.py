import pandas as pd
import pytest

from src.limpieza import can_distrito as m


@pytest.fixture(scope="module")
def datos():
    if not m.XLSX.exists():
        pytest.skip("falta el Excel de fincas por distrito en data/raw/censo_agropecuario")
    return m.leer()


def test_distritos_suman_el_total_de_cada_departamento(datos):
    t, _ = datos
    dist = t[t.distrito_codigo.notna()].groupby("dep_codigo")[["fincas", "superficie_ha"]].sum()
    dep = t[t.distrito_codigo.isna()].set_index("dep_codigo")[["fincas", "superficie_ha"]]
    assert len(dep) == 17
    assert (dist.fincas == dep.fincas).all()
    assert ((dist.superficie_ha - dep.superficie_ha).abs() < 0.5).all()


def test_totales_departamentales_coinciden_con_el_volumen_i(datos):
    if not m.VOLUMEN_I.exists():
        pytest.skip("falta el Volumen I del CAN")
    t, _ = datos
    dep = t[t.distrito_codigo.isna()].set_index("dep_codigo")
    v1 = m.totales_volumen_i().set_index("dep_codigo")
    assert (dep.fincas == v1.fincas).all()
    assert ((dep.superficie_ha - v1.superficie_ha).abs() < 0.01).all()


def test_total_nacional_del_censo(datos):
    t, _ = datos
    dist = t[t.distrito_codigo.notna()]
    assert dist.fincas.sum() == 291_497 and len(dist) == 259
    assert round(dist.superficie_ha.sum()) == 30_401_660


def test_los_estratos_suman_el_total_salvo_un_distrito_de_la_fuente(datos):
    t, e = datos
    s = e.groupby(["dep_codigo", "distrito_codigo"], dropna=False)[["fincas", "superficie_ha"]].sum().reset_index()
    j = s.merge(t, on=["dep_codigo", "distrito_codigo"], suffixes=("_est", "_tot"))
    mal = j[(j.fincas_est != j.fincas_tot) | ((j.superficie_ha_est - j.superficie_ha_tot).abs() > 1)]
    # inconsistencia de la fuente: Mayor José J. Martínez (Ñeembucú) trae estratos que no suman su total
    assert mal.distrito_codigo.tolist() == ["1210"]


def test_union_con_las_ciudades_del_mapa_mic(datos):
    ruta = m.CLEAN / "ciudades_mic.csv"
    if not ruta.exists():
        pytest.skip("falta ciudades_mic.csv")
    t, _ = datos
    u = m.unir_ciudades(t, pd.read_csv(ruta))
    assert len(u) == 263 and u.en_can.sum() == 259
    assert set(u.loc[~u.en_can, "ciudad"]) == {"ASUNCION", "CIUDAD DEL ESTE", "ITACUA", "NUEVA ASUNCION"}
    assert u.fincas.sum() == 291_497
    assert len(set(m.ALIAS_MIC.values())) == len(m.ALIAS_MIC)
