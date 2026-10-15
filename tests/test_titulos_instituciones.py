import pandas as pd

from src.puentes import titulos_instituciones as ti


def test_partir_separa_el_lugar_por_guion_o_por_marca():
    assert ti.partir("UNIVERSIDAD CATÓLICA NUESTRA SEÑORA DE LA ASUNCIÓN - CAMPUS UNIVERSITARIO ALTO PARANA") == (
        "UNIVERSIDAD CATOLICA NUESTRA SENORA DE LA ASUNCION", "CAMPUS UNIVERSITARIO ALTO PARANA")
    assert ti.partir("UNIVERSIDAD PRIVADA DEL GUAIRA SEDE ENCARNACION") == ("UNIVERSIDAD PRIVADA DEL GUAIRA", "SEDE ENCARNACION")
    assert ti.partir("  \tINSTITUTO X - FILIAL ITAPUA") == ("INSTITUTO X", "FILIAL ITAPUA")
    assert ti.partir("UNIVERSIDAD DEL NORTE") == ("UNIVERSIDAD DEL NORTE", "")


def test_palabras_expande_abreviaturas_y_saca_palabras_vacias():
    assert ti.palabras("UNIV. CATOLICA NTRA. SRA. DE LA ASUNCION") == ti.palabras("UNIVERSIDAD CATÓLICA NUESTRA SEÑORA DE LA ASUNCIÓN")


def test_jaccard_a_mano():
    a, b = frozenset(["A", "B", "C", "D"]), frozenset(["A", "B", "C", "E"])
    assert ti.jaccard(a, b) == 3 / 5
    assert ti.jaccard(a, frozenset()) == 0.0


def test_lugar_limpio_quita_marcas():
    assert ti.lugar_limpio("CAMPUS UNIVERSITARIO ALTO PARANA") == "ALTO PARANA"
    assert ti.lugar_limpio("SEDE CIUDAD DEL ESTE") == "CIUDAD DEL ESTE"
    assert ti.lugar_limpio("FILIAL EN ITAPUA") == "ITAPUA"


def test_cruce_exacto_similitud_y_umbrales():
    bases = {b: ti.palabras(b) for b in ["UNIVERSIDAD DEL NORTE", "UNIVERSIDAD PRIVADA DEL ESTE", "INSTITUTO TECNICO SUPERIOR SAN JOSE"]}
    assert ti.cruzar_base("UNIVERSIDAD DEL NORTE", bases)[0] == "exacto"
    m = ti.cruzar_base("UNIV PRIVADA DEL ESTE", bases)
    assert m[0] == "similitud" and m[1] == "UNIVERSIDAD PRIVADA DEL ESTE"
    assert ti.cruzar_base("CENTRO DE ESTUDIOS MARINOS", bases)[0] == "sin_cruce"
    # 3 de 5 palabras en común: entre 0,60 y 0,80, queda para revisar y no se asigna
    assert ti.cruzar_base("INSTITUTO TECNICO SUPERIOR SAN CARLOS", bases)[0] == "revisar"


def test_no_acepta_si_el_segundo_candidato_esta_muy_cerca():
    bases = {b: ti.palabras(b) for b in ["INSTITUTO SUPERIOR SANTA ROSA UNO", "INSTITUTO SUPERIOR SANTA ROSA DOS"]}
    # el nombre comparte 4 palabras con ambos (0,67 y 0,67): ninguno supera el umbral
    assert ti.cruzar_base("INSTITUTO SUPERIOR SANTA ROSA", bases)[0] in ("revisar", "similitud")
    assert ti.cruzar_base("INSTITUTO SUPERIOR SANTA ROSA", bases)[0] != "exacto"


def test_sede_principal_toma_el_distrito_con_mas_filas_y_marca_el_empate():
    f = pd.Series({("ALTO PARANA", "CIUDADDELESTE"): 5, ("ALTO PARANA", "HERNANDARIAS"): 2})
    assert ti.sede_principal(f, {})[0] == ("ALTO PARANA", "CIUDADDELESTE") and not ti.sede_principal(f, {})[1]
    g = pd.Series({("ASUNCION", "ASUNCION"): 3, ("CENTRAL", "LUQUE"): 3})
    k, empate = ti.sede_principal(g, {})
    assert empate and k == ("ASUNCION", "ASUNCION")


