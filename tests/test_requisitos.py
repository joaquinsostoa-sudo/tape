import zipfile

import numpy as np
import pandas as pd
import pytest

from src.puentes import requisitos as r


def test_intensidades_naics_son_razon_de_sumas_y_el_capital_usa_su_propia_ventana():
    nber = pd.DataFrame({
        "naics": ["A", "A", "A", "B", "B"],
        "year": [2012, 2013, 2018, 2012, 2018],
        "emp": [10.0, 30.0, 10.0, 5.0, 5.0],
        "prode": [8.0, 24.0, 6.0, 1.0, 1.0],
        "vship": [100.0, 300.0, 100.0, 50.0, 50.0],
        "energy": [10.0, 30.0, 20.0, 5.0, 5.0],
        "cap": [200.0, 600.0, np.nan, 50.0, np.nan],  # el capital no existe en 2018
    })
    out = r.intensidades_naics(nber).set_index("naics")
    assert out.loc["A", "energia"] == pytest.approx((10 + 30 + 20) / (100 + 300 + 100))
    assert out.loc["A", "habilidades"] == pytest.approx(1 - (8 + 24 + 6) / (10 + 30 + 10))
    assert out.loc["A", "capital"] == pytest.approx((200 + 600) / (10 + 30))  # 2018 queda fuera
    assert out.loc["B", "capital"] == pytest.approx(50 / 5)


def test_hs12_a_naics_reparte_por_lineas_hs10_y_completa_ceros(tmp_path):
    cab = "commodity\tyear\tsic\tsic_matchtype\tnaics\tnaics_matchtype\tnaicsX\n"
    exp = cab + "".join(f"{c}\t2015\t0116\tx\t{n}\tFrom Census\t{n}\n" for c, n in [
        ("0101110010", "111111"), ("0101110020", "111111"), ("0101110030", "111112"),  # HS6 010111: 2/3 y 1/3
        ("202400000", "111113"),  # 9 dígitos: el archivo pierde el cero inicial; equivale a 0202400000 (HS6 020240)
        ("0202300000", ""),  # sin NAICS: se ignora
        ("0303000000", "311711")])  # año fuera de la ventana abajo
    imp = cab + "0101110010\t2015\t0116\tx\t111111\tFrom Census\t111111\n"  # duplicado de una línea: no suma
    imp += "0404000000\t2010\t0116\tx\t311513\tFrom Census\t311513\n"  # año fuera de la ventana
    ruta = tmp_path / "c.zip"
    with zipfile.ZipFile(ruta, "w") as z:
        z.writestr("hs_sic_naics_exports_89_117_20180927.csv", exp)
        z.writestr("hs_sic_naics_imports_89_117_20180927.csv", imp)
    t = r.hs12_a_naics(ruta, anios=("2015",)).set_index(["source", "target"]).weight
    assert t[("010111", "111111")] == pytest.approx(2 / 3)
    assert t[("010111", "111112")] == pytest.approx(1 / 3)
    assert t[("020240", "111113")] == 1.0  # el 9-dígitos se completó con ceros a la izquierda
    assert not any(s == "020230" for s, _ in t.index)  # 0202300000 no tiene NAICS
    assert not any(s == "040400" for s, _ in t.index)  # fuera de ventana


def test_promedio_por_cadena_pondera_los_caminos_y_mide_cobertura():
    hs92_hs12 = pd.DataFrame({"source": ["A", "A"], "target": ["X", "Y"], "weight": [0.5, 0.5]})
    hs12_naics = pd.DataFrame({"source": ["X", "Y", "Y"], "target": ["N1", "N2", "N3"], "weight": [1.0, 0.5, 0.5]})
    naics = pd.DataFrame({"naics": ["N1", "N2"], "energia": [0.10, 0.30], "capital": [100.0, 300.0],
                          "habilidades": [0.2, 0.4]})  # N3 no tiene dato
    out = r.promedio_por_cadena(hs92_hs12, hs12_naics, naics).set_index("hs92").loc["A"]
    # caminos con dato: A-X-N1 (peso 0.5) y A-Y-N2 (peso 0.25): promedio ponderado de 0.10 y 0.30
    assert out.energia == pytest.approx((0.5 * 0.10 + 0.25 * 0.30) / 0.75)
    assert out.cobertura == pytest.approx(0.75)  # el camino A-Y-N3 (0.25) no tiene dato
    assert out.peso_top == pytest.approx(0.5)  # el camino principal pesa la mitad


