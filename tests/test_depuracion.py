import pandas as pd
import pytest

from src.limpieza import depuracion as d


def _datos(tmp_path):
    expo = pd.DataFrame({"anio": [2019] * 6, "codigo_baci": [600, 600, 600, 600, 600, 999], "hs6": ["851712", "120100", "271600", "010110", "010190", "010110"],
                         "valor_miles_usd": [1000.0, 5000.0, 2000.0, 50.0, 400.0, 700.0], "toneladas": [1.0] * 6})
    impo = pd.DataFrame({"anio": [2019] * 3, "codigo_baci": [600, 600, 600], "hs6": ["851712", "120100", "010110"], "valor_miles_usd": [500.0, 100.0, 50.0], "toneladas": [1.0] * 3})
    pu = pd.DataFrame({"codigo_baci": [600], "iso3": ["PRY"]})
    ruta = {k: tmp_path / f"{k}.parquet" for k in ("expo", "impo", "salida", "hs4")}
    expo.to_parquet(ruta["expo"])
    impo.to_parquet(ruta["impo"])
    pu.to_csv(tmp_path / "pu.csv", index=False)
    return ruta, tmp_path / "pu.csv"


def test_marca_la_reexportacion_con_la_razon_y_el_piso_y_no_borra_filas(tmp_path):
    r, pu = _datos(tmp_path)
    con = d.depurar(r["expo"], r["impo"], pu, r["salida"], r["hs4"])
    t = con.execute("SELECT * FROM depurado").df().set_index(["codigo_baci", "hs6"])
    assert len(t) == 6  # nada se borra
    celu = t.loc[(600, "851712")]
    assert celu.reexportacion and celu.reexp_025 and not celu.reexp_100 and celu.razon_m_x == pytest.approx(0.5)  # M = 0,5 X
    assert not t.loc[(600, "120100")].reexportacion  # importa muy poco
    assert not t.loc[(600, "010110")].reexportacion and t.loc[(600, "010110")].razon_m_x == 1.0  # X = 50 < piso de 100: no se marca
    assert not t.loc[(600, "010190")].reexportacion  # sin importaciones del producto
    assert t.loc[(600, "271600")].excluido_energia and not t.loc[(600, "851712")].excluido_energia
    assert pd.isna(t.loc[(999, "010110")].iso3)  # el país sin ISO3 se conserva en la tabla completa


def test_hs4_depurado_suma_solo_lo_no_marcado_y_descarta_paises_sin_iso3(tmp_path):
    r, pu = _datos(tmp_path)
    d.depurar(r["expo"], r["impo"], pu, r["salida"], r["hs4"])
    h = pd.read_parquet(r["hs4"]).set_index("hs4").x
    assert "8517" not in h.index  # el HS6 marcado no entra
    assert h["1201"] == 5000.0 and h["2716"] == 2000.0 and h["0101"] == 450.0  # 010110 (50) + 010190 (400); la energía queda (los modelos la excluyen del RCA)
    assert (pd.read_parquet(r["hs4"]).iso3 == "PRY").all()


def test_umbral_distinto_cambia_la_marca(tmp_path):
    r, pu = _datos(tmp_path)
    con = d.depurar(r["expo"], r["impo"], pu, r["salida"], r["hs4"], theta=0.6)
    assert not con.execute("SELECT reexportacion FROM depurado WHERE hs6 = '851712'").fetchone()[0]


def test_resumenes_cuentan_lo_marcado(tmp_path):
    r, pu = _datos(tmp_path)
    con = d.depurar(r["expo"], r["impo"], pu, r["salida"], r["hs4"])
    g = d.resumen_global(con, 2019)
    assert g["marcado_05"] == 1000.0 and g["energia"] == 2000.0 and g["pares_marcados_05"] == 1
    t, top = d.paraguay(con, 2019, n=2)
    assert t["total"] == 8450.0 and t["energia"] == 2000.0 and t["reexportado_sin_energia"] == 1000.0 and top.hs6.tolist() == ["120100", "271600"]
    p = d.proporcion_por_pais(con, 2019, minimo=1.0)
    assert p.iloc[0].iso3 == "PRY" and p.iloc[0].prop_05 == pytest.approx(1000.0 / 6450.0)
