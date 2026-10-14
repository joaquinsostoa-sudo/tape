import zipfile

import pandas as pd
import pytest

from src.limpieza import baci

CSV = """t,i,j,k,v,q
2000,600,32,10110,10.0,2.0
2000,600,76,10110,5.0,NA
2000,600,76,120100,100.0,50.0
2000,32,600,120100,40.0,10.0
2000,76,600,10110,15.0,4.0
2000,76,32,271600,60.0,3.0
"""


def _csv(tmp_path):
    ruta = tmp_path / "BACI_HS92_Y2000_V202601.csv"
    ruta.write_text(CSV)
    return ruta


def test_agregar_csv_suma_por_pais_y_producto_y_completa_el_hs6(tmp_path):
    expo, impo = baci.agregar_csv(_csv(tmp_path))
    e = expo.set_index(["codigo_baci", "hs6"])
    assert e.loc[(600, "010110"), "valor_miles_usd"] == 15.0  # suma de dos destinos; el cero a la izquierda se repone
    assert e.loc[(600, "010110"), "toneladas"] == 2.0  # el «NA» no suma ni rompe
    assert e.loc[(600, "120100"), "valor_miles_usd"] == 100.0
    i = impo.set_index(["codigo_baci", "hs6"])
    assert i.loc[(76, "010110"), "valor_miles_usd"] == 5.0 and i.loc[(600, "120100"), "valor_miles_usd"] == 40.0


def test_totales_de_exportacion_e_importacion_coinciden_y_no_hay_problemas(tmp_path):
    expo, impo = baci.agregar_csv(_csv(tmp_path))
    assert baci.verificar(expo, impo, {600, 32, 76}) == {"valores_negativos": 0, "anios_con_totales_distintos": 0, "paises_fuera_del_catalogo": 0, "hs6_mal_formado": 0, "claves_duplicadas": 0}
    assert baci.verificar(expo, impo, {600, 32})["paises_fuera_del_catalogo"] > 0


def test_verificar_detecta_negativos_y_totales_distintos(tmp_path):
    expo, impo = baci.agregar_csv(_csv(tmp_path))
    impo.loc[0, "valor_miles_usd"] = -1.0
    v = baci.verificar(expo, impo, {600, 32, 76})
    assert v["valores_negativos"] == 1 and v["anios_con_totales_distintos"] == 1


def test_miembros_por_anio_ignora_lo_que_no_es_anual():
    nombres = ["BACI_HS92_Y2001_V202601.csv", "BACI_HS92_Y1995_V202601.csv", "country_codes_V202601.csv", "Readme.txt"]
    assert list(baci.miembros_por_anio(nombres)) == [1995, 2001]


def test_procesar_zip_extrae_un_anio_y_borra_la_carpeta_temporal(tmp_path):
    z = tmp_path / "b.zip"
    with zipfile.ZipFile(z, "w") as f:
        f.writestr("BACI_HS92_Y2000_V202601.csv", CSV)
        f.writestr("country_codes_V202601.csv", "country_code\n600\n")
    tmp = tmp_path / "tmp"
    expo, _ = baci.procesar_zip(z, tmp)
    assert expo.anio.unique().tolist() == [2000] and len(expo) == 5 and not tmp.exists()


def test_hs4_agrega_a_cuatro_digitos_y_descarta_codigos_sin_iso3():
    expo = pd.DataFrame({"anio": [2000] * 3, "codigo_baci": [600, 600, 999], "hs6": ["010110", "010190", "010110"], "valor_miles_usd": [1.0, 2.0, 9.0], "toneladas": [0.0] * 3})
    puente = pd.DataFrame({"codigo_baci": [600], "iso3": ["PRY"]})
    h = baci.exportaciones_hs4(expo, puente)
    assert h.to_dict("records") == [{"anio": 2000, "iso3": "PRY", "hs4": "0101", "x": 3.0}]


def test_comparar_cuenta_diferencias_y_claves_sueltas():
    a = pd.DataFrame({"anio": [2000, 2000, 2000], "iso3": ["PRY"] * 3, "hs4": ["0101", "0102", "0103"], "x": [1.0, 2.0, 3.0]})
    b = pd.DataFrame({"anio": [2000, 2000, 2000], "iso3": ["PRY"] * 3, "hs4": ["0101", "0102", "0104"], "x": [1.0, 2.5, 4.0]})
    r = baci.comparar(a, b)
    assert r["solo_nuevo"] == 1 and r["solo_viejo"] == 1 and r["filas_con_dif_mayor_1e6"] == 1 and r["dif_relativa_max"] == pytest.approx(0.2)
