"""Borrador de la taxonomía de sectores TAPE, construida sobre CIIU Rev.4 (decisión D9).

Cada sector es una lista de prefijos CIIU Rev.4 (división de 2 dígitos, grupo de 3 o clase de 4).
Restricciones de diseño (comprobadas en tests):
  1. Cada clase CIIU Rev.4 de las secciones A-S cae en exactamente un sector.
  2. Ningún sector cruza los grupos de EPHC, crédito BCP, cuentas regionales ni MIP, es decir,
     cada sector "hereda" un único grupo de cada clasificación (regla de CLAUDE.md).
Es un BORRADOR para aprobación del equipo; las columnas de grupos usan los mapeos supuestos de
`clasificaciones_locales.py`. Falta la clasificación de 33 actividades CNAEP del BCP.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .clasificaciones_locales import ANIDAN, CLASIFICACIONES, atomo_a_categoria

RAIZ = Path(__file__).resolve().parents[2]
ISIC4_CLASES = RAIZ / "data" / "raw" / "concordancias" / "unsd" / "isic4-cpc21.txt"
EXCLUIDAS = ("99",)  # organizaciones extraterritoriales: sin sentido para Paraguay


@dataclass(frozen=True)
class Sector:
    id: str
    nombre: str
    seccion: str  # sección CIIU Rev.4 (A-S)
    ciiu4: str  # prefijos separados por coma
    comercio: bool  # produce bienes con código HS (entra al espacio producto)
    confianza: str  # alta | media | baja: qué tan bien corta la CIIU esta actividad
    notas: str = ""


S = Sector
SECTORES: list[Sector] = [
    # --- Agropecuario, forestal, pesca y minería (A, B)
    S("S01", "Cultivos anuales (soja, maíz, trigo, arroz, caña, algodón, hortalizas)", "A", "011", True, "alta",
      "núcleo exportador de Paraguay"),
    S("S02", "Cultivos perennes y viveros", "A", "012,013", True, "alta"),
    S("S03", "Ganadería bovina y otras especies", "A", "0141,0142,0143,0144,0149", True, "alta",
      "0149 incluye apicultura"),
    S("S04", "Avicultura y porcicultura", "A", "0145,0146", True, "alta"),
    S("S05", "Servicios agropecuarios y poscosecha (silos, acopio)", "A", "015,016,017", False, "media",
      "015 (mixta) se agrupa aquí porque no se puede separar de la agricultura"),
    S("S06", "Silvicultura y extracción de madera", "A", "02", True, "alta"),
    S("S07", "Pesca y acuicultura", "A", "03", True, "alta"),
    S("S08", "Minería y canteras", "B", "05,06,07,08,09", True, "media",
      "en Paraguay es sobre todo canteras y áridos (08)"),
    # --- Alimentos y bebidas (C10-C12)
    S("S09", "Frigoríficos y productos cárnicos", "C", "101", True, "alta", "carne bovina"),
    S("S10", "Lácteos", "C", "105", True, "alta"),
    S("S11", "Aceites y oleaginosas", "C", "104", True, "alta", "molienda de soja"),
    S("S12", "Molinería y almidones", "C", "106", True, "alta"),
    S("S13", "Panificados, confitería y pastas", "C", "1071,1073,1074", True, "alta"),
    S("S14", "Frutas, hortalizas y pescado procesados", "C", "102,103", True, "alta"),
    S("S15", "Azúcar y alcohol", "C", "1072,1101", True, "media", "1101 incluye alcohol; ver nota de biocombustibles"),
    S("S16", "Yerba mate, hierbas y otros alimentos", "C", "1075,1079", True, "media"),
    S("S17", "Alimentos balanceados y para mascotas", "C", "108", True, "alta"),
    S("S18", "Bebidas y agua envasada", "C", "1102,1103,1104", True, "alta"),
    S("S19", "Tabaco", "C", "12", True, "alta"),
    # --- Textil, cuero, madera, papel, muebles
    S("S20", "Textiles e hilandería", "C", "13", True, "alta"),
    S("S21", "Confecciones", "C", "14", True, "alta", "maquila"),
    S("S22", "Cuero y calzado", "C", "15", True, "alta"),
    S("S23", "Aserrado y productos de madera", "C", "16", True, "alta"),
    S("S24", "Muebles", "C", "31", True, "alta"),
    S("S25", "Papel y cartón", "C", "17", True, "alta"),
    S("S26", "Impresión y reproducción", "C", "18", False, "alta", "mayormente servicios; poco comercio"),
    # --- Química, caucho y plásticos, no metálicos
    S("S27", "Petróleo refinado y combustibles", "C", "19", True, "media",
      "los biocombustibles (biodiésel, bioetanol) no tienen clase CIIU propia: ver docs/taxonomia.md"),
    S("S28", "Químicos básicos, fertilizantes y agroquímicos", "C", "201,2021,203", True, "alta"),
    S("S29", "Pinturas, limpieza y cosmética", "C", "2022,2023,2029", True, "alta"),
    S("S30", "Farmacéutica", "C", "21", True, "alta"),
    S("S31", "Caucho y plásticos", "C", "22", True, "alta", "maquila de plásticos"),
    S("S32", "Cemento, hormigón y prefabricados", "C", "2394,2395", True, "alta"),
    S("S33", "Cerámica y ladrillos", "C", "2391,2392,2393", True, "alta", "olerías"),
    S("S34", "Vidrio, piedra y otros minerales no metálicos", "C", "231,2396,2399", True, "alta"),
    # --- Metales, maquinaria, equipos y transporte
    S("S35", "Siderurgia y fundición", "C", "241,243", True, "alta"),
    S("S36", "Metales no ferrosos y aluminio", "C", "242", True, "alta", "maquila de aluminio"),
    S("S37", "Productos de metal y estructuras (herrería, mecanizado)", "C", "25", True, "alta"),
    S("S38", "Maquinaria y equipo", "C", "28", True, "alta"),
    S("S39", "Electrónica y equipo eléctrico (incluye cables)", "C", "26,27", True, "media",
      "los arneses pueden clasificarse en 27 o en 29: ver docs/taxonomia.md"),
    S("S40", "Autopartes y vehículos", "C", "29", True, "alta", "maquila de autopartes"),
    S("S41", "Otro equipo de transporte y astilleros", "C", "30", True, "alta"),
    S("S42", "Joyería, deportes y manufacturas diversas", "C", "32", True, "alta"),
    S("S43", "Reparación e instalación de maquinaria", "C", "33", False, "alta"),
    # --- Energía, agua, residuos, construcción
    S("S44", "Electricidad, gas y vapor", "D", "35", False, "alta",
      "la exportación de energía eléctrica (HS 271600) se excluye del comercio"),
    S("S45", "Agua, saneamiento y remediación", "E", "36,37,39", False, "alta"),
    S("S46", "Gestión de residuos y reciclaje", "E", "38", False, "alta"),
    S("S47", "Construcción", "F", "41,42,43", False, "alta"),
    # --- Comercio y transporte
    S("S48", "Comercio mayorista", "G", "46", False, "alta"),
    S("S49", "Comercio minorista y de vehículos", "G", "45,47", False, "alta"),
    S("S50", "Transporte terrestre y por tuberías", "H", "49", False, "alta"),
    S("S51", "Transporte acuático y aéreo", "H", "50,51", False, "alta", "hidrovía"),
    S("S52", "Almacenamiento, logística y correos", "H", "52,53", False, "alta"),
    # --- Servicios
    S("S53", "Alojamiento y gastronomía", "I", "55,56", False, "alta"),
    S("S54", "Agencias de viaje y turismo", "N", "79", False, "alta",
      "separado de S53 porque EPHC lo agrupa en otra rama"),
    S("S55", "Telecomunicaciones", "J", "61", False, "alta"),
    S("S56", "Software, informática y servicios de información", "J", "62,63", False, "alta"),
    S("S57", "Edición, audiovisual y medios", "J", "58,59,60", False, "media"),
    S("S58", "Finanzas y seguros", "K", "64,65,66", False, "alta"),
    S("S59", "Servicios inmobiliarios", "L", "68", False, "alta"),
    S("S60", "Servicios profesionales, científicos y técnicos", "M", "69,70,71,72,73,74,75", False, "alta"),
    S("S61", "Servicios administrativos y de apoyo a empresas", "N", "77,78,80,81,82", False, "alta"),
    S("S62", "Administración pública y defensa", "O", "84", False, "alta"),
    S("S63", "Educación", "P", "85", False, "alta"),
    S("S64", "Salud y asistencia social", "Q", "86,87,88", False, "alta"),
    S("S65", "Arte, recreación y deportes", "R", "90,91,92,93", False, "alta"),
    S("S66", "Otros servicios personales y de reparación", "S", "94,95,96,97,98", False, "media"),
]


def prefijos(sector: Sector) -> list[str]:
    return [p.strip() for p in sector.ciiu4.split(",")]


def atomo_de(prefijo: str) -> str:
    """Átomo de `clasificaciones_locales` al que pertenece un prefijo CIIU."""
    if prefijo.startswith("014"):
        return "014"
    return "01x" if prefijo.startswith("01") else prefijo[:2]


def atomos_de_sector(sector: Sector) -> list[str]:
    return sorted({atomo_de(p) for p in prefijos(sector)})


def clases_ciiu4(ruta: Path = ISIC4_CLASES) -> list[str]:
    """Clases CIIU Rev.4 (4 dígitos) de la tabla oficial de la ONU."""
    return sorted(pd.read_csv(ruta, dtype=str)["ISIC4code"].unique())


def sectores_de_clase(clase: str) -> list[str]:
    return [s.id for s in SECTORES if any(clase.startswith(p) for p in prefijos(s))]


def grupos_de_sector(sector: Sector) -> dict[str, str]:
    """Grupo de cada clasificación por actividad al que pertenece el sector ('+' si cruza varios)."""
    out = {}
    for k in ANIDAN:
        mapa = atomo_a_categoria(CLASIFICACIONES[k])
        grupos = sorted({g for a in atomos_de_sector(sector) for g in (mapa[a] or ["SIN_GRUPO"])})
        out[k] = "+".join(grupos)
    return out


def tabla_taxonomia() -> pd.DataFrame:
    filas = []
    for s in SECTORES:
        filas.append({
            "sector_id": s.id, "nombre": s.nombre, "seccion_ciiu": s.seccion, "ciiu4": s.ciiu4,
            "atomos": ",".join(atomos_de_sector(s)), "entra_en_comercio": s.comercio,
            "confianza": s.confianza, **{f"grupo_{k}": v for k, v in grupos_de_sector(s).items()},
            "grupo_cnaep33": "", "notas": s.notas,
        })
    return pd.DataFrame(filas)


def main() -> None:
    df = tabla_taxonomia()
    df.to_csv(RAIZ / "data" / "clean" / "taxonomia_sectores_tape.csv", index=False, encoding="utf-8")
    print(f"{len(df)} sectores; con comercio: {int(df['entra_en_comercio'].sum())}")


if __name__ == "__main__":
    main()
