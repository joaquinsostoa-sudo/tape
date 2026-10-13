import numpy as np
import pandas as pd
import pytest

from src.modelos import logit_nacional as ln


def _expo():
    filas = [(2000, "A", "0101", 60.0), (2000, "A", "0202", 40.0), (2000, "A", "2716", 1000.0),
             (2000, "B", "0101", 20.0), (2000, "B", "0202", 80.0)]
    return pd.DataFrame(filas, columns=["anio", "iso3", "hs4", "x"])


def test_rca_a_mano_y_sin_energia_ni_en_los_totales():
    r = ln.calcular_rca(_expo()).set_index(["iso3", "hs4"]).rca
    assert "2716" not in set(ln.calcular_rca(_expo()).hs4)
    assert r["A", "0101"] == pytest.approx(1.5) and r["A", "0202"] == pytest.approx(2 / 3)
    assert r["B", "0101"] == pytest.approx(0.5) and r["B", "0202"] == pytest.approx(4 / 3)


def _rca(filas):
    return pd.DataFrame(filas, columns=["anio", "iso3", "hs4", "rca"])


def test_presencia_dos_de_tres_anios_de_calendario_y_sin_datos_posteriores():
    r = _rca([(2003, "X", "1111", 1.5), (2005, "X", "1111", 1.2),  # 2 de 3 años (2003-2005): presente
              (2000, "X", "2222", 2.0), (2005, "X", "2222", 2.0),  # dos años pero lejos: no
              (2004, "X", "3333", 3.0),  # un solo año: no
              (2006, "X", "4444", 2.0), (2007, "X", "4444", 2.0)])  # después de t0: no se usa
    p = ln.presencia(r, 2005)
    assert set(zip(p.iso3, p.hs4, strict=True)) == {("X", "1111")}


def test_panel_incluye_los_que_no_exportaban_y_define_la_entrada_de_un_solo_anio():
    r = _rca([(2000, "A", "0101", 0.3), (2005, "A", "0101", 1.4),  # entra
              (2000, "A", "0202", 0.8), (2005, "A", "0202", 2.0),  # ya tenía RCA 0,8 ≥ 0,5: fuera del panel
              (2000, "B", "0101", 0.1), (2005, "B", "0101", 0.9),  # no llega a 1
              (2005, "B", "0303", 1.2)])  # B no exportaba 0303 en 2000 (RCA = 0) y entra
    p = ln.panel_ventana(r, {"A", "B"}, ["0101", "0202", "0303"], 2000, 5).set_index(["iso3", "hs4"])
    assert ("A", "0202") not in p.index
    assert p.loc[("A", "0101"), "E"] == 1 and p.loc[("B", "0101"), "E"] == 0
    assert p.loc[("B", "0303"), "rca0"] == 0 and p.loc[("B", "0303"), "E"] == 1
    assert p.loc[("A", "0303"), "E"] == 0  # tampoco exportaba y sigue sin hacerlo


def test_paises_elegibles_exige_poblacion_y_exportaciones_y_deja_fuera_los_sin_dato():
    expo = pd.DataFrame({"anio": 2000, "iso3": ["A", "B", "C", "D"], "hs4": "0101",
                         "x": [2e6, 5e5, 3e6, 4e6]})
    pob = pd.DataFrame({"anio": 2000, "iso3": ["A", "B", "C"], "poblacion": [5e6, 9e6, 5e5]})
    assert ln.paises_elegibles(expo, pob, 2000) == {"A"}  # B exporta poco, C es chico, D sin dato de población


def test_sin_variacion_quita_grupos_en_cascada():
    df = pd.DataFrame({"g": ["a", "a", "b", "b", "c", "c"], "h": ["x", "y", "x", "y", "x", "y"],
                       "E": [1, 0, 0, 0, 1, 0]})
    out = ln.sin_variacion(df, "E", ["g"])
    assert set(out.g) == {"a", "c"}


def test_requisito_de_logistica_crece_cuando_el_producto_pesa_mas_por_dolar():
    req = pd.DataFrame({"hs4": ["1", "2", "3"], "energia": [.01, .02, .03], "capital": [100., 200., 300.],
                        "habilidades": [.2, .3, .4], "valor_peso_usd_kg": [0.5, 5.0, 50.0]})
    r = ln.requisitos_estandarizados(req).set_index("hs4").r_logistica
    assert r["1"] > r["2"] > r["3"] and r.mean() == pytest.approx(0.0, abs=1e-9)


def test_recupera_coeficientes_conocidos_con_efectos_fijos():
    rng = np.random.default_rng(11)
    n_c, n_p = 70, 150
    verdad = {"d_z": 1.0, "ra_energia": 0.4, "ra_capital_humano": -0.3, "ra_credito": 0.0, "ra_logistica": 0.2}
    filas = []
    for v in (2000, 2005):
        cef, pef = rng.normal(0, .5, n_c), rng.normal(-3.0, .6, n_p)
        for c in range(n_c):
            for p in range(n_p):
                x = rng.normal(size=5)
                eta = cef[c] + pef[p] + sum(b * xi for b, xi in zip(verdad.values(), x, strict=True))
                filas.append((f"c{c}", f"p{p}", v, *x, int(rng.random() < 1 / (1 + np.exp(-eta)))))
    df = pd.DataFrame(filas, columns=["iso3", "hs4", "anio", *verdad, "E"])
    df["pais_ventana"] = df.iso3 + "_" + df.anio.astype(str)
    df["producto_ventana"] = df.hs4 + "_" + df.anio.astype(str)
    tabla, info = ln.ajustar_especificacion(df, list(verdad))
    for k, b in verdad.items():
        assert abs(tabla.loc[k, "coef"] - b) < 3 * tabla.loc[k, "ee"] + 0.02, k
    assert info["entradas"] > 500
