"""Cruce carrera → sector TAPE y títulos por sector × distrito (D27 final y D28, capital humano específico).

Dos pasos auditables, declarados en `docs/supuestos.md` antes de construir:
1. carrera (nombre normalizado) → *campo* de estudio por reglas de texto en orden (gana la primera que coincide). Cada campo lleva un código CINE-F 2013 aproximado
   (asignación propia, a validar), los sectores TAPE a los que sirve, si es transversal y su confianza.
2. campo → sectores con **cuenta completa**: cada título cuenta entero en cada sector del campo (se mide la disponibilidad de personal formado, no cuántos trabajan en el sector),
   así que los sectores no se pueden sumar entre sí. Las carreras transversales (derecho, contabilidad, administración, economía, marketing) no van a ningún sector:
   forman la base transversal y suman igual al total del distrito.

El nivel del título (técnico, grado, docente, especialización, maestría, doctorado) sale de la columna `titulo`; el indicador de formación específica usa técnico y grado.
Cada título se reparte entre los distritos de su institución con los pesos de `titulos_instituciones.py` (D17), en los dos escenarios (sede principal y reparto parejo).
Los títulos de instituciones sin ubicar se conservan con distrito vacío. `titulos_distrito.csv` cuenta cada título una sola vez (suma el total).

Salidas: `puente_carrera_sector.csv`, `titulos_sector_distrito.csv` y `titulos_distrito.csv` (sin datos personales). Requiere `exigencia_formacion_sector.csv` (`exigencia_sector.py`, D28).
Uso: uv run python -m src.puentes.exigencia_sector && uv run python -m src.puentes.carrera_sector
"""
from __future__ import annotations

import re

import pandas as pd

from .distritos import normalizar
from .taxonomia_tape import RAIZ

CONTEOS = RAIZ / "data" / "clean" / "titulos_conteos.parquet"
PESOS_INSTITUCION = RAIZ / "data" / "clean" / "titulos_institucion_distrito.csv"
SALIDA_PUENTE = RAIZ / "data" / "clean" / "puente_carrera_sector.csv"
SALIDA_SECTOR_DISTRITO = RAIZ / "data" / "clean" / "titulos_sector_distrito.csv"
SALIDA_TOTALES = RAIZ / "data" / "clean" / "titulos_distrito.csv"
EXIGENCIA = RAIZ / "data" / "clean" / "exigencia_formacion_sector.csv"
MANUFACTURA = [f"S{i:02d}" for i in range(9, 45)]
ALIMENTOS = [f"S{i:02d}" for i in range(9, 20)]
AGRO = ["S01", "S02", "S03", "S04", "S05"]
PREFIJOS = re.compile(r"^(ESPECIALIZACION|MAESTRIA|MASTER|DOCTORADO|TECNICO SUPERIOR|TECNICO|LICENCIATURA|ESPECIALISTA)\s+(EN|DE|EN LA|EN EL)\s+")

