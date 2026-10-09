import pytest

from src.limpieza import mic_ciudades


@pytest.fixture(scope="module")
def df():
    try:
        return mic_ciudades.cargar()
    except FileNotFoundError:
        pytest.skip("faltan los CSV de data/raw/mic_mapa")


def test_totales_del_visor(df):
    assert len(df) == 263
    assert df.poblacion_2022.sum() == 6_109_903
    assert df.pea.sum() == 3_331_360
    assert df.hombres.sum() == 3_057_674 and df.mujeres.sum() == 3_052_229


def test_hombres_mas_mujeres_es_la_poblacion(df):
    assert (df.hombres + df.mujeres == df.poblacion_2022).all()


def test_departamentos_con_codigo_ine(df):
    assert sorted(df.dep_codigo.unique()) == list(range(18))
    assert df.loc[df.ciudad == "ASUNCION", "dep_codigo"].item() == 0
    assert df.loc[df.ciudad == "ENCARNACION", "dep_codigo"].item() == 7


def test_dos_bella_vista_son_distintas(df):
    bv = df[df.ciudad == "BELLA VISTA"]
    assert sorted(bv.dep_codigo) == [7, 13]


def test_unica_ciudad_sin_coordenadas(df):
    assert df.loc[df.lat.isna(), "ciudad"].tolist() == ["MARIA ANTONIA"]
    con = df.dropna(subset=["lat"])
    assert con.lat.between(-27.7, -19.2).all() and con.lon.between(-62.7, -54.2).all()


def test_distancias_a_si_mismas_son_cero(df):
    assert df.loc[df.ciudad == "ASUNCION", "dist_asu_km"].item() == 0
    assert df.loc[df.ciudad == "CIUDAD DEL ESTE", "dist_cde_km"].item() == 0
    assert df.loc[df.ciudad == "ENCARNACION", "dist_enc_km"].item() == 0
