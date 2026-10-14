import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import box

from src.puentes import distritos as d


def test_normalizar_y_departamento():
    assert d.normalizar("  San Lázaro  (Ex-X) ") == "SAN LAZARO EX X"
    assert d.departamento("CAPITAL") == "ASUNCION" and d.departamento("Pte Hayes") == "PRESIDENTE HAYES" and d.departamento("Itapúa") == "ITAPUA"


def test_llave_ignora_titulos_ex_y_grafias_guaranies():
    assert d.llave("La Victoria (Ex Puerto Casado)") == d.llave("La Victoria")
    assert d.llave("Yby Yaú") == d.llave("Yvy Ya'u")
    assert d.llave("Ypejhu") == d.llave("Ype Jhu")


def test_similitud_nombres_iguales_variantes_y_contenidos():
    assert d.similitud("Luque", "LUQUE") == 1.0
    assert d.similitud("Guayaibí", "Guajayvi") > 0.85
    assert d.similitud("San Pedro", "San Pedro del Ykuamandiyú") == pytest.approx(0.85, abs=0.2) and d.similitud("San Pedro", "San Pedro del Ykuamandiyú") >= 0.85
    assert d.similitud("Luque", "Capiatá") < 0.5


def test_emparejar_es_uno_a_uno_y_descarta_lo_distinto():
    pares = d.emparejar(["Luque", "San Lorenzo", "Nuevo Lugar"], ["San Lorenzo", "Luque"])
    assert {(i, j) for i, j, _ in pares} == {(0, 1), (1, 0)}  # «Nuevo Lugar» queda sin pareja
    assert d.emparejar([], ["A"]) == []


def test_confianza_por_umbral():
    assert [d.confianza(s) for s in (1.0, 0.9, 0.8, 0.7, 0.6)] == ["alta", "alta", "media", "media", "baja"]


def test_padre_por_vecindad_elige_la_frontera_mas_larga():
    pol = gpd.GeoDataFrame({"geometry": [box(0, 0, 1000, 1000), box(1000, 0, 2000, 1000), box(0, 1000, 1000, 1200), box(1000, 1000, 1200, 1100), box(5000, 5000, 5100, 5100)]}, crs="EPSG:32721")
    # el polígono 0 comparte 1000 m con el 1 y 1000 m de arriba con el 2 (y nada con el 3); el 3 toca solo al 1 en 100 m
    mejor, largo = d.padre_por_vecindad(pol, 3, [0, 1, 2])
    assert mejor == 1 and 50 < largo < 250  # medida aproximada: el buffer de 50 m infla un poco el largo
    assert d.padre_por_vecindad(pol, 4, [0, 1, 2]) is None  # un polígono lejano no tiene vecinos


def test_construir_2012_une_los_nombres_y_asigna_padre_y_fragmentos():
    c11 = pd.DataFrame({"departamento": ["CENTRAL", "CENTRAL"], "distrito": ["Luque", "Limpio"]})
    pol = gpd.GeoDataFrame({"departamento": ["Central"] * 4, "distrito": ["Luque", "Limpio", "Nuevo", "Esquirla"], "id": list("abcd"), "km2": [10.0, 10.0, 5.0, 0.1],
                            "geometry": [box(0, 0, 1000, 1000), box(1000, 0, 2000, 1000), box(2000, 0, 2500, 1000), box(1000, 1000, 1010, 1010)]}, crs="EPSG:32721")
    r = d.construir_2012(c11, pol).set_index("distrito_2012")
    assert r.loc["Luque", "unidad_2011"] == "Luque" and r.loc["Luque", "relacion"] == "igual"
    assert r.loc["Nuevo", "unidad_2011"] == "Limpio" and r.loc["Nuevo", "relacion"] == "nuevo_desde_padre" and r.loc["Nuevo", "confianza"] == "baja"
    assert r.loc["Esquirla", "relacion"] == "fragmento" and r.loc["Esquirla", "unidad_2011"] == "Limpio"