# campo: (CINE-F aproximado, sectores, transversal, confianza). Más de 5 sectores = confianza baja.
CAMPOS: dict[str, tuple[str, list[str], bool, str]] = {
    "educacion": ("0110", ["S64"], False, "alta"),
    "educacion_fisica_deporte": ("1014", ["S64", "S66"], False, "media"),
    "idiomas_humanidades": ("0230", ["S64"], False, "media"),
    "ciencias_sociales_humanidades": ("0310", ["S64", "S61"], False, "media"),
    "teologia_religion": ("0221", ["S67"], False, "media"),
    "artes_musica": ("0210", ["S66"], False, "alta"),
    "bibliotecologia": ("0322", ["S66"], False, "media"),
    "comunicacion_medios": ("0321", ["S58"], False, "alta"),
    "diseno_grafico": ("0213", ["S58", "S27"], False, "media"),
    "diseno_moda_textil": ("0723", ["S21", "S22", "S23"], False, "media"),
    "derecho_notariado": ("0421", ["S61"], True, "alta"),
    "contabilidad_auditoria": ("0411", ["S61"], True, "alta"),
    "economia": ("0311", ["S61"], True, "alta"),
    "administracion_empresas": ("0413", ["S62"], True, "alta"),
    "marketing_publicidad": ("0414", ["S61"], True, "media"),
    "finanzas_banca": ("0412", ["S59"], False, "alta"),
    "cooperativas": ("0413", ["S59"], False, "media"),
    "comercio_exterior_aduana": ("0416", ["S49", "S53"], False, "media"),
    "gestion_publica_politica": ("0312", ["S63"], False, "alta"),
    "seguridad_defensa": ("1031", ["S63"], False, "alta"),
    "salud_clinica": ("0912", ["S65"], False, "alta"),
    "enfermeria_obstetricia": ("0913", ["S65"], False, "alta"),
    "odontologia": ("0911", ["S65"], False, "alta"),
    "diagnostico_terapia": ("0914", ["S65"], False, "alta"),
    "nutricion": ("0915", ["S65"], False, "alta"),
    "salud_publica_gestion": ("0910", ["S65"], False, "alta"),
    "psicologia": ("0313", ["S65"], False, "media"),
    "trabajo_social": ("0923", ["S65"], False, "alta"),
    "farmacia_bioquimica": ("0916", ["S31", "S65"], False, "media"),
    "veterinaria_zootecnia": ("0841", ["S03", "S04"], False, "media"),
    "agronomia_produccion": ("0811", AGRO, False, "media"),
    "forestal": ("0821", ["S06", "S24"], False, "media"),
    "pesca_acuicultura": ("0831", ["S07"], False, "alta"),
    "alimentos_agroindustria": ("0721", ALIMENTOS, False, "baja"),
    "ingenieria_quimica": ("0711", ["S28", "S29", "S30", "S31", "S32"], False, "media"),
    "electricidad_energia": ("0713", ["S40", "S44", "S45"], False, "media"),
    "electronica_telecom": ("0714", ["S40", "S56"], False, "media"),
    "mecanica_industrial": ("0715", ["S38", "S39", "S44"], False, "media"),
    "automotriz": ("0716", ["S41", "S44", "S50"], False, "media"),
    "naval_transporte": ("0716", ["S42", "S51", "S52"], False, "media"),
    "ingenieria_industrial": ("0710", MANUFACTURA, False, "baja"),
    "madera_muebles": ("0722", ["S24", "S25"], False, "media"),
    "arquitectura": ("0731", ["S48", "S61"], False, "media"),
    "ingenieria_civil_construccion": ("0732", ["S48"], False, "alta"),
    "topografia_geomatica": ("0732", ["S61"], False, "media"),
    "ambiental": ("0521", ["S46", "S47"], False, "media"),
    "geologia_mineria": ("0724", ["S08"], False, "alta"),
    "informatica": ("0613", ["S57"], False, "alta"),
    "turismo": ("1015", ["S55", "S54"], False, "media"),
    "hoteleria_gastronomia": ("1013", ["S54"], False, "alta"),
    "estetica_servicios_personales": ("1012", ["S67"], False, "alta"),
    "ciencias_basicas_investigacion": ("0531", ["S61"], False, "media"),
}

