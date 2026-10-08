import openpyxl
import pandas as pd
import pytest

from src.limpieza.bcp_cra import EXCEL, cargar

pytestmark = pytest.mark.skipif(not EXCEL.exists(), reason="falta el anexo CRA en data/raw (no versionado)")


@pytest.fixture(scope="module")
def cra() -> pd.DataFrame:
    return cargar()


def test_18_departamentos_y_serie_2021_2024(cra):
    assert cra.depto_codigo.nunique() == 18
    assert (cra.anio.min(), cra.anio.max()) == (2021, 2024)
    assert set(cra[cra.preliminar].anio) == {2023, 2024}


def test_las_seis_ramas_mas_impuestos_suman_el_pib(cra):
    n = cra[(cra.medida == "nominal") & (cra.anio == 2022)]
    p = n.pivot_table(index="depto_codigo", columns="rama", values="valor")
    ramas = ["agricultura", "ganaderia_forestal_pesca_mineria", "manufactura", "electricidad_agua",
             "construccion", "servicios"]
    assert p[ramas].sum(axis=1).sub(p["valor_agregado_total"]).abs().max() < 1e-3 * p["pib"].max()
    assert (p["valor_agregado_total"] + p["impuestos_productos"]).sub(p["pib"]).abs().max() < 1e-3 * p["pib"].max()


def test_el_pib_departamental_coincide_con_la_hoja_de_totales(cra):
    wb = openpyxl.load_workbook(EXCEL, data_only=True)
    ws = wb["PIB_corriente"]
    # año 2022; el código de Presidente Hayes viene como número (15) y no como texto ("15") en el Excel
    total_hoja = {f"{int(r[0]):02d}": r[4] for r in ws.iter_rows(min_row=1, values_only=True)
                  if str(r[0]).isdigit() and isinstance(r[4], (int, float))}
    assert len(total_hoja) == 18  # la comparación no puede quedar vacía
    n = cra[(cra.medida == "nominal") & (cra.rama == "pib") & (cra.anio == 2022)].set_index("depto_codigo").valor
    for cod, valor in total_hoja.items():
        assert n[cod] == pytest.approx(valor, rel=1e-6)


def test_el_deflactor_es_nominal_sobre_real_por_cien(cra):
    d = cra[(cra.rama == "pib") & cra.medida.isin(["nominal", "real", "deflactor"])].pivot_table(
        index=["depto_codigo", "anio"], columns="medida", values="valor")
    assert (d.nominal / d.real * 100).sub(d.deflactor).abs().max() < 1e-6
