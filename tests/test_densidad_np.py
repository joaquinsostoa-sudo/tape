import duckdb
import numpy as np
import pandas as pd
import pytest

from src.modelos import densidad as sql
from src.modelos import densidad_np as dn


def _pres(filas):
    return pd.DataFrame([(c, p) for c, ps in filas.items() for p in ps], columns=["country", "product"])


def test_ejemplo_hecho_a_mano():
    # A: c1 c2 c3 c4 | B: c1 c2 c3 c5 | C: c2 c4 c6. Conjuntos: AB=3, AC=2, BC=1 (c2). Umbral 2: BC no cuenta.
    pres = _pres({"c1": "AB", "c2": "ABC", "c3": "AB", "c4": "AC", "c5": "B", "c6": "C"})
    m, paises, productos = dn.matriz_presencia(pres)
    phi = dn.proximidad(m, umbral=2)
    a, b, c = (list(productos).index(x) for x in "ABC")
    assert phi[a, b] == pytest.approx(0.75)  # min(3/4, 3/4)
    assert phi[a, c] == pytest.approx(0.5)  # min(2/4, 2/3)
    assert phi[b, c] == 0.0  # solo 1 país en común (< umbral)
    assert np.allclose(phi, phi.T) and (np.diag(phi) == 0).all()
    d = dn.densidad(m, phi)
    c5, c6 = list(paises).index("c5"), list(paises).index("c6")
    assert d[c5, a] == pytest.approx(0.75 / 1.25)  # c5 solo tiene B: (φ_AB·1 + φ_AC·0) / (φ_AB + φ_AC)
    assert d[c6, a] == pytest.approx(0.5 / 1.25)  # c6 solo tiene C
    assert d[c5, c] == 0.0  # C solo es cercano a A, y c5 no tiene A


def test_producto_sin_vecinos_tiene_densidad_cero():
    pres = _pres({"c1": "AB", "c2": "AB", "c3": "AB", "c4": "AB", "c5": "AB", "c6": "Z"})  # Z solo en un país
    df = dn.densidad_df(pres, pres.assign(product="Z"), umbral=5)
    assert (df.densidad == 0.0).all()


def test_pares_fuera_de_la_presencia_valen_cero():
    pres = _pres({"c1": "AB", "c2": "AB", "c3": "AB", "c4": "AB", "c5": "AB"})
    base = pd.DataFrame({"country": ["c1", "c9", "c1"], "product": ["A", "A", "Q"]})  # c9 y Q no están en la presencia
    df = dn.densidad_df(pres, base, umbral=5).set_index(["country", "product"]).densidad
    assert df[("c1", "A")] == pytest.approx(1.0)  # A solo tiene a B como vecino y c1 lo tiene
    assert df[("c9", "A")] == 0.0 and df[("c1", "Q")] == 0.0


def test_main_escribe_las_tablas_de_densidad_en_la_base(tmp_path, monkeypatch):
    rng = np.random.default_rng(7)
    pres_m = rng.random((30, 40)) < 0.4
    pres = pd.DataFrame([(f"c{c:02d}", f"{p:04d}") for c, p in zip(*np.nonzero(pres_m), strict=True)],
                        columns=["country", "product"])
    base = pd.DataFrame([(f"c{c:02d}", f"{p:04d}") for c in range(30) for p in range(40)], columns=["country", "product"])
    base["year"] = 2004
    db = tmp_path / "t.duckdb"
    con = duckdb.connect(str(db))
    con.register("p", pres)
    con.register("b", base)
    monkeypatch.setattr(sql, "VENTANAS", [(2000, 2004)])
    con.execute("CREATE TABLE presencia_2000_2004 AS SELECT * FROM p")
    con.execute("CREATE TABLE rca_matrix AS SELECT year, country, product, 1.0 AS rca FROM b")
    con.close()
    dn.main(["--db", str(db), "--phi-dir", str(tmp_path / "phi")])
    con = duckdb.connect(str(db))
    n, cols = con.execute("SELECT count(*) FROM densidad_2000_2004").fetchone()[0], [
        c[0] for c in con.execute("SELECT * FROM densidad_2000_2004 LIMIT 1").description]
    con.close()
    assert n == 30 * 40 and cols == ["country", "product", "densidad"]  # las mismas columnas que lee backtest.py
    assert (tmp_path / "phi" / "phi_2000_2004.parquet").exists()


@pytest.mark.parametrize("semilla", [0, 1, 2])
def test_coincide_con_la_version_sql(semilla):
    """La versión en memoria da la misma densidad que `densidad.calcular_phi/calcular_densidad` (DuckDB)."""
    rng = np.random.default_rng(semilla)
    n_c, n_p = 40, 70
    probas = rng.uniform(0.05, 0.6, n_p)  # productos de distinta ubicuidad
    pres_m = rng.random((n_c, n_p)) < probas
    pres = pd.DataFrame([(f"c{c:02d}", f"{p:04d}") for c, p in zip(*np.nonzero(pres_m), strict=True)],
                        columns=["country", "product"])
    pres["has_rca"] = 1
    base = pd.DataFrame([(f"c{c:02d}", f"{p:04d}") for c in range(n_c) for p in range(n_p)], columns=["country", "product"])
    base["year"] = 2004

    con = duckdb.connect()
    con.register("tmp_pres", pres)
    con.register("tmp_base", base)
    con.execute("CREATE TABLE presencia_2000_2004 AS SELECT * FROM tmp_pres")
    con.execute("CREATE TABLE rca_matrix AS SELECT year, country, product, 1.0 AS rca FROM tmp_base")
    sql.calcular_phi(con, 2000, 2004)
    sql.calcular_densidad(con, 2000, 2004)
    esperado = con.execute("SELECT country, product, densidad FROM densidad_2000_2004").fetchdf()
    obtenido = dn.densidad_df(pres, base)
    j = esperado.merge(obtenido, on=["country", "product"], suffixes=("_sql", "_np"))
    assert len(j) == len(esperado) == n_c * n_p
    assert np.allclose(j.densidad_sql, j.densidad_np, atol=1e-5)
    assert j.densidad_sql.max() > 0.2  # el caso no es trivial