# (patrón sobre el nombre normalizado y sin prefijo, campo). Gana la primera que coincide.
REGLAS: list[tuple[str, str]] = [
    (r"EDUCACION FISICA|PREPARADOR FISICO|PREPARACION FISICA|CIENCIAS DEL DEPORTE|GESTION DEPORTIVA|FUTBOL|ENTRENAMIENTO|DEPORTE|RECREACION|NATACION|ATLETISMO|BASQUETBOL|VOLEIBOL|\bTENIS\b|CICLISMO", "educacion_fisica_deporte"),
    (r"PEDAGOG|DIDACTIC|DOCENT|DOCENCIA|EDUCATIV|PROFESORADO|^PROFESOR|EDUCACION (ESCOLAR|INICIAL|INCLUSIVA|BILINGUE|ARTISTICA|MATEMATICA|BASADA|DE LAS|PARA|SUPERIOR|INTERCULTURAL)|CIENCIAS DE LA EDUCACION|^EDUCACION|FORMACION ESPECIFICA|HABILITACION PEDAGOGICA|PRIMERA INFANCIA|APRENDIZAJES|PROFESIONALIZACION|CURRICUL|NORMAL SUPERIOR|ESCUELAS|TRABAJO Y TECNOLOGIA|EVALUACION INSTITUCIONAL|EDUCACION", "educacion"),
    (r"ENFERMERIA|OBSTETRICIA|PARTERIA", "enfermeria_obstetricia"),
    (r"ODONTOLOGIA|ORTODONCIA|ENDODONCIA|PROTESIS DENTAL|OPERATORIA DENTAL|IMPLANT|REHABILITACION ORAL|PERIODONCIA|ODONTOPEDIATRIA|CIRUGIA BUCAL|DENTAL", "odontologia"),
    (r"FARMACI|BIOQUIMIC|QUIMICA Y FARMACIA|CIENCIAS FARMACEUTICAS|FARMACEUTIC", "farmacia_bioquimica"),
    (r"NUTRICION|DIETETICA|OBESIDAD|TRASTORNOS ALIMENTARIOS", "nutricion"),
    (r"SALUD PUBLICA|ADMINISTRACION HOSPITALARIA|GESTION HOSPITALARIA|ADMINISTRACION Y GESTION HOSPITALARIA|SISTEMAS DE SALUD|EPIDEMIOLOGIA|GESTION SANITARIA|GERENCIA EN SALUD", "salud_publica_gestion"),
    (r"RADIOLOGIA|IMAGEN|ECOGRAFIA|LABORATORIO|KINESIOLOGIA|FISIOTERAPIA|FISIATRIA|FONOAUDIOLOGIA|INSTRUMENTACION QUIRURGICA|INSTRUMENTACION Y AREA|QUIRURGIC|OPTICA|CONTACTOLOGIA|MASAJE|PODOLOGIA|REHABILITACION|TERAPIA|CITOLOGIA|HEMOTERAPIA|AUDIOLOGIA|ELECTROMEDICINA|EMERGENCIA|ANESTESI|PSICOMOTRICIDAD", "diagnostico_terapia"),
    (r"PSICOLOGIA|PSIQUIATRIA|NEUROPSICOLOGIA|CONSEJERIA", "psicologia"),
    (r"TRABAJO SOCIAL|ASISTENCIA SOCIAL|DESARROLLO COMUNITARIO|GERONTOLOGIA|NINEZ Y LA ADOLESCENCIA|NINEZ Y ADOLESCENCIA|ESTIMULACION TEMPRANA|DESARROLLO INFANTIL", "trabajo_social"),
    (r"AGRONOM|AGROPECUARI|AGRARI|AGRICOLA|AGRICULTURA|PRODUCCION VEGETAL|AGROECOLOG|HORTICULTURA|FRUTICULTURA|RURAL|\bCAMPO\b|SUELOS|AGRONEGOCIOS|AGRIBUSINESS|CULTIVOS", "agronomia_produccion"),
    (r"VETERINARI|ZOOTECN|PRODUCCION ANIMAL|SANIDAD ANIMAL|GANADER|PECUARI|AVICULTURA|APICULTURA", "veterinaria_zootecnia"),
    (r"MEDICINA|CIRUGIA|CIRUJANO|PEDIATRIA|GINECOLOGIA|TRAUMATOLOGIA|CARDIOLOGIA|DERMATOLOGIA|NEUROLOGIA|ONCOLOGIA|UROLOGIA|OFTALMOLOGIA|OTORRINO|ENDOCRINOLOGIA|COLPOSCOPIA|PATOLOGIA|NEONATOLOGIA|INTENSIVA|CLINICA|MEDICO|SALUD|GERIATRIA|NEFROLOGIA|GASTROENTEROLOGIA|REUMATOLOGIA|INFECTOLOGIA|HEMATOLOGIA|FAMILIAR Y COMUNITARIA|ANATOMIA|ORTOPEDIA|EMERGENTOLOGIA|NEUMOLOGIA|DIABETOLOGIA|MASTOLOGIA|HIPERTENSION|CLIMATERIO|ADICCIONES|ATENCION INTEGRAL", "salud_clinica"),
    (r"INFORMATIC|TECNOLOGIAS? DE LA INFORMACION|SISTEMAS|COMPUTACION|COMPUTADORAS|PROGRAMACION|PROGRAMADOR|SOFTWARE|BASE DE DATOS|CIBERSEGURIDAD|\bTICS?\b|INTELIGENCIA ARTIFICIAL|CIENCIA DE DATOS|ANALISIS DE DATOS|TELEMATICA|COMPUTER", "informatica"),
    (r"COMUNICACION|PERIODISMO|AUDIOVISUAL|\bRADIO\b|TELEVISION|LOCUCION", "comunicacion_medios"),
    (r"DISENO GRAFICO|DISENO PUBLICITARIO|ARTES GRAFICAS|DISENO WEB|DISENO MULTIMEDIA|ANIMACION", "diseno_grafico"),
    (r"DISENO DE MODA|DISENO DE MODAS|INDUMENTARIA|CONFECCION|\bMODA\b|TEXTIL", "diseno_moda_textil"),
    (r"MARKETING|MERCADOTECNIA|PUBLICIDAD|RELACIONES PUBLICAS|PROTOCOLO|COMERCIALIZACION|VENTAS", "marketing_publicidad"),
    (r"COMERCIO EXTERIOR|COMERCIO INTERNACIONAL|ADUANA|ADUANERA|LOGISTICA|NEGOCIOS INTERNACIONALES|IMPORTACION|EXPORTACION", "comercio_exterior_aduana"),
    (r"COOPERATIV", "cooperativas"),
    (r"BANCA|BANCARIA|FINANZAS|FINANCIERA|SEGUROS|MERCADO DE VALORES|CREDITO", "finanzas_banca"),
    (r"CONTABIL|CONTADUR|CONTADOR|AUDITORIA|IMPUESTOS|TRIBUTARI|TRIBUTACION|CIENCIAS CONTABLES|FISCAL", "contabilidad_auditoria"),
    (r"^ECONOMIA|ECONOMICAS|ECONOMETRIA|DESARROLLO LOCAL|DESARROLLO ECONOMICO|ESTADISTICA", "economia"),
    (r"DERECHO|NOTARIADO|ESCRIBANIA|ABOGACIA|\bABOGADO|JURIDIC|PROCESAL|PENAL|MEDIACION|CIENCIAS LEGALES|LEGISLACION|LEGISLATIV", "derecho_notariado"),
    (r"GOBERNABILIDAD|GESTION PUBLICA|ADMINISTRACION PUBLICA|ASUNTOS PUBLICOS|POLITICA|RELACIONES INTERNACIONALES|DIPLOMACIA|GERENCIA PUBLICA|GOBIERNO|PLANIFICACION Y CONDUCCION|ESTRATEGIC(A|O) NACIONAL|DESARROLLO MUNICIPAL|ADMINISTRACION MUNICIPAL|INTENDENCIA", "gestion_publica_politica"),
    (r"POLICIAL|MILITAR|SEGURIDAD|DEFENSA|CRIMINAL|FORENSE|INTELIGENCIA|PREVENCION|CRIMINOLOGIA|ARMADA|PENITENCIARI|PERICIA|OPERACIONES|DELITO", "seguridad_defensa"),
    (r"ALIMENTOS|AGROINDUSTRIA|AGROALIMENTARIA|INDUSTRIAS ALIMENTARIAS|FRIGORIFIC|LACTEOS|PANADERIA|REPOSTERIA|PASTELERIA|BROMATOLOGIA", "alimentos_agroindustria"),
    (r"FORESTAL|AGROFORESTAL|SILVICULTURA", "forestal"),
    (r"PESCA|ACUICOL|ACUICULTURA|PISCICULTURA", "pesca_acuicultura"),
    (r"QUIMICA INDUSTRIAL|INGENIERIA QUIMICA|PROCESOS QUIMICOS|PETROLEO|PETROQUIMICA|QUIMICA", "ingenieria_quimica"),
    (r"ELECTROMECANICA|ELECTRICIDAD|ELECTRICA|ELECTRICO|ELECTRICISTA|ELECTROTECNIA|INSTALACIONES ELECTRICAS|ENERGIA|ENERGETIC|ENERGIAS RENOVABLES", "electricidad_energia"),
    (r"ELECTRONICA|TELECOMUNICACION|\bREDES\b|AUTOMATIZACION|MECATRONICA INDUSTRIAL|ROBOTICA|INSTRUMENTACION INDUSTRIAL", "electronica_telecom"),
    (r"AUTOMOTRIZ|AUTOMOVIL|MOTORES|VEHICULOS", "automotriz"),
    (r"CUBIERTA|NAUTIC|NAVEGACION|MARINA|MARITIM|AERONAUTIC|AVIACION|PILOTO|PILOTAJE|FLUVIAL|PUERTO|^MAQUINAS$|TRANSPORTE|TRANSITO AEREO", "naval_transporte"),
    (r"MECANICA|MECATRONICA|MAQUINAS|METALMECANICA|SOLDADURA|MAQUINARIA|TORNERIA|MANTENIMIENTO|REFRIGERACION|CLIMATIZACION", "mecanica_industrial"),
    (r"INGENIERIA INDUSTRIAL|INGENIERIA EMPRESARIAL|TECNOLOGIA DE (LA )?PRODUCCION|PRODUCCION INDUSTRIAL|PROCESOS INDUSTRIALES|CALIDAD|INGENIERIA (DE|EN) PRODUCCION|HIGIENE Y SEGURIDAD|^PRODUCCION$", "ingenieria_industrial"),
    (r"MADERA|CARPINTERIA|MUEBLES|EBANISTERIA", "madera_muebles"),
    (r"ARQUITECTURA|URBANISMO|PAISAJISMO|DISENO DE INTERIORES|INTERIORES|DISENO INDUSTRIAL", "arquitectura"),
    (r"INGENIERIA CIVIL|CONSTRUCCION|OBRAS|EDIFICACIONES|HIDRAULICA|VIAL|CAMINOS|ESTRUCTURAS|MAESTRO MAYOR", "ingenieria_civil_construccion"),
    (r"TOPOGRAFIA|AGRIMENSURA|GEODESIA|GEOMATICA|CARTOGRAFIA|INFORMACION GEOGRAFICA|TELEDETECCION|GEOGRAFIA|GEOGRAFICA", "topografia_geomatica"),
    (r"AMBIENT|ECOLOGIA|RECURSOS NATURALES|RESIDUOS|SANEAMIENTO|HIDROLOGIA|CAMBIO CLIMATICO|SOSTENIBLE|SUSTENTABLE|CONSERVACION", "ambiental"),
    (r"GEOLOGIA|MINERIA|MINAS|MINERALES|HIDROGEOLOGIA", "geologia_mineria"),
    (r"TURISMO|AGENCIA DE VIAJE|\bGUIAS?\b", "turismo"),
    (r"HOTELERIA|GASTRONOMIA|COCINA|HOSTELERIA|BARTENDER|SOMMELIER", "hoteleria_gastronomia"),
    (r"ESTETICA|COSMETOLOGIA|PELUQUERIA|COSMIATRIA|BELLEZA|BARBERIA|MAQUILLAJE|\bSPA\b", "estetica_servicios_personales"),
    (r"BIBLIOTECOLOGIA|ARCHIVOLOGIA|BIBLIOTECA", "bibliotecologia"),
    (r"TEOLOGIA|RELIGIO|PASTORAL|CIENCIAS BIBLICAS", "teologia_religion"),
    (r"MUSICA|ARTES? (VISUALES|PLASTICAS|ESCENICAS)|^ARTES|TEATRO|DANZA|\bCINE\b|FOTOGRAFIA|\bCANTO\b", "artes_musica"),
    (r"ANTROPOLOGIA|SOCIOLOGIA|HISTORIA|FILOSOFIA|ARQUEOLOGIA|CIENCIAS SOCIALES|HUMANIDADES", "ciencias_sociales_humanidades"),
    (r"LENGUA|LETRAS|LITERATURA|INGLES|GUARANI|CASTELLANO|TERMINOLOGIA|LINGUISTIC|IDIOMA|TRADUCCION|PORTUGUES|FRANCES|ALEMAN", "idiomas_humanidades"),
    (r"ADMINISTRACION|ADMINISTRATIV|GERENCIA|GESTION EMPRESARIAL|DIRECCION|NEGOCIOS|EMPRESA|GESTION|ORGANIZACION|RECURSOS HUMANOS|TALENTO HUMANO|SECRETARIADO|EMPRENDEDOR|COMERCIAL|COMERCIO|LIDERAZGO|PLANIFICACION|PROYECTOS|CONSULTORIA", "administracion_empresas"),
    (r"MATEMATICA|FISICA|BIOLOGIA|CIENCIAS BASICAS|CIENCIAS NATURALES|INVESTIGACION|METODOLOGIA|TESIS|CIENCIA|ASTRONOMIA|BIOTECNOLOGIA|GENETICA|MICROBIOLOGIA|BIOLOGICAS|BIOMEDIC", "ciencias_basicas_investigacion"),
    (r"ESTUDIOS|CULTURA|SOCIAL", "ciencias_sociales_humanidades"),
]
REGLAS_COMPILADAS = [(re.compile(p), c) for p, c in REGLAS]
NIVELES = ("tecnico", "grado", "docente", "especializacion", "maestria", "doctorado", "otro")
GRADO_DOCTOR = {"DOCTOR EN ODONTOLOGIA", "DOCTORA EN ODONTOLOGIA", "DOCTOR A EN ODONTOLOGIA", "DOCTOR EN MEDICINA", "DOCTORA EN MEDICINA",
                "DOCTOR A EN MEDICINA", "DOCTOR EN CIENCIAS VETERINARIAS", "DOCTOR A EN CIENCIAS VETERINARIAS"}
