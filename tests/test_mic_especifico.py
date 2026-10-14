import pandas as pd

from src.puentes import mic_especifico as me


def _puente():
    return pd.DataFrame([
        {"sector_mic": "X", "subsector_mic": "CARPINTERIA Y EBANISTERIA", "sector_id": "S24", "confianza": "media", "ciiu4": "1622", "peso": 0.6},
        {"sector_mic": "X", "subsector_mic": "CARPINTERIA Y EBANISTERIA", "sector_id": "S25", "confianza": "media", "ciiu4": "3100", "peso": 0.4},
        {"sector_mic": "X", "subsector_mic": "INDUSTRIA GENERAL Y MULTIACTIVIDAD", "sector_id": "", "confianza": "sin_sector", "ciiu4": "", "peso": 0.0},
        {"sector_mic": "X", "subsector_mic": "CAL Y DERIVADOS", "sector_id": "S33", "confianza": "alta", "ciiu4": "2394", "peso": 1.0},
    ])


def test_normalizar_quita_tildes_y_caracteres_rotos():
    assert me.normalizar("  Carpintería\xad  y  herrería ") == "CARPINTERIA Y HERRERIA"
    assert me.partes("HERRERIA Y HOJALATERIA, CARPINTERIA/VIDRIERIA") == ["HERRERIA", "HOJALATERIA", "CARPINTERIA", "VIDRIERIA"]


def test_regla_simple_y_primera_coincidencia_gana():
    clases, conf, _ = me.desde_reglas("PANADERIA")
    assert clases == [("1071", 1.0)] and conf == "alta"
    clases, _, _ = me.desde_reglas("FABRICA DE HIELO")
    assert clases == [("3530", 1.0)]  # HIELO antes que FABRICA


def test_compuesto_reparte_por_igual_y_baja_la_confianza_si_cambia_de_sector():
    clases, conf, _ = me.desde_reglas("HERRERIA Y TORNERIA")
    assert dict(clases) == {"2511": 0.5, "2592": 0.5}
    clases, conf, _ = me.desde_reglas("TORNERIA Y SOLDADURA")
    assert clases == [("2592", 1.0)] and conf == "alta"  # las dos partes caen en la misma clase
    clases, conf, _ = me.desde_reglas("CARPINTERIA Y VENTA")
    assert conf == "media" and dict(clases) == {"1622": 0.6, "3100": 0.4}  # VENTA no decide, no cambia nada


def test_generico_y_sin_regla():
    assert me.desde_reglas("FABRICA") == me.GENERICO
    assert me.desde_reglas("XYZQ") is None
    assert me.desde_reglas("CARBONERIA") == me.HEREDAR


def test_sin_regla_hereda_el_subsector_con_confianza_baja():
    filas = me.mapear("COSA RARA", "CARPINTERIA Y EBANISTERIA", _puente())
    assert {f["sector_id"] for f in filas} == {"S24", "S25"}
    assert all(f["confianza"] == "baja" and f["fuente"] == "heredado_subsector" for f in filas)
    assert me.mapear("COSA RARA", "INDUSTRIA GENERAL Y MULTIACTIVIDAD", _puente())[0]["confianza"] == "sin_sector"


def test_discrepancia_con_el_subsector_usa_la_regla_y_baja_un_escalon():
    filas = me.mapear("TABACALERA", "CAL Y DERIVADOS", _puente())
    assert filas[0]["ciiu4"] == "1200" and filas[0]["discrepancia_subsector"] and filas[0]["confianza"] == "media"
    ok = me.mapear("CALERA", "CAL Y DERIVADOS", _puente())
    assert not ok[0]["discrepancia_subsector"] and ok[0]["confianza"] == "alta"


def test_por_distrito_reparte_la_industria_segun_el_peso():
    esp = pd.DataFrame({"especifico": ["CARPINTERIA", "CARPINTERIA", "FABRICA"], "sector_id": ["S24", "S25", ""], "peso": [0.6, 0.4, 0.0], "confianza": ["media", "media", "sin_sector"]})
    loc = pd.DataFrame({"departamento": ["A", "A"], "distrito": ["D", "D"], "especifico": ["CARPINTERIA", "FABRICA"]})
    d = me.por_distrito(loc, esp).set_index("sector_id").n_industrias
    assert abs(d["S24"] - 0.6) < 1e-9 and abs(d["S25"] - 0.4) < 1e-9 and d[""] == 1.0


def test_las_actividades_mas_frecuentes_caen_donde_el_equipo_espera():
    esperado = {"OLERIA": "2392", "HERRERIA": "2511", "PANADERIA": "1071", "ASERRADERO": "1610", "TORNERIA": "2592", "VIDRIERIA": "2310", "RECICLADORA": "3830",
                "CURTIEMBRE": "1511", "FABRICA DE ESENCIA DE PETITGRAIN": "2029", "PANADERIA Y CONFITERIA": "1071", "MOLINO MINERO": "0810", "TABACALERA": "1200"}
    for texto, clase in esperado.items():
        assert me.desde_reglas(texto)[0][0][0] == clase, texto
    assert dict(me.desde_reglas("CARPINTERIA")[0]) == {"1622": 0.6, "3100": 0.4}  # ambigua: se reparte, confianza media


def test_actividades_en_sectores_sin_nada_en_comun_bajan_a_confianza_baja():
    assert me.desde_reglas("CARPINTERIA Y HERRERIA")[1] == "baja"
    assert me.desde_reglas("CARPINTERIA Y MUEBLERIA")[1] == "media"  # comparten el sector de muebles