def _distritos():
    filas = [
        ("ALTO PARANA", ti.llave("Ciudad del Este"), "Ciudad del Este", "Ciudad del Este"),
        ("ALTO PARANA", ti.llave("Hernandarias"), "Hernandarias", "Hernandarias"),
        ("ITAPUA", ti.llave("Encarnación"), "Encarnación", "Encarnación"),
        ("ITAPUA", ti.llave("Hohenau"), "Hohenau", "Hohenau"),
        ("MISIONES", ti.llave("San Juan Bautista"), "San Juan Bautista", "San Juan Bautista"),
        ("NEEMBUCU", ti.llave("San Juan Bautista"), "San Juan Bautista", "San Juan Bautista"),
        ("ASUNCION", ti.llave("Asunción"), "Asunción", "Asunción"),
    ]
    return pd.DataFrame(filas, columns=["dep", "clave", "distrito", "unidad_2011"])


def test_resolver_lugar_distrito_departamento_y_no_lugar():
    d = _distritos()
    assert ti.resolver_lugar("SEDE ENCARNACION", set(), d, set()) == ("distrito", "ITAPUA", ti.llave("Encarnación"))
    assert ti.resolver_lugar("CAMPUS UNIVERSITARIO ALTO PARANA", set(), d, set()) == ("departamento", "ALTO PARANA")
    assert ti.resolver_lugar("DERECHO", set(), d, set()) is None
    # un distrito repetido en dos departamentos se resuelve con la pista de los campus
    assert ti.resolver_lugar("SAN JUAN BAUTISTA", {"MISIONES"}, d, set()) == ("distrito", "MISIONES", ti.llave("San Juan Bautista"))
    assert ti.resolver_lugar("SAN JUAN BAUTISTA", set(), d, set()) is None


def _campus(filas):
    df = pd.DataFrame(filas, columns=["nombre_institucion", "nombre_departamento", "nombre_distrito"])
    df["base"] = [ti.partir(n)[0] for n in df["nombre_institucion"]]
    df["dep"] = [ti.departamento(n) for n in df["nombre_departamento"]]
    df["clave"] = [ti.llave(n) for n in df["nombre_distrito"]]
    return df


def _conteos(nombres):
    return pd.DataFrame([{"institucion": n, "institucion_id": str(i), "titulos": t} for i, (n, t) in enumerate(nombres)])


def test_construir_asigna_confianzas_y_escenarios():
    campus = _campus([
        ("UNIVERSIDAD DEL NORTE", "ALTO PARANA", "CIUDAD DEL ESTE"),
        ("UNIVERSIDAD DEL NORTE", "ALTO PARANA", "CIUDAD DEL ESTE"),
        ("UNIVERSIDAD DEL NORTE", "ALTO PARANA", "HERNANDARIAS"),
        ("INSTITUTO UNICO", "ITAPUA", "HOHENAU"),
    ])
    conteos = _conteos([
        ("UNIVERSIDAD DEL NORTE", 100),                       # varias sedes: sede principal, baja
        ("UNIVERSIDAD DEL NORTE - HERNANDARIAS", 10),         # lugar explícito: alta
        ("INSTITUTO UNICO", 50),                              # una sola sede, cruce exacto: alta
        ("INSTITUTO RARO DE OTRA COSA", 5),                   # sin cruce
        ("INSTITUTO TECNICO EUROSUR SEDE ENCARNACION", 7),    # base sin cruce pero lugar explícito: alta
    ])
    p, w = ti.construir(conteos, campus, _distritos())
    f = p.set_index("nom")
    assert f.loc["UNIVERSIDAD DEL NORTE", "confianza"] == "baja" and f.loc["UNIVERSIDAD DEL NORTE", "distrito_principal"] == "Ciudad del Este"
    assert f.loc["UNIVERSIDAD DEL NORTE HERNANDARIAS", "confianza"] == "alta" and f.loc["UNIVERSIDAD DEL NORTE HERNANDARIAS", "distrito_principal"] == "Hernandarias"
    assert f.loc["INSTITUTO UNICO", "confianza"] == "alta"
    assert f.loc["INSTITUTO RARO DE OTRA COSA", "metodo_ubicacion"] == "sin_cruce" and f.loc["INSTITUTO RARO DE OTRA COSA", "revisar"]
    assert f.loc["INSTITUTO TECNICO EUROSUR SEDE ENCARNACION", "confianza"] == "alta"
    # los pesos de cada institución ubicada suman uno en cada escenario
    s = w.groupby(["nom", "escenario"])["peso"].sum()
    assert (s.round(9) == 1.0).all()
    parejo = w[(w.nom == "UNIVERSIDAD DEL NORTE") & (w.escenario == "parejo")]
    assert sorted(parejo["peso"].round(3)) == [0.5, 0.5]