INICIO_GRADO = ("LICENCIAD", "INGENIER", "ABOGAD", "MEDIC", "ODONTOLOG", "ARQUITECT", "CONTADOR", "BIOQUIMIC", "QUIMICO", "NOTARIO", "ESCRIBAN",
                "ECONOMISTA", "ADMINISTRADOR", "PSICOLOG", "NUTRICIONISTA", "ENFERMER", "VETERINAR", "AGRONOM", "TRABAJADOR", "BIBLIOTECOLOG", "FARMACEUTIC")


def limpiar(carrera: str) -> str:
    """Nombre de carrera normalizado y sin prefijos como «Especialización en» o «Técnico superior en»."""
    n = normalizar(carrera)
    return PREFIJOS.sub("", n)


def campo_de(carrera: str) -> tuple[str, str] | None:
    """Campo de estudio de la carrera y la regla (patrón) que lo asignó; None si ninguna regla coincide."""
    n = limpiar(carrera)
    for rx, campo in REGLAS_COMPILADAS:
        if rx.search(n):
            return campo, rx.pattern
    return None


def nivel_titulo(titulo: str) -> str:
    """Nivel del título según su texto: tecnico, grado, docente, especializacion, maestria, doctorado u otro."""
    t = normalizar(titulo)
    if t.startswith(("TECNICO DOCENTE", "PROFESOR")) or "HABILITACION PEDAGOGICA" in t:
        return "docente"
    if t.startswith("ESPECIALISTA") or "ESPECIALIZACION" in t:
        return "especializacion"
    if t.startswith(("MAGISTER", "MASTER")) or "MAESTRIA" in t:
        return "maestria"
    if t.startswith("DOCTOR"):
        return "grado" if t in GRADO_DOCTOR else "doctorado"
    if t.startswith(("TECNICO", "TECNOLOGO")):
        return "tecnico"
    if t.startswith(INICIO_GRADO):
        return "grado"
    return "otro"


