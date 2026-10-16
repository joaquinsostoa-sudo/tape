import pandas as pd

from src.puentes import carrera_sector as cs


def test_limpiar_quita_prefijos_y_normaliza():
    assert cs.limpiar("Especialización en Ortodoncia y Ortopedia Facial") == "ORTODONCIA Y ORTOPEDIA FACIAL"
    assert cs.limpiar("TÉCNICO SUPERIOR EN Electricidad") == "ELECTRICIDAD"


def test_las_reglas_que_fallaron_en_la_revision_ya_no_fallan():
    casos = {
        "RADIOLOGIA": "diagnostico_terapia",                       # no es comunicación por la palabra «radio»
        "MATEMATICA": "ciencias_basicas_investigacion",             # no es informática por «tic»
        "CIENCIAS ADMINISTRATIVAS": "administracion_empresas",
        "CIENCIAS SOCIALES": "ciencias_sociales_humanidades",
        "ADMINISTRACION AGROPECUARIA": "agronomia_produccion",     # no es veterinaria por «pecuari»
        "MEDICINA VETERINARIA": "veterinaria_zootecnia",            # no es salud humana
        "DOCENCIA UNIVERSITARIA": "educacion",
        "TECNOLOGIAS DE LA INFORMACION Y LA COMUNICACION": "informatica",
        "FUTBOL DE CAMPO": "educacion_fisica_deporte",              # no es agronomía por «campo»
        "ANTROPOLOGIA CULTURAL GUARANI Y PARAGUAYA": "ciencias_sociales_humanidades",  # no es idioma por «guaraní»
    }
    for carrera, campo in casos.items():
        assert cs.campo_de(carrera)[0] == campo, carrera


def test_campos_principales():
    assert cs.campo_de("ENFERMERIA")[0] == "enfermeria_obstetricia"
    assert cs.campo_de("DERECHO")[0] == "derecho_notariado"
    assert cs.campo_de("INGENIERIA AGRONOMICA")[0] == "agronomia_produccion"
    assert cs.campo_de("TECNOLOGIA DE ALIMENTOS")[0] == "alimentos_agroindustria"
    assert cs.campo_de("ZZZ SIN SENTIDO") is None


def test_nivel_del_titulo():
    assert cs.nivel_titulo("LICENCIADO/A") == "grado"
    assert cs.nivel_titulo("INGENIERO/A AGRONOMO/A") == "grado"
    assert cs.nivel_titulo("TECNICO SUPERIOR EN ENFERMERIA") == "tecnico"
    assert cs.nivel_titulo("TÉCNICO DOCENTE EN EDUCACIÓN INCLUSIVA") == "docente"
    assert cs.nivel_titulo("HABILITACIÓN PEDAGÓGICA PARA EGRESADOS UNIVERSITARIOS") == "docente"
    assert cs.nivel_titulo("PROFESOR DE EDUCACIÓN INICIAL") == "docente"
    assert cs.nivel_titulo("ESPECIALISTA EN DIDÁCTICA UNIVERSITARIA") == "especializacion"
    assert cs.nivel_titulo("MAGISTER") == "maestria" and cs.nivel_titulo("MASTER EN TEOLOGIA") == "maestria"
    assert cs.nivel_titulo("DOCTOR/A") == "doctorado"
    assert cs.nivel_titulo("DOCTOR/A EN ODONTOLOGÍA") == "grado"   # en Paraguay es un título de grado
    assert cs.nivel_titulo("ALGO RARO") == "otro"


def test_todo_campo_declarado_tiene_sectores_validos_y_confianza_coherente():
    ids = set(pd.read_csv(cs.RAIZ / "data" / "clean" / "taxonomia_sectores_tape.csv")["sector_id"])
    for campo, (_, sectores, _, conf) in cs.CAMPOS.items():
        assert sectores and set(sectores) <= ids, campo
        if len(sectores) > 5:
            assert conf == "baja", campo                         # regla D27: más de 5 sectores = confianza baja
    assert {c for _, c in cs.REGLAS} <= set(cs.CAMPOS)           # ninguna regla apunta a un campo inexistente


def test_transversales_no_tienen_sector_y_guardan_el_sector_futuro():
    for campo in ("derecho_notariado", "contabilidad_auditoria", "economia", "administracion_empresas", "marketing_publicidad"):
        _, sectores, trans, _ = cs.CAMPOS[campo]
        assert trans and len(sectores) == 1 and sectores[0] in ("S61", "S62")      # solo informativo
    p = cs.puente_carreras(_conteos())
    d = p[p["carrera"] == "DERECHO"]
    assert len(d) == 1 and d.iloc[0]["sector_id"] == "" and d.iloc[0]["tipo"] == "transversal" and d.iloc[0]["sector_futuro"] == "S61"


def _conteos():
    return pd.DataFrame({
        "carrera": ["INGENIERIA AGRONOMICA", "DERECHO", "ZZZ SIN SENTIDO"],
        "titulo": ["INGENIERO/A AGRONOMO/A", "ABOGADO/A", "LICENCIADO/A"],
        "institucion": ["UNIVERSIDAD A", "UNIVERSIDAD A", "UNIVERSIDAD B"],
        "titulos": [10, 4, 6],
    })


def _pesos():
    return pd.DataFrame({
        "nom": ["UNIVERSIDAD A", "UNIVERSIDAD A", "UNIVERSIDAD A"], "escenario": ["principal", "parejo", "parejo"],
        "departamento": ["CENTRAL", "CENTRAL", "ASUNCION"], "distrito": ["San Lorenzo", "San Lorenzo", "Asunción"],
        "unidad_2011": ["x", "x", "y"], "peso": [1.0, 0.5, 0.5], "confianza": ["baja"] * 3,
    })


def test_cuenta_completa_cada_sector_del_campo_recibe_el_titulo_entero():
    p = cs.puente_carreras(_conteos())
    a = p[p["carrera"] == "INGENIERIA AGRONOMICA"]
    assert set(a["sector_id"]) == set(cs.AGRO) and (a["peso"] == 1.0).all() and (a["n_sectores"] == 5).all()
    f = cs.titulos_sector_distrito(_conteos(), p, _pesos())
    agro = f[(f["escenario"] == "principal") & (f["sector_id"] == "S01")]
    assert round(agro["titulos"].sum(), 6) == 10                                   # entero, no 10 / 5
    todos = f[(f["escenario"] == "principal") & f["sector_id"].isin(cs.AGRO)]
    assert round(todos["titulos"].sum(), 6) == 50                                  # los sectores no se pueden sumar: 5 x 10


def test_la_tabla_de_totales_cuenta_cada_titulo_una_vez_y_conserva_lo_no_ubicado():
    c = _conteos()
    p = cs.puente_carreras(c)
    t = cs.titulos_distrito(c, p, _pesos())
    for esc in ("principal", "parejo"):
        assert round(t[t["escenario"] == esc]["titulos"].sum(), 6) == 20            # 10 + 4 + 6, sin doble conteo
    sin = t[(t["escenario"] == "principal") & (t["distrito"] == "")]
    assert round(sin["titulos"].sum(), 6) == 6 and set(sin["confianza_ubicacion"]) == {"sin_ubicar"}     # UNIVERSIDAD B no está ubicada
    trans = t[(t["escenario"] == "parejo") & (t["tipo"] == "transversal")]
    assert round(trans["titulos"].sum(), 6) == 4                                    # la base transversal suma al distrito
    assert "control" in dir(cs) and "20" in cs.control(p, t, 20).replace(",", "")
