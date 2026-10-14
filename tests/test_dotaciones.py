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


def test_arrastrar_ediciones_solo_hacia_adelante_si_se_pide():
    lpi = pd.DataFrame({"iso3": ["AAA", "AAA"], "anio": [2010, 2014], "valor": [3.0, 4.0]})
    out = d.arrastrar_ediciones(lpi, anios=range(2008, 2017), hacia_atras=False).set_index("anio")
    assert out.loc[2008:2009, "lpi"].isna().all()  # antes de la primera edición no se inventa nada
    assert (out.loc[2010:2013, "lpi"] == 3.0).all() and (out.loc[2010:2013, "lpi_edicion_anio"] == 2010).all()
    assert (out.loc[2014:2016, "lpi"] == 4.0).all() and (out.loc[2014:2016, "lpi_edicion_anio"] == 2014).all()


def test_arrastrar_primera_edicion_hacia_atras_y_la_marca():
    lpi = pd.DataFrame({"iso3": ["AAA", "AAA"], "anio": [2010, 2014], "valor": [3.0, 4.0]})
    out = d.arrastrar_ediciones(lpi, anios=range(2008, 2017)).set_index("anio")
    assert (out.loc[2008:2009, "lpi"] == 3.0).all() and out.loc[2008:2009, "lpi_hacia_atras"].all()
    assert not out.loc[2010:2016, "lpi_hacia_atras"].any()  # desde la primera edición el dato es real
    assert (out.loc[2010:2013, "lpi"] == 3.0).all() and (out.loc[2014:2016, "lpi"] == 4.0).all()


def test_leer_wdi_descarta_agregados_y_valores_vacios(tmp_path):
    def reg(iso, fecha, v):
        return {"countryiso3code": iso, "date": fecha, "value": v, "country": {"value": iso}}

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
    fila = pwt[(pwt.iso3 == "PRY") & (pwt.anio == 2015)].iloc[0]
    assert py.log_capital_trabajador == pytest.approx(np.log(fila.rnna / fila.emp))  # capital real por trabajador


def test_capital_fisico_cubre_mas_paises_que_el_capital_humano_en_2000(tabla):
    z = tabla[tabla.anio == 2000]
    assert z.z_capital_fisico.notna().sum() > z.z_capital_humano.notna().sum()
    assert z.z_capital_fisico.mean() == pytest.approx(0.0, abs=1e-9)


def test_estandarizacion_y_cobertura(tabla):
    for capa in d.CAPAS:
        z = tabla[tabla.anio == 2015][f"z_{capa}"]
        assert z.mean() == pytest.approx(0.0, abs=1e-9) and z.std() == pytest.approx(1.0)
    assert tabla[tabla.anio == 2015].z_capital_humano.notna().sum() > 120
    antes = tabla[tabla.anio < 2007].dropna(subset=["lpi"])
    assert antes.lpi_hacia_atras.all() and (antes.lpi_edicion_anio >= 2007).all()  # D14: todo LPI previo es retroceso
    assert not tabla[tabla.anio >= 2010].query("lpi_edicion_anio == 2007").lpi_hacia_atras.any()  # y lo real no se marca
    assert tabla[tabla.anio > 2023].hc.isna().all()  # PWT 11.0 termina en 2023
    assert not set(tabla.iso3) & {"WLD", "EUU", "LCN"}  # sin agregados regionales


def test_leer_wdi_se_queda_con_la_fila_del_pais_y_no_con_las_ciudades(tmp_path):
    def reg(iso, fecha, v, nombre):
        return {"countryiso3code": iso, "date": fecha, "value": v, "country": {"value": nombre}}

    datos = [{"page": 1}, [reg("IND", "2019", 16.3, "Delhi"), reg("IND", "2019", 20.3, "Mumbai"),
                           reg("IND", "2019", 18.2, "India"),  # la fila del país: promedio ponderado de las ciudades
                           reg("PRY", "2019", 6.6, "Paraguay"),
                           reg("XXX", "2019", 10.0, "Ciudad A"), reg("XXX", "2019", 20.0, "Ciudad B")]]
    (tmp_path / "wdi_P.Q_p1.json").write_text(json.dumps(datos), encoding="utf-8")
    nombres = {"IND": "India", "PRY": "Paraguay", "XXX": "Xlandia"}
    out = d.leer_wdi("P.Q", {"IND", "PRY", "XXX"}, tmp_path, nombres=nombres).set_index("iso3").valor
    assert out["IND"] == 18.2 and out["PRY"] == 6.6
    assert out["XXX"] == 15.0  # ninguna lleva el nombre de la economía: se promedian