def puente_carreras(conteos: pd.DataFrame) -> pd.DataFrame:
    """Una fila por carrera normalizada y sector (D27 final).

    Cuenta completa: cada título cuenta entero en cada sector del campo (peso 1); no se deben sumar los sectores entre sí.
    Las carreras transversales no van a ningún sector (sector_id vacío, tipo «transversal»): forman la base transversal y guardan en `sector_futuro` el
    sector de servicios al que irían si se mapean los servicios. Las que ninguna regla clasifica quedan «sin_clasificar».
    """
    t = conteos.assign(car=[normalizar(x) for x in conteos["carrera"]]).groupby("car")["titulos"].sum()
    filas = []
    for car, n in t.items():
        r = campo_de(car)
        if r is None:
            filas.append({"carrera": car, "campo": "sin_clasificar", "cine_f": "", "sector_id": "", "sector_futuro": "", "tipo": "sin_clasificar",
                          "n_sectores": 0, "peso": 1.0, "transversal": False, "confianza": "", "regla": "", "titulos": n})
            continue
        campo, patron = r
        cine, sectores, trans, conf = CAMPOS[campo]
        base = {"carrera": car, "campo": campo, "cine_f": cine, "transversal": trans, "confianza": conf, "regla": patron[:60], "titulos": n, "peso": 1.0}
        if trans:
            filas.append({**base, "sector_id": "", "sector_futuro": sectores[0], "tipo": "transversal", "n_sectores": 0})
        else:
            filas.extend({**base, "sector_id": s, "sector_futuro": "", "tipo": "sector", "n_sectores": len(sectores)} for s in sectores)
    return pd.DataFrame(filas)


