import pandas as pd
import pytest

from src.limpieza import censo_2011 as c


def _libro(tmp_path):
    """Archivo mínimo con la estructura del Cuadro 1: un departamento con un distrito de dos sectores (uno sin detalle) y otro distrito sin encabezado de sector."""
    n = None
    industria = [["Industria", n, 12, 50, 30, 20, 5, 10, 15], ["101", "Procesamiento de carne", 7, 30, 20, 10, 3, 6, 9], ["10", "Alimentos", 3, 15, 8, 7, 1, 2, 3],
                 [n, "Otras actividades de industria", 2, 5, 2, 3, 1, 2, 3]]
    comercio = [["Comercio", n, 30, 40, 24, 16, 4, 8, 12], ["47", "Comercio al por menor", 20, 25, 15, 10, 2, 5, 8], [n, "Otras actividades de comercio", 10, 15, 9, 6, 2, 3, 4]]
    servicios = [["Servicios", n, 3, 10, 6, 4, 1, 2, 3]]  # sin ramas: reserva estadística
    filas = [[n] * 9, ["Cuadro 1."] + [n] * 8, ["TOTAL", n, 45, 100, 60, 40, 10, 20, 30],
             ["CENTRAL", n, 45, 100, 60, 40, 10, 20, 30], *industria, *comercio, *servicios,
             ["Limpio", n, 15, 60, 38, 22, 6, 12, 18], *industria, *servicios,
             ["Luque", n, 30, 40, 24, 16, 4, 8, 12], *comercio]
    ruta = tmp_path / "cuadro.xlsx"
    pd.DataFrame(filas).to_excel(ruta, header=False, index=False)
    return ruta


def test_sector_de_division_exacto():
    esperado = {"101": "Industria", "08": "Industria", "43": "Industria", "45": "Comercio", "47": "Comercio", "49": "Servicios", "561": "Servicios", "": "Mixto"}
    for codigo, sector in esperado.items():
        assert c.sector_de_division(codigo) == sector


def test_leer_arma_ramas_residuales_y_completa_sectores_sin_detalle(tmp_path):
    ramas, totales, nacional = c.leer(_libro(tmp_path))
    assert nacional["ue"] == 45 and nacional["po"] == 100
    luque = ramas[ramas.distrito == "Luque"]
    assert luque.ue.sum() == 30 and set(luque.ciiu) == {"47", ""}
    limpio = ramas[ramas.distrito == "Limpio"]
    implicito = limpio[limpio.rama.str.contains("implícito")]
    assert implicito.sector.tolist() == ["Servicios"] and implicito.ue.iloc[0] == 3  # sector sin detalle completado con su total
    assert c.verificar(ramas, totales, nacional) == {"ramas_vs_sector": 0, "ramas_vs_bloque": 0, "distritos_vs_departamento": 0, "departamentos_vs_total": 0}


@pytest.mark.skipif(not c.ENTRADA.exists(), reason="falta el archivo del censo en data/raw/censo_2011/")
def test_el_archivo_real_suma_exacto_en_todos_los_niveles():
    ramas, totales, nacional = c.leer()
    assert nacional["ue"] == 224242 and nacional["po"] == pytest.approx(799153)
    assert all(v == 0 for v in c.verificar(ramas, totales, nacional).values())
    assert ramas[ramas.distrito.isna()].ue.sum() == 224242