def test_precio_promedio_usa_solo_los_anios_con_precio():
    df = pd.DataFrame({"iso3": ["A", "A", "A", "B"], "anio": [2013, 2015, 2017, 2020],
                       "precio_electricidad_db": [100.0, 10.0, 20.0, 99.0]})
    p = d.precio_promedio(df, anios=range(2014, 2020))
    assert p["A"] == 15.0  # el dato de 2013 queda fuera
    assert "B" not in p.index  # su único dato es de 2020, fuera de la ventana


def test_una_fila_por_pais_y_anio(tabla):
    assert not tabla.duplicated(["iso3", "anio"]).any()  # las filas por ciudad de Doing Business no deben duplicar


def test_energia_es_el_precio_de_la_electricidad_y_paraguay_es_barato(tabla):
    py = tabla[(tabla.iso3 == "PRY") & (tabla.anio == 2015)].iloc[0]
    assert py.precio_electricidad_kwh == pytest.approx(6.6, abs=0.3)  # centavos de USD por kWh
    assert py.pct_energia > 0.85  # entre los más baratos: la capa mide "barato = mejor"
    assert tabla[tabla.iso3 == "PRY"].z_energia.round(9).nunique() == 1  # característica estable, igual en todos los años
    assert py.hidro > 95  # casi toda la electricidad de Paraguay es hidroeléctrica
    caro = tabla[(tabla.iso3 == "DEU") & (tabla.anio == 2015)].iloc[0]
    assert caro.z_energia < 0 < py.z_energia


def test_capas_correlacionadas_salvo_la_energia(tabla):
    c = tabla[tabla.anio == 2015][[f"z_{x}" for x in d.CAPAS]].corr()
    otras = c.loc[["z_capital_humano", "z_credito", "z_logistica"], ["z_capital_humano", "z_credito", "z_logistica"]]
    assert (otras.to_numpy()[np.triu_indices(3, 1)] > 0.5).all()  # advertencia de colinealidad entre estas tres
    assert c.loc["z_energia", ["z_capital_humano", "z_credito", "z_logistica"]].abs().max() < 0.3  # el precio es independiente


def test_salario_medio_en_usd_a_mano():
    pwt = pd.DataFrame({"labsh": [0.5], "cgdpo": [2000.0], "pl_gdpo": [0.4], "emp": [10.0]})  # PIB de mercado = 800 millones de USD; 10 millones de trabajadores
    assert d.salario_usd(pwt).iloc[0] == pytest.approx(0.5 * 800 / 10 * 1.0)  # 40 USD por trabajador (millones sobre millones)


def test_salario_de_paraguay_es_razonable_y_la_mano_de_obra_barata_es_su_inverso(tabla):
    py = tabla[(tabla.iso3 == "PRY") & (tabla.anio == 2015)].iloc[0]
    assert 3_000 < py.salario_usd < 12_000 and py.menos_log_salario == pytest.approx(-np.log(py.salario_usd))
    assert tabla[tabla.anio == 2015].menos_log_salario.notna().sum() > 120


def test_impuesto_sobre_utilidades_de_paraguay_y_arrastre_posterior_a_2019(tabla):
    py = tabla[tabla.iso3 == "PRY"].set_index("anio")
    assert py.loc[2015, "impuesto_utilidades"] == pytest.approx(9.6, abs=0.5) and py.loc[2015, "menos_impuesto_utilidades"] == pytest.approx(-py.loc[2015, "impuesto_utilidades"])
    assert not py.loc[2019, "impuesto_arrastrado"] and py.loc[2022, "impuesto_arrastrado"]  # después de 2019 se arrastra el último dato
    assert py.loc[2022, "impuesto_utilidades"] == py.loc[2019, "impuesto_utilidades"]
    assert tabla[tabla.anio == 2015].impuesto_utilidades.notna().sum() > 150
