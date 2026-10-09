import json

import pandas as pd
import pytest

from src.limpieza import mic_aduanas as m


@pytest.fixture(scope="module")
def datos():
    if not m.JSON_ADUANAS.exists():
        pytest.skip("falta el JSON de aduanas en data/raw/mic_mapa")
    return json.loads(m.JSON_ADUANAS.read_text(encoding="utf-8"))


def test_importaciones_del_detalle_y_del_mapa_coinciden(datos):
    det, pts = m.detalle(datos), m.mapa(datos)
    total = datos["total_pivot"]["imp_usd_cif"]
    assert round(det.imp_usd_cif.sum()) == round(pts.imp_usd_cif.sum()) == total == 20_012_428_317


def test_exportaciones_cif_del_mapa_superan_a_las_fob_del_detalle(datos):
    det, pts = m.detalle(datos), m.mapa(datos)
    assert pts.exp_usd.sum() > det.exp_usd.sum()


def test_filas_sin_operaciones(datos):
    det = m.detalle(datos)
    assert len(det) == 42 and det.con_operaciones.sum() == 33
    assert det.loc[~det.con_operaciones, "imp_usd_cif"].isna().all()


def test_ciudad_y_punto_se_separan_del_nombre(datos):
    det = m.detalle(datos).set_index("red_aduanera")
    f = det.loc["ASUNCION - Puerto Fluvial (Ita Enramada)"]
    assert f.ciudad_aduana == "ASUNCION" and f.punto == "Puerto Fluvial (Ita Enramada)"


def test_union_con_coordenadas_es_exacta_o_se_declara(datos):
    u = m.unir_coordenadas(m.detalle(datos), m.mapa(datos))
    assert len(u) == 42
    assert set(u.union_mapa) == {"exacta", "sin_coordenadas"}
    assert u[u.union_mapa == "exacta"][["lat", "lon"]].notna().all().all()
    # los 9 sin operaciones nunca tienen coordenadas
    assert (u.loc[~u.con_operaciones, "union_mapa"] == "sin_coordenadas").all()


def test_ranking_trae_las_35_aduanas(datos):
    r = m.ranking(datos)
    assert len(r) == 35 and r.aduana_dna.is_unique
    assert r.loc[r.aduana_dna == "TERPORT", "imp_usd_cif"].item() == 2_455_661_736


def test_puntos_dentro_de_paraguay(datos):
    p = m.mapa(datos)
    assert p.lat.between(-27.7, -19.2).all() and p.lon.between(-62.7, -54.2).all()
    assert isinstance(p, pd.DataFrame)