def _base_carrera_nivel_institucion(conteos: pd.DataFrame) -> pd.DataFrame:
    """Títulos por carrera normalizada, nivel e institución normalizada (suma de todos los años y meses)."""
    base = conteos.assign(car=[normalizar(x) for x in conteos["carrera"]], nivel=[nivel_titulo(x) for x in conteos["titulo"]],
                          nom=[normalizar(x) for x in conteos["institucion"]])
    return base.groupby(["car", "nivel", "nom"], as_index=False)["titulos"].sum()


def _repartir_por_institucion(x: pd.DataFrame, pesos_inst: pd.DataFrame, claves: list[str]) -> pd.DataFrame:
    """Reparte `x` (con columna titulos y nom) entre los distritos de su institución, en los dos escenarios; lo no ubicado conserva distrito vacío."""
    pi = pesos_inst[["nom", "escenario", "departamento", "distrito", "unidad_2011", "peso", "confianza"]].rename(
        columns={"peso": "peso_inst", "confianza": "confianza_ubicacion"})
    ubic = x.merge(pi, on="nom", how="inner")
    ubic["t"] = ubic["titulos"] * ubic["peso_inst"]
    partes = [ubic.groupby(claves, as_index=False)["t"].sum()]
    sin = x.merge(pi[["nom"]].drop_duplicates(), on="nom", how="left", indicator=True)
    sin = sin[sin["_merge"] == "left_only"].drop(columns="_merge")
    for esc in ("principal", "parejo"):
        s = sin.assign(t=sin["titulos"], departamento="", distrito="", unidad_2011="", escenario=esc, confianza_ubicacion="sin_ubicar")
        partes.append(s.groupby(claves, as_index=False)["t"].sum())
    return pd.concat(partes, ignore_index=True).rename(columns={"t": "titulos"})


