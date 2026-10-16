import numpy as np
import pandas as pd

from src.puentes import ejemplo_ch as ej


def test_si_la_industria_exige_formacion_el_puntaje_es_el_minimo_de_las_dos_partes():
    base = pd.Series([80.0, 40.0, 60.0])
    espec = pd.Series([60.0, 20.0, 100.0])
    assert list(ej.puntaje(base, espec, exige=True)) == [60.0, 20.0, 60.0]               # el eslabón más débil (D31)
    assert list(ej.puntaje(base, espec, exige=True, metodo="promedio")) == [70.0, 30.0, 80.0]   # solo como sensibilidad


def test_si_no_exige_solo_cuenta_la_base_y_la_formacion_no_resta():
    base = pd.Series([80.0, 40.0])
    espec = pd.Series([0.0, 100.0])
    assert list(ej.puntaje(base, espec, exige=False)) == [80.0, 40.0]


def test_si_falta_una_parte_y_la_industria_exige_el_puntaje_no_se_inventa():
    p = ej.puntaje(pd.Series([50.0, np.nan]), pd.Series([np.nan, 50.0]), exige=True)
    assert p.isna().all()


def test_el_limitante_es_la_parte_con_menor_percentil():
    assert list(ej.limitante(pd.Series([70.0, 30.0]), pd.Series([40.0, 90.0]))) == ["formación específica", "base"]


def test_control_contra_la_poblacion_cuenta_los_distritos_con_industria_en_el_20_por_ciento_superior():
    n = 10
    d = pd.DataFrame({"poblacion": np.arange(1, n + 1) * 100, "p_base": np.arange(n) * 10.0, "p_especifico": np.arange(n) * 10.0,
                      "puntaje": np.arange(n) * 10.0, "industrias_hoy": [0, 0, 0, 0, 0, 0, 0, 0, 1, 2]})
    c = ej.control_vs_poblacion(d)
    assert c["distritos_con_industria"] == 2 and c["en_top20_puntaje"] == 2 and c["en_top20_poblacion"] == 2


def _fichas():
    """Diez distritos: los tres últimos tienen la industria hoy (productores)."""
    return pd.DataFrame({
        "dep": ["A"] * 10, "clave": [f"d{i}" for i in range(10)], "poblacion": [1000] * 10,
        "p_base": [95.0, 90.0, 85.0, 20.0, 70.0, 60.0, 30.0, 80.0, 75.0, 40.0],
        "p_especifico": [95.0, 30.0, 85.0, 90.0, 20.0, 60.0, 30.0, 80.0, 75.0, 50.0],
        "pool": [900.0, 100.0, 800.0, 950.0, 50.0, 500.0, 200.0, 700.0, 600.0, 300.0],
        "industrias_hoy": [0, 0, 0, 0, 0, 0, 0, 1, 1, 1] * 1,
    })


def test_umbrales_con_menos_de_10_productores_usan_la_mediana_y_lo_avisan():
    d = _fichas()
    u = ej.umbrales(d, "productores")
    assert u["n_productores"] == 3 and "menos de 10" in u["referencia"]
    assert u["base"] == d["p_base"].median()
    assert ej.umbrales(d, "mediana")["referencia"] == "mediana de todos los distritos"


def test_umbrales_con_suficientes_productores_son_el_percentil_10_de_los_productores():
    d = pd.DataFrame({"p_base": np.arange(1.0, 21.0), "p_especifico": np.arange(1.0, 21.0), "pool": np.arange(1.0, 21.0), "industrias_hoy": [1] * 12 + [0] * 8})
    u = ej.umbrales(d, "productores")
    assert u["referencia"].startswith("productores")
    assert abs(u["base"] - np.quantile(np.arange(1.0, 13.0), 0.10)) < 1e-9


def test_las_cuatro_categorias_para_una_industria_que_exige_formacion():
    d = _fichas()
    g = ej.diagnostico(d, exige=True, referencia="mediana")                              # umbral en la mediana para un caso a mano
    ub, ue = g["umbral_base"].iloc[0], g["umbral_especifico"].iloc[0]
    esperado = ["lista" if (b >= ub and e >= ue) else "falta formación específica" if b >= ub else "falta base" if e >= ue else "faltan ambas"
                for b, e in zip(d["p_base"], d["p_especifico"], strict=True)]
    assert list(g["categoria"]) == esperado
    assert set(esperado) == set(ej.CATEGORIAS)
    assert (g.loc[g["categoria"] == "faltan ambas", "faltan_graduados"] >= 0).all()


def test_una_industria_que_no_exige_solo_clasifica_por_la_base():
    g = ej.diagnostico(_fichas(), exige=False, referencia="mediana")
    assert set(g["categoria"]) == {"lista", "falta base"}
    assert g["faltan_graduados"].isna().all()                                            # no hay brecha de formación que medir
    assert list(g["orden"]) == list(g["p_base"])


def test_falta_formacion_cuantifica_los_graduados_que_faltan_hasta_el_umbral():
    d = _fichas()
    g = ej.diagnostico(d, exige=True, referencia="mediana")
    u_pool = d["pool"].median()
    f = g[g["categoria"] == "falta formación específica"]
    assert len(f) > 0 and (f["faltan_graduados"] == (u_pool - f["pool"]).clip(lower=0).round(0)).all()


def test_un_distrito_sin_dato_queda_marcado_y_no_se_clasifica():
    d = _fichas()
    d.loc[0, "p_base"] = np.nan
    assert ej.diagnostico(d, exige=True, referencia="mediana").loc[0, "categoria"] == "sin dato"
