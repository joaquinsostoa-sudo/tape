"""Equivalencia de las clasificaciones sectoriales locales con CIIU Rev.4.

Unidad mínima ("átomo"): división CIIU Rev.4 de 2 dígitos, salvo la 01, que se parte en
`014` (producción pecuaria) y `01x` (resto), porque crédito y cuentas regionales separan la
ganadería de la agricultura. Cada categoría local se declara como lista de átomos con un nivel
de confianza. Es un BORRADOR para revisión del equipo (CLAUDE.md, regla 5).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]

_RANGOS = [(2, 3), (5, 9), (10, 33), (35, 39), (41, 43), (45, 47), (49, 53), (55, 56),
           (58, 63), (64, 66), (68, 68), (69, 75), (77, 82), (84, 84), (85, 85), (86, 88),
           (90, 93), (94, 96), (97, 98), (99, 99)]
_DIVISIONES = [f"{d:02d}" for a, b in _RANGOS for d in range(a, b + 1)]
# La CNAEP del BCP separa los alimentos (división 10) en seis actividades: por eso se parte en subátomos.
DIV10 = ["101", "104", "105", "106", "1071", "1072", "10o"]  # 10o = resto: 102, 103, 1073-1079, 108
ATOMOS: list[str] = ["01x", "014"] + [x for d in _DIVISIONES for x in (DIV10 if d == "10" else [d])]


@dataclass(frozen=True)
class Categoria:
    codigo: str
    nombre: str
    tipo: str  # actividad | residual | producto (CONSUMO, VIVIENDA e Impuestos se excluyen)
    atomos: str  # "10-12,45,01x"; "*" = todo lo no asignado en la clasificación
    confianza: str  # alta | media | baja
    notas: str = ""


def expandir(spec: str) -> list[str]:
    """Expande "10-12,45,014" a la lista de átomos; "*" y "" devuelven lista vacía."""
    salida: list[str] = []
    for tok in (t.strip() for t in spec.split(",")):
        if tok in ("", "*"):
            continue
        if "-" in tok:
            a, b = tok.split("-")
            salida += [f"{d:02d}" for d in range(int(a), int(b) + 1) if f"{d:02d}" in _DIVISIONES]
        else:
            salida.append(tok)
    salida = [x for t in salida for x in (DIV10 if t == "10" else [t])]
    desconocidos = set(salida) - set(ATOMOS)
    if desconocidos:
        raise ValueError(f"átomos inválidos: {sorted(desconocidos)}")
    return salida


C = Categoria
EPHC = [
    C("E1", "Agricultura, ganadería, caza y pesca", "actividad", "01x,014,02,03", "alta"),
    C("E2", "Industrias manufactureras", "actividad", "10-33", "alta"),
    C("E3", "Electricidad, gas y agua", "actividad", "35-39", "media", "incluye saneamiento (37-39)"),
    C("E4", "Construcciones", "actividad", "41-43", "alta"),
    C("E5", "Comercio, restaurantes y hoteles", "actividad", "45-47,55-56", "alta"),
    C("E6", "Transporte, almacenamiento y comunicaciones", "actividad", "49-53,61,79", "media",
      "61 telecomunicaciones; 79 agencias de viaje: supuesto"),
    C("E7", "Finanzas, seguros e inmuebles", "actividad", "64-66,68,62-63,69-75,77-78,80-82", "media",
      "agrupa servicios a empresas, como la CIIU Rev.2/3 (supuesto)"),
    C("E8", "Servicios comunales, sociales y personales", "actividad", "84-88,90-99,58-60", "media",
      "58-60 (edición, audiovisual, radiodifusión): supuesto, confianza baja"),
]  # minería (05-09) no tiene rama visible: queda SIN_GRUPO; verificar con el clasificador del INE

CREDITO = [
    C("K01", "ACTIVIDADES INMOBILIARIAS", "actividad", "68", "alta"),
    C("K02", "ADMINISTRACION PUBLICA", "actividad", "84", "alta"),
    C("K03", "AGRICULTURA", "actividad", "01x,02", "media", "incluye forestal: supuesto"),
    C("K04", "COMERCIO AL POR MAYOR", "actividad", "46", "alta"),
    C("K05", "COMERCIO AL POR MENOR", "actividad", "47,45", "media", "45 (vehículos): supuesto"),
    C("K06", "CONSTRUCCION", "actividad", "41-43", "alta"),
    C("K08", "GANADERIA", "actividad", "014", "media"),
    C("K09", "INDUSTRIA", "actividad", "10-33", "alta"),
    C("K10", "OTROS", "residual", "*", "baja", "residual: minería, utilities, pesca, etc. (verificar)"),
    C("K11", "SECTOR FINANCIERO", "actividad", "64-66", "alta"),
    C("K12", "SERVICIOS", "actividad", "49-53,55-56,58-63,69-75,77-82,85-88,90-98", "media"),
]

REGIONAL = [
    C("R1", "Agricultura", "actividad", "01x", "media", "supuesto: sin ganadería (la lista tiene Gan. aparte)"),
    C("R2", "Gan./Forestal/Pesca/Min.", "actividad", "014,02,03,05-09", "media"),
    C("R3", "Manufactura", "actividad", "10-33", "alta"),
    C("R4", "Electricidad y Agua", "actividad", "35-39", "media"),
    C("R5", "Construcción", "actividad", "41-43", "alta"),
    C("R6", "Servicios", "actividad", "45-99", "media", "todo lo demás"),
]

MIP = [
    C("M01", "Agricultura, ganadería, caza y pesca", "actividad", "01x,014,02,03", "alta"),
    C("M02", "Minería", "actividad", "05-09", "alta"),
    C("M03", "Alimentos, bebidas y tabacos", "actividad", "10-12", "alta"),
    C("M04", "Textiles, confecciones y calzado", "actividad", "13-15", "alta"),
    C("M05", "Madera, papel y cartón", "actividad", "16-18", "media", "18 impresión: supuesto"),
    C("M06", "Química, farmacia y caucho", "actividad", "19-22", "media", "19 refinación de petróleo: supuesto; 22 incluye plásticos"),
    C("M07", "Minerales no metálicos", "actividad", "23", "alta"),
    C("M08", "Hierro y acero", "actividad", "24", "media", "24 incluye metales no ferrosos (aluminio)"),
    C("M09", "Productos de metal", "actividad", "25", "alta"),
    C("M10", "Maquinaria, equipo y vehículos", "actividad", "26-30", "media"),
    C("M11", "Otras manufacturas y reparación", "actividad", "31-33", "media"),
    C("M12", "Electricidad, gas, y agua", "actividad", "35-39", "media"),
    C("M13", "Construcción", "actividad", "41-43", "alta"),
    C("M14", "Comercio al por mayor y menor", "actividad", "45-47", "alta"),
    C("M15", "Transporte", "actividad", "49-53", "alta"),
    C("M16", "Turismo (aloj., alimentación y recreación)", "actividad", "55-56,79,90-93", "media"),
    C("M17", "Telecomunicaciones, edición y servicios de info.", "actividad", "58-63", "alta"),
    C("M18", "Finanzas y seguros", "actividad", "64-66", "alta"),
    C("M19", "Servicios inmobiliarios", "actividad", "68", "alta"),
    C("M20", "Servicios a las empresas", "actividad", "69-75,77-78,80-82", "media"),
    C("M21", "Otros servicios", "actividad", "84-88,94-99", "media"),
]

# 33 actividades de las cuentas nacionales del BCP (CNAEP). Los ids siguen el orden del Excel
# (data/raw/bcp_cuentas_nacionales) y coinciden con `actividad_id` de pib_33_actividades.parquet.
# Es un MAPEO SUPUESTO por el nombre de cada actividad: falta la nota metodológica del BCP.
CNAEP33 = [
    C("N01", "Agricultura", "actividad", "01x", "alta"),
    C("N02", "Ganadería", "actividad", "014", "alta"),
    C("N03", "Forestal", "actividad", "02", "alta"),
    C("N04", "Pesca", "actividad", "03", "alta"),
    C("N05", "Minería", "actividad", "05-09", "alta"),
    C("N06", "Producción de carne", "actividad", "101", "alta"),
    C("N07", "Elaboración de aceites", "actividad", "104", "alta"),
    C("N08", "Producción de lácteos", "actividad", "105", "alta"),
    C("N09", "Producción de molinería y panadería", "actividad", "106,1071", "media",
      "supuesto: molinería (106) y panadería (1071)"),
    C("N10", "Producción de azúcar", "actividad", "1072", "alta"),
    C("N11", "Producción de otros alimentos", "actividad", "10o", "media",
      "supuesto: pescado, frutas, confitería, pastas, yerba, balanceados"),
    C("N12", "Producción de bebidas y tabaco", "actividad", "11,12", "alta"),
    C("N13", "Producción de textiles y prendas de vestir", "actividad", "13,14", "alta"),
    C("N14", "Producción de cuero y calzado", "actividad", "15", "alta"),
    C("N15", "Industria de la madera", "actividad", "16", "alta"),
    C("N16", "Producción de papel y productos del papel", "actividad", "17,18", "media", "18 impresión: supuesto"),
    C("N17", "Productos químicos", "actividad", "19-22", "media", "supuesto: incluye refinación, caucho y plásticos"),
    C("N18", "Minerales no metálicos", "actividad", "23", "alta"),
    C("N19", "Metales comunes", "actividad", "24", "alta"),
    C("N20", "Productos metálicos", "actividad", "25", "alta", "vale 0 de 1991 a 2007 (corte de serie)"),
    C("N21", "Maquinaria y equipo", "actividad", "26-30", "media", "supuesto: incluye electrónica y transporte"),
    C("N22", "Otras industrias manufactureras", "actividad", "31-33", "media", "supuesto: muebles, diversas, reparación"),
    C("N23", "Electricidad y agua", "actividad", "35-39", "media", "supuesto: incluye saneamiento y residuos"),
    C("N24", "Construcción", "actividad", "41-43", "alta"),
    C("N25", "Comercio", "actividad", "45-47", "alta"),
    C("N26", "Transporte", "actividad", "49-53", "media", "53 correos: supuesto"),
    C("N27", "Telecomunicaciones", "actividad", "61", "alta"),
    C("N28", "Intermediación financiera", "actividad", "64-66", "alta"),
    C("N29", "Servicios inmobiliarios", "actividad", "68", "alta"),
    C("N30", "Servicios a las empresas", "actividad", "58-60,62-63,69-75,77-82", "media",
      "supuesto: incluye informática, edición y agencias de viaje (79)"),
    C("N31", "Restaurantes y hoteles", "actividad", "55-56", "alta"),
    C("N32", "Servicios a los hogares", "actividad", "85-88,90-98", "baja",
      "privado: educación, salud y servicios personales (supuesto)"),
    C("N33", "Servicios gubernamentales", "actividad", "84-88", "baja",
      "administración pública y educación y salud públicas (supuesto): se solapa con N32 en 85-88"),
]
# Educación y salud (85-88) se reparten entre N32 (privado) y N33 (público): la CIIU no distingue
# la titularidad, así que esos átomos quedan en las dos categorías (único solapamiento permitido).
CNAEP_SOLAPE_PERMITIDO = {"85", "86", "87", "88"}

# Maquila: clasificación por rubro (producto), no anida con las demás; se mapea a divisiones/grupos.
MAQUILA = [
    C("Q01", "Autopartes", "producto", "29", "media", "los arneses pueden caer en 27 (cables) o 29"),
    C("Q02", "Confecciones y Textiles", "producto", "13-14", "alta"),
    C("Q03", "Bebidas y líquidos alcohólicos", "producto", "11", "alta", "solo en el gráfico de exportaciones"),
    C("Q04", "Aluminio y sus manufacturas", "producto", "24,25", "media"),
    C("Q05", "Productos quimicos y farmaceuticos", "producto", "20-21", "alta"),
    C("Q06", "Plásticos y sus manufacturas", "producto", "22", "alta"),
    C("Q07", "Productos alimenticios", "producto", "10", "alta"),
    C("Q08", "Servicios Intangibles", "producto", "62-63,82", "baja", "servicios (BPO, software): fuera del espacio producto"),
    C("Q09", "Madera y sus manufacturas", "producto", "16", "alta", "muebles (31) si corresponde"),
    C("Q10", "Metalúrgico y sus manufacturas", "producto", "24-25", "media"),
    C("Q11", "Alimentos para mascotas", "producto", "10", "alta", "CIIU 1080"),
    C("Q12", "Agroquímicos", "producto", "20", "alta", "CIIU 2021"),
    C("Q13", "Productos carnicos y sus derivados", "producto", "10", "alta", "CIIU 101"),
    C("Q14", "Domisanitarios", "producto", "20", "alta", "CIIU 2023"),
    C("Q15", "maquinaria y equipos", "producto", "28", "media"),
    C("Q16", "Calzados y sus partes", "producto", "15", "alta"),
    C("Q17", "Tabaco", "producto", "12", "alta"),
    C("Q18", "Electronica y electricidad", "producto", "26-27", "alta"),
    C("Q19", "Yerba mate y productos medicinales", "producto", "10,21", "baja", "mezcla alimento y fitoterápicos"),
    C("Q20", "Cueros y sus manufacturas", "producto", "15", "alta"),
    C("Q21", "Manufacturas diversas", "producto", "31-32", "baja"),
    C("Q22", "Preparados Solubles", "producto", "10", "media"),
    C("Q23", "Pigmento, pintura y colorantes", "producto", "20", "alta", "CIIU 2022"),
    C("Q24", "Joyas y articulos conexos", "producto", "32", "alta", "CIIU 3211"),
    C("Q25", "Articulos deportivos", "producto", "32", "alta", "CIIU 3230"),
    C("Q26", "Fabricación de productos de vidrio", "producto", "23", "alta", "CIIU 231"),
    C("Q27", "Plomo", "producto", "24", "baja", "metales no ferrosos; uso no aclarado"),
    C("Q28", "Otros", "residual", "*", "baja"),
]

# Mapa logístico MIC, pestaña INDUSTRIAS: sector > subsector (> sector específico, texto libre).
# Se mapea el subsector (73 pares). Los 1.744 "sectores específicos" quedan para una etapa posterior.
MIC_CSV = RAIZ / "data" / "raw" / "mic_mapa" / "industrias_sector_subsector_2026-10-08.csv"
_MIC: dict[str, tuple[str, str, str]] = {  # subsector -> (átomos, confianza, notas)
    "AGROINDUSTRIA GENERAL": ("01x,02,10", "baja", "mezcla producción primaria y procesamiento"),
    "APICULTURA Y MIEL": ("01x,10", "media", "CIIU 0149 y 1079"),
    "BALANCEADOS Y NUTRICION ANIMAL": ("10", "alta", "CIIU 1080"),
    "PRODUCCION PECUARIA Y GRANJAS": ("014", "alta"),
    "SILOS, ACOPIO Y GRANOS": ("01x,52", "media", "CIIU 0163 y 5210"),
    "TABACO Y DERIVADOS": ("12", "alta"),
    "ACEITES Y OLEAGINOSAS": ("10", "alta"),
    "ALIMENTOS PROCESADOS": ("10", "alta"),
    "AZUCAR, ALCOHOL Y CANA": ("10,11", "media", "azúcar 1072; alcohol 1101"),
    "BEBIDAS Y AGUA": ("11", "alta"),
    "EMBUTIDOS Y FIAMBRES": ("10", "alta", "CIIU 1010"),
    "ESENCIAS, AROMAS Y EXTRACTOS": ("10,20", "baja", "230 industrias; revisar qué son (¿yuyos/tereré?)"),
    "FRIGORIFICOS Y CARNICOS": ("10", "alta", "CIIU 1010"),
    "HELADOS": ("10", "alta", "CIIU 1050"),
    "HIELO Y AGUA": ("11,36", "media"),
    "LACTEOS": ("10", "alta", "CIIU 1050"),
    "MOLINERIA, HARINAS Y ALMIDONES": ("10", "alta", "CIIU 106"),
    "PANIFICADOS Y CONFITERIA": ("10", "alta", "CIIU 1071/1073; 1.671 industrias, en su mayoría panaderías"),
    "PASTAS Y FIDEOS": ("10", "alta", "CIIU 1074"),
    "YERBA MATE Y HIERBAS": ("10", "media", "CIIU 1079"),
    "ARTESANIA Y MANUALIDADES": ("13,16,32", "baja"),
    "FABRICA DE BALANCEADOS DE LA COOPERATIVA": ("10", "alta", "registro suelto: sector mal cargado"),
    "ELECTRICIDAD Y ELECTRONICA": ("26,27", "media"),
    "REFRIGERACION Y CLIMATIZACION": ("28,43", "media"),
    "CARBON, LENA Y COMBUSTIBLES SOLIDOS": ("02,19", "baja"),
    "COMBUSTIBLES Y LUBRICANTES": ("19,47", "baja", "puede incluir estaciones de servicio (47)"),
    "ASERRADEROS Y MADERA ASERRADA": ("16", "alta", "CIIU 1610"),
    "CAJAS, ENVASES Y EMBALAJES DE MADERA": ("16", "alta"),
    "CARPINTERIA Y EBANISTERIA": ("16,31", "media", "carpintería 1622 y muebles 3100"),
    "MUEBLES Y MOBILIARIO": ("31", "alta"),
    "PRODUCTOS DE MADERA": ("16", "alta"),
    "BASCULAS Y BALANZAS": ("28", "alta"),
    "MAQUINARIA, EQUIPOS Y REPUESTOS": ("28,29,33", "media"),
    "ALUMINIO Y ABERTURAS": ("25", "media", "aberturas 2511"),
    "ASTILLEROS Y EMBARCACIONES": ("30", "alta", "CIIU 3011"),
    "HERRERIA Y ESTRUCTURAS METALICAS": ("25", "alta", "CIIU 2511/2599; 2.250 industrias"),
    "HOJALATERIA Y CHAPERIA": ("25,45", "media", "chapería de vehículos 4520"),
    "METALURGIA Y FUNDICION": ("24", "alta"),
    "METALURGIA Y METALMECANICA": ("24,25", "media"),
    "PRODUCTOS METALICOS": ("25", "alta"),
    "TORNERIA Y MECANIZADO": ("25", "alta", "CIIU 2592"),
    "BALDOSAS, MARMOL Y REVESTIMIENTOS": ("23", "alta"),
    "CAL Y DERIVADOS": ("23", "alta"),
    "CANTERAS Y ARIDOS": ("08", "alta", "es minería (sección B), no manufactura"),
    "CEMENTO, YESO Y AFINES": ("23", "alta"),
    "CERAMICA, LADRILLOS Y OLERIA": ("23", "alta", "2.944 industrias, en su mayoría olerías"),
    "MATERIALES DE CONSTRUCCION": ("23", "media"),
    "PREFABRICADOS Y HORMIGON": ("23", "alta"),
    "VIDRIO Y VIDRIERIA": ("23", "alta", "vidrierías pueden ser comercio/servicio"),
    "FABRICA Y VENTA DE MOBILIARIO DE METAL Y CARPINTERIA": ("25,31", "media", "registro suelto"),
    "INDUSTRIA GENERAL Y MULTIACTIVIDAD": ("10-33", "baja", "no asignable a un sector"),
    "OTROS INDUSTRIALES": ("10-33", "baja", "no asignable a un sector"),
    "GRAFICA, IMPRENTA Y SENALETICA": ("18", "alta"),
    "PAPEL, CARTON Y EMBALAJES": ("17", "alta"),
    "BOLSAS Y ENVASES PLASTICOS": ("22", "alta"),
    "CAUCHO Y GOMA": ("22", "alta"),
    "PLASTICOS Y ENVASES": ("22", "alta"),
    "AGROQUIMICOS Y FERTILIZANTES": ("20", "alta"),
    "COSMETICA Y PERFUMERIA": ("20", "alta"),
    "PINTURAS Y RECUBRIMIENTOS": ("20", "alta"),
    "PRODUCTOS DE LIMPIEZA": ("20", "alta"),
    "QUIMICOS, FARMACIA Y LABORATORIO": ("20,21", "media"),
    "RECICLAJE DE PAPEL Y CARTON": ("38", "alta"),
    "RECICLAJE DE PLASTICOS": ("38", "alta"),
    "RECICLAJE GENERAL": ("38", "alta"),
    "RECICLAJE METALICO": ("38", "alta"),
    "SERVICIOS INDUSTRIALES Y MANTENIMIENTO": ("33", "media", "reparación 33; puede incluir 43"),
    "CALZADOS": ("15", "alta"),
    "COLCHONES, TAPICERIA Y HOGAR": ("13,31,95", "baja"),
    "CONFECCION E INDUMENTARIA": ("14", "alta"),
    "CUERO Y MARROQUINERIA": ("15", "alta"),
    "TEXTILES Y TEJIDOS": ("13", "alta"),
    "FABRICA DE HAMACAS Y COLCHAS DE LA COOPERATIVA": ("13", "alta", "registro suelto: sector mal cargado"),
}


def mic_categorias(ruta: Path = MIC_CSV) -> list[Categoria]:
    """Subsectores del mapa MIC como categorías, con los átomos de `_MIC`."""
    df = pd.read_csv(ruta, dtype=str)
    cats = []
    for i, f in enumerate(df.itertuples(index=False), start=1):
        atomos, conf, *nota = _MIC[f.subsector]
        cats.append(Categoria(f"I{i:02d}", f"{f.sector} > {f.subsector}", "producto", atomos, conf,
                              (nota[0] if nota else "") + f" [n={f.n_industrias}]"))
    return cats


CLASIFICACIONES: dict[str, list[Categoria]] = {
    "ephc": EPHC, "credito": CREDITO, "regional": REGIONAL, "mip": MIP, "maquila": MAQUILA,
    "mic_mapa": mic_categorias(), "cnaep33": CNAEP33,
}
ANIDAN = ["ephc", "credito", "regional", "mip"]  # clasificaciones por actividad, sin solapes
GRUPOS = ANIDAN + ["cnaep33"]  # las que cada sector TAPE hereda (cnaep33 con el solape de 85-88)
SIN_GRUPO = "SIN_GRUPO"


def atomo_a_categoria(categorias: list[Categoria]) -> dict[str, list[str]]:
    """Asigna cada átomo a las categorías que lo reclaman; el residual recoge lo no asignado."""
    mapa: dict[str, list[str]] = {a: [] for a in ATOMOS}
    residual = next((c.codigo for c in categorias if c.atomos == "*"), None)
    for c in categorias:
        for a in expandir(c.atomos):
            mapa[a].append(c.codigo)
    for a, cs in mapa.items():
        if not cs and residual:
            cs.append(residual)
    return mapa


def tabla_equivalencias() -> pd.DataFrame:
    """Una fila por (clasificación, categoría) con sus átomos CIIU Rev.4 y la confianza."""
    filas = [
        {"clasificacion": k, "codigo": c.codigo, "nombre": c.nombre, "tipo": c.tipo,
         "ciiu4_atomos": c.atomos, "confianza": c.confianza, "notas": c.notas}
        for k, cats in CLASIFICACIONES.items() for c in cats
    ]
    return pd.DataFrame(filas)


def tabla_atomos() -> pd.DataFrame:
    """Una fila por átomo con su categoría en cada clasificación que anida, y la firma común."""
    cols: dict[str, dict[str, str]] = {}
    for k in GRUPOS:
        mapa = atomo_a_categoria(CLASIFICACIONES[k])
        cols[k] = {a: "+".join(cs) if cs else SIN_GRUPO for a, cs in mapa.items()}
    df = pd.DataFrame(cols).rename_axis("atomo").reset_index()
    df["firma"] = df[GRUPOS].agg("|".join, axis=1)
    df["bloque_minimo"] = df["firma"].astype("category").cat.codes + 1
    return df


def main() -> None:
    salida = RAIZ / "data" / "clean"
    tabla_equivalencias().to_csv(salida / "clasificaciones_locales_ciiu.csv", index=False, encoding="utf-8")
    at = tabla_atomos()
    at.to_csv(salida / "ciiu4_atomos_clasificaciones.csv", index=False, encoding="utf-8")
    print(f"átomos: {len(at)}; bloques mínimos comunes: {at['bloque_minimo'].nunique()}")


if __name__ == "__main__":
    main()
