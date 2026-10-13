import pandas as pd
import pytest

from src.puentes import paises_baci as p


def _codigos() -> pd.DataFrame:
    return pd.DataFrame({
        "country_code": [600, 56, 58, 999],
        "country_name": ["Paraguay", "Belgium", "Belgium-Luxembourg (...1998)", "Sin ISO"],
        "country_iso2": ["PY", "BE", "BE", None],
        "country_iso3": ["PRY", "BEL", "BEL", None],
    })


def test_paraguay_es_600_pry_y_se_descarta_sin_iso3():
    out = p.construir(_codigos())
    assert out.set_index("codigo_baci").loc[600, "iso3"] == "PRY"
    assert 999 not in set(out.codigo_baci)


def test_dos_codigos_para_un_iso3_marca_el_historico():
    out = p.construir(_codigos()).set_index("codigo_baci")
    assert out.loc[56, "iso3"] == out.loc[58, "iso3"] == "BEL"
    assert not out.loc[56, "historico"] and out.loc[58, "historico"]


def test_codigo_repetido_falla():
    d = pd.concat([_codigos(), _codigos().iloc[[0]]])
    with pytest.raises(ValueError):
        p.construir(d)


def test_datos_reales_si_estan():
    if not (p.ZIP.exists() or p.CSV.exists()):
        pytest.skip("falta BACI")
    out = p.construir(p.leer_codigos()).set_index("codigo_baci")
    assert out.loc[600, "iso3"] == "PRY"