def titulos_sector_distrito(conteos: pd.DataFrame, puente: pd.DataFrame, pesos_inst: pd.DataFrame) -> pd.DataFrame:
    """Títulos por sector × distrito × nivel × escenario con cuenta completa: un título de un campo de varios sectores aparece entero en cada uno.

    Las filas con sector vacío son la base transversal y lo sin clasificar. No sumar entre sectores: para totales usar `titulos_distrito`.
    """
    pc = puente[["carrera", "sector_id", "tipo", "n_sectores", "transversal", "confianza"]].rename(columns={"carrera": "car", "confianza": "confianza_carrera"})
    x = _base_carrera_nivel_institucion(conteos).merge(pc, on="car", how="left")
    x["sector_id"] = x["sector_id"].fillna("")
    x["tipo"] = x["tipo"].fillna("sin_clasificar")
    x["n_sectores"] = x["n_sectores"].fillna(0).astype(int)
    x["transversal"] = x["transversal"].fillna(False).astype(bool)
    x["confianza_carrera"] = x["confianza_carrera"].fillna("")
    claves = ["sector_id", "tipo", "n_sectores", "departamento", "distrito", "unidad_2011", "escenario", "nivel", "transversal", "confianza_carrera", "confianza_ubicacion"]
    return _repartir_por_institucion(x, pesos_inst, claves)


