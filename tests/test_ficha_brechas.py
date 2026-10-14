import numpy as np
import pandas as pd
import pytest

from src.modelos import ficha_brechas as fb


def test_percentiles_y_mediana_de_productores_sin_paraguay():
    dot = pd.DataFrame({"iso3": list("ABCDE") + ["PRY"], "x": [1.0, 2, 3, 4, 5, 3.5]})
    pct = fb.percentiles(dot, ["x"])
    assert pct.loc["PRY", "x"] == pytest.approx(100 * 4 / 6) and pct.loc["A", "x"] == pytest.approx(100 / 6)
    mediana, n = fb.mediana_productores(pct, {"A", "C", "E", "PRY"})  # Paraguay no cuenta como productor de su propia referencia
    assert n == 3 and mediana["x"] == pytest.approx(pct.loc["C", "x"])
    vacio, n0 = fb.mediana_productores(pct, {"PRY"})
    assert n0 == 0 and np.isnan(vacio["x"])


def _datos(n_paises: int = 12):
    """Mundo sintético: los países de ingreso alto (índices altos) producen el producto «0001»; Paraguay no."""
    paises = [f"P{i:02d}" for i in range(n_paises - 1)] + ["PRY"]
    filas = []
    for anio in range(2003, 2011):
        for k, p in enumerate(paises):
            fuerte = k >= 6 and p != "PRY"
            filas.append((anio, p, "0001", 5_000_000.0 if fuerte else 1.0))
            filas.append((anio, p, "0002", 5_000_000.0))
            filas.append((anio, p, "0003", 3_000_000.0 if k % 2 else 1.0))
    expo = pd.DataFrame(filas, columns=["anio", "iso3", "hs4", "x"])
    dot = pd.DataFrame({"iso3": paises, "anio": 2010, **{c: np.arange(n_paises, dtype=float) for c in fb.CAPAS}})
    dot.loc[dot.iso3 == "PRY", list(fb.CAPAS)] = 2.0  # Paraguay está en el tercio bajo de todas las dotaciones
    pob = pd.DataFrame({"iso3": paises, "anio": 2010, "poblacion": 5_000_000.0})
    return expo, dot, pob


def test_ficha_de_un_producto_que_hacen_los_mas_dotados():
    expo, dot, pob = _datos()
    f = fb.ficha(expo, dot, pob, "0001", 2010)
    assert f["n_productores"] == 5 and "PRY" not in f["productores"]
    t = f["tabla"].set_index("columna")
    assert t.loc["hc", "paraguay"] < t.loc["hc", "productores"]  # Paraguay por debajo de los productores
    assert t.loc["hc", "brecha_productores"] > 30 and (t.brecha_productores.dropna() > 0).all()
    assert f["confianza"] in {"alta", "media"}
