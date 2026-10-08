import pytest

from src.puentes.taxonomia_tape import (
    EXCLUIDAS,
    ISIC4_CLASES,
    SECTORES,
    atomo_de,
    clases_ciiu4,
    cruces,
    sectores_de_clase,
)


def test_atomo_de_prefijos():
    assert atomo_de("0141") == "014" and atomo_de("011") == "01x"
    assert atomo_de("1072") == "1072" and atomo_de("1073") == "10o" and atomo_de("101") == "101"


def test_ids_unicos_y_cantidad_razonable():
    ids = [s.id for s in SECTORES]
    assert len(ids) == len(set(ids)) and 40 <= len(ids) <= 70


def test_ningun_sector_cruza_grupos_de_las_clasificaciones_locales():
    assert not {s.id: c for s in SECTORES if (c := cruces(s))}


@pytest.mark.skipif(not ISIC4_CLASES.exists(), reason="falta data/raw/concordancias (no versionado)")
def test_cada_clase_ciiu4_cae_en_exactamente_un_sector():
    clases = [c for c in clases_ciiu4() if c[:2] not in EXCLUIDAS]
    sin = [c for c in clases if len(sectores_de_clase(c)) == 0]
    varios = {c: sectores_de_clase(c) for c in clases if len(sectores_de_clase(c)) > 1}
    assert not sin, f"clases sin sector: {sin}"
    assert not varios, f"clases en varios sectores: {varios}"


@pytest.mark.skipif(not ISIC4_CLASES.exists(), reason="falta data/raw/concordancias (no versionado)")
def test_todo_prefijo_corresponde_a_alguna_clase_real():
    clases = clases_ciiu4()
    malos = [(s.id, p) for s in SECTORES for p in s.ciiu4.split(",") if not any(c.startswith(p) for c in clases)]
    # La tabla CPC<->CIIU de la ONU solo lista clases con productos CPC: faltan 0150 (mixta),
    # el comercio (46, 47) y 98 (hogares), que sí existen en la CIIU Rev.4.
    assert {p for _, p in malos} <= {"015", "46", "47", "98"}, malos