def test_resumen_suma_el_total_de_titulos():
    p = pd.DataFrame({"nom": ["a", "b"], "titulos": [30, 70], "metodo_ubicacion": ["x", "y"], "confianza": ["alta", "baja"]})
    r = ti.resumen(p)
    assert r["titulos"].sum() == 100 and r["pct_titulos"].sum() == 100.0


def test_desempate_prefiere_asuncion_a_la_capital_departamental():
    f = pd.Series({("CONCEPCION", ti.llave("Concepción")): 2, ("ASUNCION", "ASUNCION"): 2, ("ITAPUA", "LUQUE"): 2})
    k, empate = ti.sede_principal(f, {})
    assert empate and k == ("ASUNCION", "ASUNCION")
    g = pd.Series({("CONCEPCION", ti.llave("Concepción")): 2, ("ITAPUA", "HOHENAU"): 2})
    assert ti.sede_principal(g, {})[0] == ("CONCEPCION", ti.llave("Concepción"))


def test_nombres_del_mec_con_las_mismas_palabras_son_una_sola_institucion():
    campus = _campus([
        ("INSTITUTO DE FORMACION DOCENTE CAAZAPA", "CAAZAPA", "CAAZAPA"),
        ("INST. DE FORM. DOC. CAAZAPA", "CAAZAPA", "CAAZAPA"),
    ])
    d = pd.DataFrame([("CAAZAPA", ti.llave("Caazapá"), "Caazapá", "Caazapá")], columns=["dep", "clave", "distrito", "unidad_2011"])
    p, _ = ti.construir(_conteos([("INSTITUTO DE FORMACIÓN DOCENTE DE CAAZAPÁ", 1477)]), campus, d)
    assert p.iloc[0]["metodo_cruce"] in ("exacto", "similitud") and p.iloc[0]["distrito_principal"] == "Caazapá"


def test_ajustar_distritos_empareja_nombres_escritos_distinto_y_deja_sin_emparejar_los_que_faltan():
    d = pd.DataFrame([
        ("CORDILLERA", ti.llave("Primero de Marzo"), "Primero de Marzo", "x"),
        ("BOQUERON", ti.llave("Filadelfia"), "Filadelfia", "x"),
    ], columns=["dep", "clave", "distrito", "unidad_2011"])
    campus = pd.DataFrame({
        "dep": ["CORDILLERA", "BOQUERON", "CONCEPCION"],
        "nombre_distrito": ["PRIMERO DE MARZO", "FERNHEIM", "VALLEMI"],
    })
    campus["clave"] = [ti.llave(n) for n in campus["nombre_distrito"]]
    nuevo, aj = ti.ajustar_distritos(campus, d)
    assert nuevo.loc[1, "clave"] == ti.llave("Filadelfia")            # alias declarado
    assert nuevo.loc[2, "clave"] == ti.llave("VALLEMI")                # no hay con qué emparejarlo: queda igual y se lista
    assert aj[aj.distrito_mec == "VALLEMI"].iloc[0]["clave_tabla"] == ""


def test_sensibilidad_conserva_el_total_y_reparte_parejo():
    p = pd.DataFrame({"nom": ["a"], "titulos": [100]})
    w = pd.DataFrame({
        "nom": ["a", "a", "a"], "escenario": ["principal", "parejo", "parejo"],
        "departamento": ["ASUNCION", "ASUNCION", "ITAPUA"], "peso": [1.0, 0.5, 0.5],
    })
    s = ti.sensibilidad(p, w).set_index("departamento")
    assert s["principal"].sum() == 100 and s["parejo"].sum() == 100
    assert s.loc["ASUNCION", "diferencia"] == -50 and s.loc["ITAPUA", "diferencia"] == 50
