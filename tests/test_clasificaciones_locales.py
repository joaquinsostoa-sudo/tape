import pytest

from src.puentes.clasificaciones_locales import (
    ANIDAN,
    ATOMOS,
    CLASIFICACIONES,
    CNAEP_SOLAPE_PERMITIDO,
    DIV10,
    atomo_a_categoria,
    expandir,
    tabla_atomos,
)


def test_expandir_rangos_y_atomos():
    assert expandir("11-12,45,014") == ["11", "12", "45", "014"]
    assert expandir("*") == []


def test_la_division_10_se_expande_en_sus_subatomos():
    assert expandir("10") == DIV10
    assert expandir("10-11") == DIV10 + ["11"]


def test_expandir_rechaza_atomo_invalido():
    with pytest.raises(ValueError):
        expandir("01")  # la 01 se declara como 01x o 014


@pytest.mark.parametrize("clasif", ANIDAN)
def test_cada_atomo_cae_en_a_lo_sumo_una_categoria(clasif):
    mapa = atomo_a_categoria(CLASIFICACIONES[clasif])
    solapados = {a: cs for a, cs in mapa.items() if len(cs) > 1}
    assert not solapados, solapados


def test_cnaep33_tiene_33_actividades_y_solo_solapa_educacion_y_salud():
    assert len(CLASIFICACIONES["cnaep33"]) == 33
    mapa = atomo_a_categoria(CLASIFICACIONES["cnaep33"])
    assert {a for a, cs in mapa.items() if len(cs) > 1} == CNAEP_SOLAPE_PERMITIDO
    sin_grupo = [a for a, cs in mapa.items() if not cs and a not in ("99",)]
    assert not sin_grupo, sin_grupo


def test_mic_mapa_cubre_los_73_subsectores_y_las_industrias_suman_17080():
    import pandas as pd

    from src.puentes.clasificaciones_locales import _MIC, MIC_CSV

    df = pd.read_csv(MIC_CSV)
    assert len(df) == 73 and set(df["subsector"]) == set(_MIC)
    assert df["n_industrias"].sum() == 17080  # coincide con los totales por zona del visor


def test_manufactura_es_un_solo_grupo_en_ephc_y_se_parte_en_nueve_en_mip():
    df = tabla_atomos().set_index("atomo")
    manu = [a for a in ATOMOS if a[:2].isdigit() and 10 <= int(a[:2]) <= 33]
    assert df.loc[manu, "ephc"].nunique() == 1
    assert df.loc[manu, "mip"].nunique() == 9
