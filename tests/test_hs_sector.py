import pandas as pd
import pytest

from src.puentes.hs_sector import (
    ARNES,
    ENERGIA,
    SALIDA,
    componer,
    con_identidad,
    extender_por_prefijo,
    nivel_confianza,
)
from src.puentes.taxonomia_tape import SECTORES


def _t(filas):
    return pd.DataFrame(filas, columns=["source", "target", "weight"])


def test_componer_multiplica_pesos_y_suma_caminos():
    a = _t([("A", "x", 0.5), ("A", "y", 0.5)])
    b = _t([("x", "Z", 1.0), ("y", "Z", 0.4), ("y", "W", 0.6)])
    r = componer(a, b).set_index(["source", "target"]).weight
    assert r[("A", "Z")] == pytest.approx(0.5 + 0.2) and r[("A", "W")] == pytest.approx(0.3)


def test_con_identidad_agrega_los_codigos_que_no_cambian():
    t = con_identidad(_t([("A", "B", 1.0)]), {"A", "C"})
    assert set(zip(t.source, t.target, strict=True)) == {("A", "B"), ("C", "C")}


def test_extender_por_prefijo_usa_a_los_hermanos_de_cuatro_digitos():
    cpc = _t([("040510", "22000", 1.0), ("040520", "22000", 0.5), ("040520", "22100", 0.5)])
    e = extender_por_prefijo({"040500"}, cpc).set_index("target").weight
    assert e["22000"] == pytest.approx(0.75) and e["22100"] == pytest.approx(0.25)  # promedio de 2 hermanos


def test_nivel_de_confianza():
    assert nivel_confianza(1.0, 1.0, "cadena") == "alta"
    assert nivel_confianza(1.0, 1.0, "regla_residuos") == "media"  # alta exige vía oficial
    assert nivel_confianza(0.7, 1.0, "cadena") == "media"
    assert nivel_confianza(0.5, 1.0, "cadena") == "baja"
    assert nivel_confianza(1.0, 0.0, "cadena") == "sin_mapeo"


pytestmark_real = pytest.mark.skipif(not SALIDA.exists(), reason="falta data/clean/puente_hs92_sector.csv")


@pytest.fixture(scope="module")
def t():
    return pd.read_csv(SALIDA, dtype={"hs92": str, "sector_id": str}, keep_default_na=False,
                       na_values=[""]).fillna({"sector_id": "", "marca": "", "ciiu4": ""})


@pytestmark_real
def test_pesos_suman_uno_y_los_sectores_existen(t):
    con = t[t.sector_id != ""]
    assert ((con.groupby("hs92").peso.sum() - 1).abs() < 1e-6).all()
    assert set(con.sector_id) <= {s.id for s in SECTORES}


@pytestmark_real
def test_solo_los_codigos_no_especificados_quedan_sin_mapeo(t):
    assert set(t[t.confianza == "sin_mapeo"].hs92) == {"999999", "9999AA"}


@pytestmark_real
def test_la_mayor_parte_del_valor_es_de_confianza_alta(t):
    c = t.drop_duplicates("hs92")
    v = c.groupby("confianza").valor_mundial.sum() / c.valor_mundial.sum()
    assert v["alta"] > 0.8


@pytestmark_real
def test_marcas_especiales(t):
    m = t.drop_duplicates("hs92").set_index("hs92").marca
    assert m[ENERGIA] == "excluir_energia_binacional" and m[ARNES] == "arnes"
    nombre = {s.id: s.nombre for s in SECTORES}
    assert "Autopartes" in nombre[t[t.hs92 == ARNES].sector_id.iloc[0]]


@pytestmark_real
def test_principales_exportaciones_de_paraguay(t):
    nombre = {s.id: s.nombre for s in SECTORES}
    top = t.sort_values("peso", ascending=False).drop_duplicates("hs92").set_index("hs92").sector_id
    assert nombre[top["120100"]].startswith("Cultivos anuales")  # soja
    assert nombre[top["020130"]].startswith("Frigoríficos")  # carne bovina
    assert nombre[top["150710"]].startswith("Aceites")  # aceite de soja
    assert nombre[top["100630"]].startswith("Molinería")  # arroz
