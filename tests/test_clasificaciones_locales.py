import pytest

from src.puentes.clasificaciones_locales import (
    ANIDAN, ATOMOS, CLASIFICACIONES, atomo_a_categoria, expandir, tabla_atomos,
)


def test_expandir_rangos_y_atomos():
    assert expandir("10-12,45,014") == ["10", "11", "12", "45", "014"]
    assert expandir("*") == []


def test_expandir_rechaza_atomo_invalido():
    with pytest.raises(ValueError):
        expandir("01")  # la 01 se declara como 01x o 014


@pytest.mark.parametrize("clasif", ANIDAN)
def test_cada_atomo_cae_en_a_lo_sumo_una_categoria(clasif):
    mapa = atomo_a_categoria(CLASIFICACIONES[clasif])
    solapados = {a: cs for a, cs in mapa.items() if len(cs) > 1}
    assert not solapados, solapados


def test_manufactura_es_un_solo_grupo_en_ephc_y_se_parte_en_nueve_en_mip():
    df = tabla_atomos().set_index("atomo")
    manu = [a for a in ATOMOS if len(a) == 2 and 10 <= int(a) <= 33]
    assert df.loc[manu, "ephc"].nunique() == 1
    assert df.loc[manu, "mip"].nunique() == 9
