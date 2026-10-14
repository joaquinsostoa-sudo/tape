import numpy as np
import pandas as pd
import pytest

from src.modelos import presente as pr


def test_productos_de_tierra_por_capitulo():
    h = pd.Series(["0102", "1201", "2403", "5201", "0301", "2709", "8544", "4403"])
    assert pr.es_de_tierra(h).tolist() == [True, True, True, True, False, False, False, False]  # pesca, petróleo, cables y madera no


def test_tierra_se_estandariza_por_anio_entre_los_paises_de_la_muestra():
    df = pd.DataFrame({"anio": [2000, 2000, 2000, 2000], "iso3": ["A", "A", "B", "B"], "hs4": ["0102", "8544", "0102", "8544"],
                       "a_pib": [0.0, 0.0, 1.0, 1.0]})
    dot = pd.DataFrame({"iso3": ["A", "B", "C"], "anio": 2000, "log_tierra": [0.0, 2.0, 4.0]})
    out = pr.agregar_tierra(df, dot)
    a = out.drop_duplicates("iso3").set_index("iso3").a_tierra
    assert a["A"] == pytest.approx(-0.7071, abs=1e-3) and a["B"] == pytest.approx(0.7071, abs=1e-3)  # C no está en la muestra
    assert out.ra_tierra.tolist() == pytest.approx([a["A"], 0.0, a["B"], 0.0])  # solo los productos de tierra llevan el término


def _panel(efecto: float, semilla: int = 0, n_c: int = 50, n_p: int = 80):
    rng = np.random.default_rng(semilla)
    filas = []
    for anio in (2000, 2005):
        cef, pef = rng.normal(0, .5, n_c), rng.normal(-1.5, .6, n_p)
        for c in range(n_c):
            for p in range(n_p):
                x = rng.normal()
                eta = cef[c] + pef[p] + efecto * x
                filas.append((f"c{c}", f"p{p}", anio, x, int(rng.random() < 1 / (1 + np.exp(-eta)))))
    df = pd.DataFrame(filas, columns=["iso3", "hs4", "anio", "ra_x", "E"])
    df["pais_ventana"] = df.iso3 + "_" + df.anio.astype(str)
    df["producto_ventana"] = df.hs4 + "_" + df.anio.astype(str)
    return df


def test_la_mejora_de_verosimilitud_detecta_un_efecto_real_y_no_inventa_uno_nulo():
    real = pr.ajustar_con_ll(_panel(0.8), ["ra_x"])
    nulo = pr.ajustar_con_ll(_panel(0.0, semilla=1), ["ra_x"])
    assert real[0].loc["ra_x", "coef"] == pytest.approx(0.8, abs=0.25) and real[1]["lr"] > 100 and real[1]["mejora_ll_por_mil"] > 10
    assert abs(nulo[0].loc["ra_x", "z"]) < 3 and nulo[1]["lr"] < 12
