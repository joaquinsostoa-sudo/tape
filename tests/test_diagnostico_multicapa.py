import numpy as np
import pandas as pd

from src.puentes import diagnostico_multicapa as dm


def test_estado_separa_sin_brecha_cerca_del_umbral_y_con_brecha():
    e = dm.estado(pd.Series([5.0, 0.0, -3.0, -10.0, -10.1, np.nan]))
    assert list(e) == [dm.SIN, dm.SIN, dm.CERCA, dm.CERCA, dm.CON, ""]
    assert dm.estado(pd.Series([-7.0]), banda=5.0).iloc[0] == dm.CON                  # la banda es un parámetro de sensibilidad


def test_umbral_de_referencia_con_minimo_de_productores_y_confianza():
    idx = pd.Series(np.arange(100.0))
    u, n, conf = dm.umbral_referencia(idx, pd.Series([True] * 10 + [False] * 90))      # productores con 0..9: percentil 10 = 0,9
    assert n == 10 and conf == "alta" and abs(u - 0.9) < 1e-9
    u, n, conf = dm.umbral_referencia(idx, pd.Series([True] * 5 + [False] * 95))
    assert n == 5 and conf == "baja" and not np.isnan(u)
    u, n, conf = dm.umbral_referencia(idx, pd.Series([True] * 4 + [False] * 96))       # menos de 5: sin referencia
    assert np.isnan(u) and n == 4 and conf == ""
    u, _, _ = dm.umbral_referencia(idx, pd.Series([True] * 10 + [False] * 90), "mediana")
    assert abs(u - 49.5) < 1e-9                                                         # sensibilidad: mediana de todos
    conn = idx.copy(); conn.iloc[:10] = np.nan                                           # los productores sin dato no cuentan
    assert dm.umbral_referencia(conn, pd.Series([True] * 10 + [False] * 90))[1] == 0


def _e(*v):
    return pd.Series(list(v))


def test_nivel_de_politica_segun_el_tipo_y_el_tamano_de_la_brecha():
    est = {"base": _e(dm.SIN, dm.CON, dm.CON, dm.SIN, dm.SIN, dm.CON), "formacion": _e(dm.SIN, dm.SIN, dm.CON, dm.SIN, dm.SIN, dm.SIN),
           "energia": _e(dm.SIN, dm.SIN, dm.SIN, dm.CON, dm.SIN, dm.SIN), "recursos": _e(dm.SIN, dm.SIN, dm.SIN, dm.SIN, dm.CON, dm.SIN)}
    brec = {"base": _e(5.0, -15.0, -12.0, 5.0, 5.0, -30.0), "formacion": _e(5.0, 1.0, -11.0, 1.0, 1.0, 1.0), "energia": _e(1.0, 1.0, 1.0, -20.0, 1.0, 1.0), "recursos": _e(1.0, 1.0, 1.0, 1.0, -20.0, 1.0)}
    r = dm.nivel_politica(est, brec)
    assert list(r["nivel"]) == [0, 1, 2, 3, 0, 2]                    # sin brechas; una de base de 15; dos; infraestructura; solo recursos; una de base de 30 (> 20)
    assert list(r["apto_recursos"]) == [True, True, True, True, False, True]


def test_infraestructura_conjunta_y_nivel_3_aunque_haya_brecha_de_formacion():
    est = {"base": _e(dm.CON), "energia": _e(dm.CON), "logistica": _e(dm.CON)}
    brec = {"base": _e(-15.0), "energia": _e(-15.0), "logistica": _e(-15.0)}
    r = dm.nivel_politica(est, brec)
    assert r["nivel"].iloc[0] == 3 and bool(r["infraestructura_conjunta"].iloc[0])


def test_pci_y_cog_del_sector_pesan_por_peso_y_valor_mundial_y_omiten_sin_dato():
    pesos = pd.DataFrame({"hs4": ["a", "b", "c"], "sector_id": ["S1", "S1", "S2"], "w": [1.0, 0.5, 1.0]})
    valor = pd.Series({"a": 10.0, "b": 40.0, "c": 5.0})
    op = pd.DataFrame({"hs4": ["a", "b", "c"], "pci": [1.0, 2.0, np.nan], "cog": [0.0, 1.0, 0.5]})
    r = dm.pci_cog_sector(op, pesos, valor).set_index("sector_id")
    assert abs(r.loc["S1", "pci"] - (1.0 * 10 + 2.0 * 20) / 30) < 1e-12              # pesos 1*10 y 0,5*40
    assert np.isnan(r.loc["S2", "pci"]) and r.loc["S2", "cog"] == 0.5               # sin PCI no se imputa


def test_escalon_resta_la_mediana_de_los_sectores_que_el_distrito_produce():
    pct = pd.Series({"A": 10.0, "B": 50.0, "C": 90.0})
    produce = pd.DataFrame({"A": [True, False], "B": [True, False], "C": [False, False]}, index=["d1", "d2"])
    e = dm.escalon(pct, produce)
    assert e.loc["d1", "C"] == 60.0 and e.loc["d1", "A"] == -20.0                    # mediana de 10 y 50 = 30
    assert e.loc["d2"].isna().all()                                                  # el distrito sin sectores con PCI queda sin dato
    assert list(dm.etiqueta_escalon(pd.Series([60.0, 5.0, -5.0, -20.0, np.nan]))) == ["más complejo", "similar", "similar", "menos complejo", ""]