@pytest.mark.skipif(not d.SALIDA_2012.exists(), reason="falta correr src.puentes.distritos")
def test_cada_distrito_del_censo_tiene_exactamente_un_poligono_igual_y_todo_polígono_una_unidad():
    p = pd.read_csv(d.SALIDA_2012, keep_default_na=False)
    c = pd.read_csv(d.CENSO_2011, keep_default_na=False)[["departamento", "distrito"]].drop_duplicates()
    iguales = p[p.relacion == "igual"].groupby(["departamento", "unidad_2011"]).size()
    assert len(iguales) == len(c) and (iguales == 1).all()
    assert (p.unidad_2011 != "").all()


def _ref():
    return pd.DataFrame({"departamento": ["CANINDEYU"] * 4, "nombre": ["Curuguaty", "Corpus Christi", "Ybyrarobana", "Nueva Esperanza"],
                         "unidad_2011": ["Curuguaty", "Corpus Christi", "Corpus Christi", "Nueva Esperanza"]})


def test_aplicar_leyes_reparte_en_partes_iguales_y_resuelve_padres_que_son_nuevos():
    df = pd.DataFrame({"departamento": ["CANINDEYU"], "distrito_2022": ["LAUREL"], "unidad_2011": ["Nueva Esperanza"], "relacion": ["nuevo_desde_padre"], "similitud": [0.0],
                       "confianza": ["baja"], "nota": ["x"]})
    r = d.aplicar_leyes(df, _ref(), "distrito_2022")
    # Laurel: Ybyrarobaná (nuevo, cuyo padre inferido es Corpus Christi) y Nueva Esperanza
    assert sorted(r.unidad_2011) == ["Corpus Christi", "Nueva Esperanza"] and r.peso.sum() == pytest.approx(1.0) and set(r.fuente_padre) == {"ley"} and set(r.confianza) == {"media"}


def test_aplicar_leyes_deja_igual_lo_que_no_esta_en_la_lista_y_los_iguales():
    df = pd.DataFrame({"departamento": ["CANINDEYU", "CANINDEYU"], "distrito_2022": ["Curuguaty", "Yasy Kañy"], "unidad_2011": ["Curuguaty", "Yasy Cañy"], "relacion": ["igual", "nuevo_desde_padre"],
                       "similitud": [1.0, 0.0], "confianza": ["alta", "baja"], "nota": ["", "inferido"]})
    r = d.aplicar_leyes(df, _ref(), "distrito_2022")
    assert len(r) == 2 and r.peso.tolist() == [1.0, 1.0] and r.fuente_padre.tolist() == ["nombre", "inferido"] and r.confianza.tolist() == ["alta", "baja"]


def test_unidad_de_falla_si_el_padre_de_la_ley_no_existe():
    with pytest.raises(ValueError, match="no se encontró"):
        d._unidad_de("Inexistente", "CANINDEYU", _ref())


def test_las_listas_de_leyes_no_se_pisan_y_traen_ley_y_padres():
    from src.puentes.distritos_leyes import CONFIRMADOS, CORREGIDOS

    assert not set(CORREGIDOS) & set(CONFIRMADOS) and len(CORREGIDOS) == 9 and len(CONFIRMADOS) == 11
    assert all(padres and ley for _, padres, ley in {**CORREGIDOS, **CONFIRMADOS}.values())


@pytest.mark.skipif(not d.SALIDA_2022.exists(), reason="falta correr src.puentes.distritos")
def test_los_pesos_suman_uno_por_distrito_y_los_de_ley_traen_la_ley():
    q = pd.read_csv(d.SALIDA_2022, keep_default_na=False)
    assert ((q.groupby(["departamento", "distrito_2022"]).peso.sum() - 1).abs() < 1e-9).all()
    assert (q[q.fuente_padre == "ley"].ley != "").all() and (q[q.fuente_padre == "ley"].padres_legales != "").all()
