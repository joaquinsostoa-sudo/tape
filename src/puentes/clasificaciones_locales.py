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
ATOMOS: list[str] = ["01x", "014"] + [f"{d:02d}" for a, b in _RANGOS for d in range(a, b + 1)]


@dataclass(frozen=True)
class Categoria:
    codigo: str
    nombre: str
    tipo: str  # actividad | finalidad | impuestos | residual | producto
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
            salida += [f"{d:02d}" for d in range(int(a), int(b) + 1) if f"{d:02d}" in ATOMOS]
        else:
            salida.append(tok)
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
    C("K06", "CONSTRUCCION", "actividad", "41-43", "alta", "puede solapar con VIVIENDA (finalidad)"),
    C("K07", "CONSUMO", "finalidad", "", "alta", "crédito a hogares; no es actividad CIIU"),
    C("K08", "GANADERIA", "actividad", "014", "media"),
    C("K09", "INDUSTRIA", "actividad", "10-33", "alta"),
    C("K10", "OTROS", "residual", "*", "baja", "residual: minería, utilities, pesca, etc. (verificar)"),
    C("K11", "SECTOR FINANCIERO", "actividad", "64-66", "alta"),
    C("K12", "SERVICIOS", "actividad", "49-53,55-56,58-63,69-75,77-82,85-88,90-98", "media"),
    C("K13", "VIVIENDA", "finalidad", "", "alta", "crédito hipotecario/vivienda; no es actividad CIIU"),
]

REGIONAL = [
    C("R1", "Agricultura", "actividad", "01x", "media", "supuesto: sin ganadería (la lista tiene Gan. aparte)"),
    C("R2", "Gan./Forestal/Pesca/Min.", "actividad", "014,02,03,05-09", "media"),
    C("R3", "Manufactura", "actividad", "10-33", "alta"),
    C("R4", "Electricidad y Agua", "actividad", "35-39", "media"),
    C("R5", "Construcción", "actividad", "41-43", "alta"),
    C("R6", "Servicios", "actividad", "45-99", "media", "todo lo demás"),
    C("R7", "Impuestos", "impuestos", "", "alta",
      "impuestos netos de subvenciones; aparece en la imagen, no en el texto del documento"),
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

CLASIFICACIONES: dict[str, list[Categoria]] = {
    "ephc": EPHC, "credito": CREDITO, "regional": REGIONAL, "mip": MIP, "maquila": MAQUILA,
}
ANIDAN = ["ephc", "credito", "regional", "mip"]  # clasificaciones por actividad
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
    for k in ANIDAN:
        mapa = atomo_a_categoria(CLASIFICACIONES[k])
        cols[k] = {a: "+".join(cs) if cs else SIN_GRUPO for a, cs in mapa.items()}
    df = pd.DataFrame(cols).rename_axis("atomo").reset_index()
    df["firma"] = df[ANIDAN].agg("|".join, axis=1)
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