def titulos_distrito(conteos: pd.DataFrame, puente: pd.DataFrame, pesos_inst: pd.DataFrame) -> pd.DataFrame:
    """Totales por distrito × nivel × escenario donde cada título cuenta UNA sola vez (suma el total de títulos en cada escenario)."""
    car = puente.drop_duplicates("carrera").set_index("carrera")[["transversal", "tipo"]]
    x = _base_carrera_nivel_institucion(conteos)
    x["transversal"] = x["car"].map(car["transversal"]).fillna(False).astype(bool)
    x["tipo"] = x["car"].map(car["tipo"]).map({"transversal": "transversal", "sin_clasificar": "sin_clasificar"}).fillna("sector")
    claves = ["departamento", "distrito", "unidad_2011", "escenario", "nivel", "tipo", "confianza_ubicacion"]
    return _repartir_por_institucion(x, pesos_inst, claves)


def control(puente: pd.DataFrame, totales: pd.DataFrame, total: int) -> str:
    """Resumen de cobertura: % de títulos clasificados por confianza y comprobación de que cada título cuenta una vez en la tabla de totales."""
    u = puente.drop_duplicates("carrera")
    clasif = u[u["campo"] != "sin_clasificar"]["titulos"].sum()
    conf = u[u["campo"] != "sin_clasificar"].groupby("confianza")["titulos"].sum() / total * 100
    cuadra = {esc: round(totales[totales["escenario"] == esc]["titulos"].sum()) for esc in ("principal", "parejo")}
    trans = u[u["tipo"] == "transversal"]["titulos"].sum() / total
    return (f"títulos {total:,} | carreras {len(u)} | clasificados {clasif / total:.1%} | base transversal {trans:.1%} | por confianza (% del total): "
            f"{conf.round(1).to_dict()} | suma de la tabla de totales por escenario: {cuadra}")


def main() -> None:
    conteos = pd.read_parquet(CONTEOS)
    puente = puente_carreras(conteos)
    puente.sort_values(["titulos", "carrera"], ascending=[False, True]).to_csv(SALIDA_PUENTE, index=False, encoding="utf-8")
    pesos = pd.read_csv(PESOS_INSTITUCION, dtype={"unidad_2011": str}).fillna("")
    final = titulos_sector_distrito(conteos, puente, pesos)
    exig = pd.read_csv(EXIGENCIA, dtype=str).fillna("")[["sector_id", "habilidades", "exige_formacion", "confianza", "cerca_del_corte"]]
    exig.columns = ["sector_id", "habilidades_nber", "exige_formacion", "confianza_exigencia", "cerca_del_corte"]
    final = final.merge(exig, on="sector_id", how="left").fillna({"exige_formacion": "", "habilidades_nber": "", "confianza_exigencia": "", "cerca_del_corte": ""})
    final.to_csv(SALIDA_SECTOR_DISTRITO, index=False, encoding="utf-8")
    totales = titulos_distrito(conteos, puente, pesos)
    totales.to_csv(SALIDA_TOTALES, index=False, encoding="utf-8")
    print(control(puente, totales, int(conteos["titulos"].sum())))
    sin = puente[puente["campo"] == "sin_clasificar"].sort_values("titulos", ascending=False)
    print("sin clasificar (30 con más títulos):")
    print(sin.head(30)[["carrera", "titulos"]].to_string(index=False))


if __name__ == "__main__":
    main()