def test_producto_sin_ningun_hs12_en_la_concordancia_queda_sin_cobertura():
    hs92_hs12 = pd.DataFrame({"source": ["A", "B"], "target": ["X", "Z"], "weight": [1.0, 1.0]})
    hs12_naics = pd.DataFrame({"source": ["X"], "target": ["N1"], "weight": [1.0]})
    naics = pd.DataFrame({"naics": ["N1"], "energia": [0.1], "capital": [1.0], "habilidades": [0.2]})
    out = r.promedio_por_cadena(hs92_hs12, hs12_naics, naics).set_index("hs92")
    assert out.loc["A", "cobertura"] == 1.0
    assert "B" not in out.index or out.loc["B", "cobertura"] == 0.0


def test_confianza_por_cobertura_y_ambiguedad():
    assert r.confianza(1.0, 0.9) == "alta"
    assert r.confianza(1.0, 0.5) == "media"  # llega a una industria, pero el reparto es ambiguo
    assert r.confianza(0.5, 1.0) == "media"
    assert r.confianza(0.2, 1.0) == "baja"
    assert r.confianza(0.0, 1.0) == "sin_dato"
    assert r.confianza(float("nan"), 1.0) == "sin_dato"


def test_agregar_hs4_pondera_por_valor_mundial_y_agrupa_valor_peso():
    hs6 = pd.DataFrame({
        "hs92": ["010111", "010119", "020000"],
        "energia": [0.10, 0.30, np.nan], "capital": [100.0, 300.0, np.nan], "habilidades": [0.2, 0.4, np.nan],
        "cobertura": [1.0, 0.5, 0.0], "peso_top": [1.0, 1.0, 0.0],
        "valor_con_peso": [100.0, 300.0, np.nan], "toneladas": [50.0, 50.0, np.nan],
    })
    valor = pd.Series({"010111": 100.0, "010119": 300.0, "020000": 50.0})
    out = r.agregar_hs4(hs6, valor).set_index("hs4")
    assert out.loc["0101", "energia"] == pytest.approx((100 * 0.10 + 300 * 0.30) / 400)
    assert out.loc["0101", "cobertura"] == pytest.approx((100 * 1.0 + 300 * 0.5) / 400)
    assert out.loc["0101", "valor_peso_usd_kg"] == pytest.approx(400 / 100)  # agrupado, no promedio de razones
    assert out.loc["0200", "confianza"] == "sin_dato" and np.isnan(out.loc["0200", "energia"])


@pytest.fixture(scope="module")
def hs4():
    if not r.SALIDA_HS4.exists():
        pytest.skip("falta data/clean/requisitos_producto.parquet (correr src.puentes.requisitos)")
    return pd.read_parquet(r.SALIDA_HS4).set_index("hs4")


def test_los_rankings_tienen_sentido_economico(hs4):
    assert hs4.loc["7601", "energia"] > hs4.loc["8471", "energia"] * 10  # aluminio vs computadoras
    assert hs4.loc["2523", "energia"] > hs4.loc["6109", "energia"]  # cemento vs camisetas
    assert hs4.loc["8471", "habilidades"] > hs4.loc["0202", "habilidades"]  # computadoras vs carne
    assert hs4.loc["1507", "capital"] > hs4.loc["0202", "capital"]  # aceite de soja vs carne bovina


def test_agro_y_minerales_sin_dato_y_sin_valores_imposibles(hs4):
    assert hs4.loc["1201", "confianza"] == "sin_dato"  # soja en grano: no es manufactura
    assert hs4.loc["5201", "confianza"] == "sin_dato"  # algodón
    d = hs4[hs4.confianza != "sin_dato"][["energia", "capital", "habilidades"]]
    assert np.isfinite(d.to_numpy()).all() and (d >= 0).all().all()
    assert hs4.habilidades.dropna().between(0, 1).all()
    assert hs4.energia.dropna().between(0, 1).all()


def test_cobertura_del_valor_mundial(hs4):
    v = hs4.valor_mundial
    con_dato = v[hs4.confianza != "sin_dato"].sum() / v.sum()
    assert 0.8 < con_dato < 0.95  # el resto es agro, minería y energía
