import pandas as pd
import pytest

from src.limpieza.cnaep_ciiu import SALIDA, asignar_ciiu, repartir_digitos
from src.puentes.cnaep_sector import SALIDA as PUENTE


def test_repartir_digitos_en_corridas_crecientes():
    assert repartir_digitos([1, 2, 9, 0, 1], 2) == [[1, 2, 9], [0, 1]]
    assert repartir_digitos([0, 0, 1], 2) == [[0], [0, 1]]
    with pytest.raises(ValueError):
        repartir_digitos([1, 2, 3], 2)


def test_asignar_ciiu_uno_a_varios():
    # CNAEP 5911 (y=473) -> CIIU 5911 y 5912 (y=456, 490), centradas frente a la fila; luego 1 a 1
    assert asignar_ciiu([473, 524, 557], [456, 490, 524, 557]) == [[0, 1], [2], [3]]


def test_asignar_ciiu_igual_cantidad_es_uno_a_uno():
    assert asignar_ciiu([10, 20, 30], [12, 25, 28]) == [[0], [1], [2]]


@pytest.mark.skipif(not SALIDA.exists(), reason="falta data/clean/cnaep1_ciiu4.csv")
def test_tabla_cnaep_ciiu_tiene_604_codigos_y_clases_validas():
    d = pd.read_csv(SALIDA, dtype=str)
    assert d.cnaep.nunique() == 604
    assert d.ciiu4.str.fullmatch(r"\d{4}").all()
    assert not d.duplicated(["cnaep", "ciiu4"]).any()
    assert (d.cnaep.str[:2] == d.ciiu4.str[:2]).mean() > 0.98  # casi todo dentro de la misma división


@pytest.mark.skipif(not PUENTE.exists(), reason="falta data/clean/puente_cnaep_sector.csv")
def test_cada_codigo_cnaep_cae_en_un_solo_sector_tape():
    p = pd.read_csv(PUENTE, dtype=str).fillna("")
    con_sector = p[p.sector_id != ""]
    assert con_sector.groupby("cnaep").sector_id.nunique().max() == 1
    assert set(p[p.sector_id == ""].cnaep) == {"99000"}
    assert p.confianza.isin(["alta", "media", "sin_sector"]).all()
