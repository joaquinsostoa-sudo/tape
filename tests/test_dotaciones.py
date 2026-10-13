import json

import numpy as np
import pandas as pd
import pytest

from src.limpieza import dotaciones as d


def test_log_positivo_deja_vacio_lo_que_no_es_positivo():
    out = d.log_positivo(pd.Series([1.0, np.e, 0.0, -5.0, np.nan]))
    assert out.iloc[0] == pytest.approx(0.0) and out.iloc[1] == pytest.approx(1.0)
    assert out.iloc[2:].isna().all()


def test_estandarizar_por_anio_es_independiente_en_cada_anio():
    df = pd.DataFrame({"anio": [2000] * 3 + [2001] * 3 + [2001],
                       "x": [1.0, 2.0, 3.0, 10.0, 20.0, 30.0, np.nan]})
    z, pct = d.estandarizar_por_anio(df, "x")
    for a in (2000, 2001):
        g = z[(df.anio == a) & df.x.notna()]
        assert g.mean() == pytest.approx(0.0) and g.std() == pytest.approx(1.0)
    assert z.iloc[0] == pytest.approx(z.iloc[3])  # 1,2,3 y 10,20,30 quedan en la misma posición relativa
    assert pct.iloc[2] == 1.0 and pct.iloc[0] == pytest.approx(1 / 3)
    assert np.isnan(z.iloc[6])


def test_arrastrar_ediciones_solo_hacia_adelante():
    lpi = pd.DataFrame({"iso3": ["AAA", "AAA"], "anio": [2010, 2014], "valor": [3.0, 4.0]})
    out = d.arrastrar_ediciones(lpi, anios=range(2008, 2017)).set_index("anio")
    assert out.loc[2008:2009, "lpi"].isna().all()  # antes de la primera edición no se inventa nada
    assert (out.loc[2010:2013, "lpi"] == 3.0).all() and (out.loc[2010:2013, "lpi_edicion_anio"] == 2010).all()
    assert (out.loc[2014:2016, "lpi"] == 4.0).all() and (out.loc[2014:2016, "lpi_edicion_anio"] == 2014).all()


def test_leer_wdi_descarta_agregados_y_valores_vacios(tmp_path):
    reg = lambda iso, fecha, v: {"countryiso3code": iso, "date": fecha, "value": v}
    datos = [{"page": 1}, [reg("PRY", "2015", 43.3), reg("WLD", "2015", 99.0), reg("PRY", "2016", None),
                           reg("BRA", "2015", 60.1)]]
    (tmp_path / "wdi_X.Y_p1.json").write_text(json.dumps(datos), encoding="utf-8")
    out = d.leer_wdi("X.Y", {"PRY", "BRA"}, tmp_path)
    assert sorted(out.iso3) == ["BRA", "PRY"] and len(out) == 2  # sin el agregado WLD ni el valor vacío
    assert out[out.iso3 == "PRY"].valor.item() == 43.3


@pytest.fixture(scope="module")
def tabla():
    if not d.SALIDA.exists():
        pytest.skip("falta data/clean/dotaciones.parquet (correr src.limpieza.dotaciones)")
    return pd.read_parquet(d.SALIDA)


def test_paraguay_coincide_con_las_fuentes(tabla):
    py = tabla[(tabla.iso3 == "PRY") & (tabla.anio == 2015)].iloc[0]
    pwt = d.leer_pwt()
    assert py.hc == pytest.approx(pwt[(pwt.iso3 == "PRY") & (pwt.anio == 2015)].hc.item())
    assert py.lpi_edicion_anio == 2014  # el LPI de 2015 es la edición de 2014 arrastrada
    assert 0 < py.pct_capital_humano < 1


def test_estandarizacion_y_cobertura(tabla):
    for capa in d.CAPAS:
        z = tabla[tabla.anio == 2015][f"z_{capa}"]
        assert z.mean() == pytest.approx(0.0, abs=1e-9) and z.std() == pytest.approx(1.0)
    assert tabla[tabla.anio == 2015].z_capital_humano.notna().sum() > 120
    assert tabla[tabla.anio < 2007].lpi.isna().all()  # no hay LPI antes de su primera edición
    assert tabla[tabla.anio > 2019].hc.isna().all()  # PWT 10.01 termina en 2019
    assert not set(tabla.iso3) & {"WLD", "EUU", "LCN"}  # sin agregados regionales


def test_las_capas_estan_correlacionadas_como_se_documento(tabla):
    c = tabla[tabla.anio == 2015][[f"z_{x}" for x in d.CAPAS]].corr()
    assert (c.to_numpy()[np.triu_indices(4, 1)] > 0.5).all()  # advertencia de colinealidad para el modelo
