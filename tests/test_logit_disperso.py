import numpy as np
import pandas as pd
import pytest
import statsmodels.formula.api as smf

from src.modelos.logit_disperso import LogitEfectosFijos


def _datos(semilla=0, n_c=40, n_p=30, efecto=1.2):
    rng = np.random.default_rng(semilla)
    cef = rng.normal(0, 0.6, n_c)
    pef = rng.normal(-1.0, 0.6, n_p)
    filas = []
    for c in range(n_c):
        for p in range(n_p):
            x = rng.normal()
            pr = 1 / (1 + np.exp(-(cef[c] + pef[p] + efecto * x)))
            filas.append((f"c{c}", f"p{p}", x, int(rng.random() < pr)))
    return pd.DataFrame(filas, columns=["country", "product", "x", "E"])


def test_sin_penalizacion_coincide_con_statsmodels():
    df = _datos()
    assert df.groupby("country").E.agg(["min", "max"]).eq([0, 1]).all(axis=None)  # sin separación perfecta
    assert df.groupby("product").E.agg(["min", "max"]).eq([0, 1]).all(axis=None)
    ref = smf.logit("E ~ x + C(country) + C(product)", data=df).fit(disp=False, maxiter=200)
    m = LogitEfectosFijos(["x"], ["country", "product"], C=None).ajustar(df, "E")
    assert np.abs(m.predecir(df) - ref.predict(df).to_numpy()).max() < 2e-3
    assert m.coeficientes["x"] == pytest.approx(ref.params["x"], abs=2e-2)


def test_la_penalizacion_suave_evita_el_infinito_cuando_hay_separacion():
    df = _datos(semilla=1, n_c=20, n_p=15)
    df.loc[df["product"] == "p0", "E"] = 0  # un producto sin ninguna entrada: separación perfecta
    p = LogitEfectosFijos(["x"], ["country", "product"], C=10).ajustar(df, "E").predecir(df)
    assert np.isfinite(p).all() and p[df["product"] == "p0"].max() < p[df["product"] != "p0"].mean()


def _con_dos_variables(semilla=3, n_c=40, n_p=30):
    rng = np.random.default_rng(semilla)
    cef, pef = rng.normal(0, 0.6, n_c), rng.normal(-1.0, 0.6, n_p)
    filas = []
    for c in range(n_c):
        choque = rng.normal(0, 0.4)  # choque común del país: razón de ser del agrupamiento
        for p in range(n_p):
            x1, x2 = rng.normal() + 0.5 * choque, rng.normal()
            pr = 1 / (1 + np.exp(-(cef[c] + pef[p] + choque + 1.0 * x1 - 0.7 * x2)))
            filas.append((f"c{c}", f"p{p}", x1, x2, int(rng.random() < pr)))
    return pd.DataFrame(filas, columns=["country", "product", "x1", "x2", "E"])


def test_errores_agrupados_coinciden_con_statsmodels():
    df = _con_dos_variables()
    ref = smf.logit("E ~ x1 + x2 + C(country) + C(product)", data=df).fit(
        disp=False, maxiter=200, cov_type="cluster",
        cov_kwds={"groups": pd.factorize(df.country)[0], "use_correction": False})
    m = LogitEfectosFijos(["x1", "x2"], ["country", "product"], C=None).ajustar(df, "E")
    out = m.errores_agrupados(df, "E", "country", correccion=False)
    assert out.ee.to_numpy() == pytest.approx(ref.bse[["x1", "x2"]].to_numpy(), rel=2e-2)
    g = df.country.nunique()
    con = m.errores_agrupados(df, "E", "country")
    assert (con.ee / out.ee).to_numpy() == pytest.approx(np.sqrt(g / (g - 1)))


def test_errores_agrupados_devuelven_tabla_completa():
    df = _con_dos_variables(semilla=5)
    m = LogitEfectosFijos(["x1", "x2"], ["country", "product"], C=None).ajustar(df, "E")
    out = m.errores_agrupados(df, "E", "country")
    assert list(out.index) == ["x1", "x2"] and out.p.between(0, 1).all() and (out.ee > 0).all()
    assert out.coef.to_numpy() == pytest.approx(list(m.coeficientes.values()))


def test_la_matriz_es_dispersa_y_los_no_vistos_se_ignoran():
    df = _datos(n_c=10, n_p=8)
    m = LogitEfectosFijos(["x"], ["country", "product"]).ajustar(df, "E")
    x = m._x(df)
    assert x.nnz == 3 * len(df)  # densidad + una dummy de país + una de producto por fila
    nuevo = pd.DataFrame({"country": ["zz"], "product": ["p1"], "x": [0.0]})
    assert 0 < m.predecir(nuevo)[0] < 1
