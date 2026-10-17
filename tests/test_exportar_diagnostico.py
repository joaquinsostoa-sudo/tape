import pandas as pd

from src.herramienta import exportar_diagnostico as ex


def test_normalizar_quita_tildes_signos_y_mayusculas():
    assert ex.normalizar("Ñeembucú") == "neembucu" and ex.normalizar("Dr. Raúl Peña") == ex.normalizar("DR.RAUL PENA")


def _f(situacion, n_brechas=0, n_cerca=0, apto=True):
    return pd.Series({"situacion": situacion, "n_brechas": n_brechas, "n_cerca": n_cerca, "apto_recursos": apto})


def test_clase_del_mapa_sigue_el_orden_declarado():
    assert ex.clase_celda(_f("oportunidad no realizada")) == 0
    assert ex.clase_celda(_f("ya se produce", n_cerca=1)) == 1
    assert ex.clase_celda(_f("no se produce, con brechas", n_brechas=1)) == 2
    assert ex.clase_celda(_f("no se produce, con brechas", n_brechas=3)) == 3
    assert ex.clase_celda(_f("no apto por recursos", n_brechas=1, apto=False)) == 4
    assert ex.clase_celda(_f("datos incompletos")) == 5 and ex.clase_celda(_f("sin referencia")) == 6


def test_tercios_de_complejidad():
    t = ex.tercio(pd.Series([5.0, 40.0, 90.0, float("nan")]))
    assert list(t) == ["simple", "intermedia", "compleja", ""]


def test_orientar_deja_el_anillo_exterior_en_sentido_horario():
    from shapely.geometry import Polygon
    antihorario = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    assert antihorario.exterior.is_ccw
    assert not ex.orientar(antihorario).exterior.is_ccw
