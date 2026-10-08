"""Borrador de la taxonomía de sectores TAPE, construida sobre CIIU Rev.4 (decisión D9).

Cada sector es una lista de prefijos CIIU Rev.4 (división de 2 dígitos, grupo de 3 o clase de 4).
Restricciones de diseño (comprobadas en tests):
  1. Cada clase CIIU Rev.4 de las secciones A-S cae en exactamente un sector.
  2. Ningún sector cruza los grupos de EPHC, crédito BCP, cuentas regionales, MIP ni las 33
     actividades del BCP: cada sector "hereda" un único grupo de cada clasificación (regla de
     CLAUDE.md). Única excepción: educación y salud en las 33 actividades del BCP, que reparte entre
     servicios a los hogares (privado) y gubernamentales (público); la CIIU no distingue titularidad.
Es un BORRADOR para aprobación del equipo; los grupos usan los mapeos supuestos de
`clasificaciones_locales.py`. Los ids se asignan por orden: si se inserta un sector, se renumeran.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

import pandas as pd

from .clasificaciones_locales import CLASIFICACIONES, GRUPOS, atomo_a_categoria

RAIZ = Path(__file__).resolve().parents[2]
ISIC4_CLASES = RAIZ / "data" / "raw" / "concordancias" / "unsd" / "isic4-cpc21.txt"
EXCLUIDAS = ("99",)  # organizaciones extraterritoriales: sin sentido para Paraguay
MIXTOS_PUBLICO_PRIVADO = {"85", "86,87,88"}  # sectores que cruzan N32+N33 del BCP por titularidad


@dataclass(frozen=True)
class Sector:
    nombre: str
    seccion: str  # sección CIIU Rev.4 (A-S)
    ciiu4: str  # prefijos separados por coma
    comercio: bool  # produce bienes con código HS (entra al espacio producto)
    confianza: str  # alta | media | baja: qué tan bien corta la CIIU esta actividad
    notas: str = ""
    id: str = ""


S = Sector
_BORRADOR: list[Sector] = [
    # --- Agropecuario, forestal, pesca y minería (A, B)
    S("Cultivos anuales (soja, maíz, trigo, arroz, caña, algodón, hortalizas)", "A", "011", True, "alta",
      "núcleo exportador de Paraguay"),
    S("Cultivos perennes y viveros", "A", "012,013", True, "alta"),
    S("Ganadería bovina y otras especies", "A", "0141,0142,0143,0144,0149", True, "alta",
      "0149 incluye apicultura"),
    S("Avicultura y porcicultura", "A", "0145,0146", True, "alta"),
    S("Servicios agropecuarios y poscosecha (silos, acopio)", "A", "015,016,017", False, "media",
      "015 (mixta) se agrupa aquí porque no se puede separar de la agricultura"),
    S("Silvicultura y extracción de madera", "A", "02", True, "alta"),
    S("Pesca y acuicultura", "A", "03", True, "alta"),
    S("Minería y canteras", "B", "05,06,07,08,09", True, "media",
      "en Paraguay es sobre todo canteras y áridos (08)"),
    # --- Alimentos y bebidas (C10-C12). La división 10 se parte como la CNAEP del BCP.
    S("Frigoríficos y productos cárnicos", "C", "101", True, "alta", "carne bovina"),
    S("Lácteos", "C", "105", True, "alta"),
    S("Aceites y oleaginosas", "C", "104", True, "alta", "molienda de soja"),
    S("Molinería y almidones", "C", "106", True, "alta"),
    S("Panificados", "C", "1071", True, "alta"),
    S("Confitería y pastas", "C", "1073,1074", True, "alta",
      "separado de panificados porque el BCP los pone en actividades distintas"),
    S("Frutas, hortalizas y pescado procesados", "C", "102,103", True, "alta"),
    S("Azúcar", "C", "1072", True, "alta"),
    S("Yerba mate, hierbas y otros alimentos", "C", "1075,1079", True, "media"),
    S("Alimentos balanceados y para mascotas", "C", "108", True, "alta"),
    S("Bebidas, alcohol y agua envasada", "C", "1101,1102,1103,1104", True, "alta",
      "1101 incluye alcohol etílico; los biocombustibles se identifican por producto HS"),
    S("Tabaco", "C", "12", True, "alta"),
    # --- Textil, cuero, madera, papel, muebles
    S("Textiles e hilandería", "C", "13", True, "alta"),
    S("Confecciones", "C", "14", True, "alta", "maquila"),
    S("Cuero y calzado", "C", "15", True, "alta"),
    S("Aserrado y productos de madera", "C", "16", True, "alta"),
    S("Muebles", "C", "31", True, "alta"),
    S("Papel y cartón", "C", "17", True, "alta"),
    S("Impresión y reproducción", "C", "18", False, "alta", "mayormente servicios; poco comercio"),
    # --- Química, caucho y plásticos, no metálicos
    S("Petróleo refinado y combustibles", "C", "19", True, "media",
      "los biocombustibles no tienen clase CIIU propia: se identifican por producto HS (ver docs/taxonomia.md)"),
    S("Químicos básicos, fertilizantes y agroquímicos", "C", "201,2021,203", True, "alta"),
    S("Pinturas, limpieza y cosmética", "C", "2022,2023,2029", True, "alta"),
    S("Farmacéutica", "C", "21", True, "alta"),
    S("Caucho y plásticos", "C", "22", True, "alta", "maquila de plásticos"),
    S("Cemento, hormigón y prefabricados", "C", "2394,2395", True, "alta"),
    S("Cerámica y ladrillos", "C", "2391,2392,2393", True, "alta", "olerías"),
    S("Vidrio, piedra y otros minerales no metálicos", "C", "231,2396,2399", True, "alta"),
    # --- Metales, maquinaria, equipos y transporte
    S("Siderurgia y fundición", "C", "241,243", True, "alta"),
    S("Metales no ferrosos y aluminio", "C", "242", True, "alta", "maquila de aluminio"),
    S("Productos de metal y estructuras (herrería, mecanizado)", "C", "25", True, "alta"),
    S("Maquinaria y equipo", "C", "28", True, "alta"),
    S("Electrónica y equipo eléctrico (incluye cables)", "C", "26,27", True, "media",
      "los arneses de maquila se asignan a Autopartes y vehículos por producto HS"),
    S("Autopartes y vehículos", "C", "29", True, "alta", "maquila de autopartes; incluye los arneses"),
    S("Otro equipo de transporte y astilleros", "C", "30", True, "alta"),
    S("Joyería, deportes y manufacturas diversas", "C", "32", True, "alta"),
    S("Reparación e instalación de maquinaria", "C", "33", False, "alta"),
    # --- Energía, agua, residuos, construcción
    S("Electricidad, gas y vapor", "D", "35", False, "alta",
      "la exportación de energía eléctrica (HS 271600) se excluye del comercio"),
    S("Agua, saneamiento y remediación", "E", "36,37,39", False, "alta"),
    S("Gestión de residuos y reciclaje", "E", "38", False, "alta"),
    S("Construcción", "F", "41,42,43", False, "alta"),
    # --- Comercio y transporte
    S("Comercio mayorista", "G", "46", False, "alta"),
    S("Comercio minorista y de vehículos", "G", "45,47", False, "alta"),
    S("Transporte terrestre y por tuberías", "H", "49", False, "alta"),
    S("Transporte acuático y aéreo", "H", "50,51", False, "alta", "hidrovía"),
    S("Almacenamiento, logística y correos", "H", "52,53", False, "alta"),
    # --- Servicios
    S("Alojamiento y gastronomía", "I", "55,56", False, "alta"),
    S("Agencias de viaje y turismo", "N", "79", False, "alta",
      "separado de alojamiento porque EPHC lo agrupa en otra rama"),
    S("Telecomunicaciones", "J", "61", False, "alta"),
    S("Software, informática y servicios de información", "J", "62,63", False, "alta"),
    S("Edición, audiovisual y medios", "J", "58,59,60", False, "media"),
    S("Finanzas y seguros", "K", "64,65,66", False, "alta"),
    S("Servicios inmobiliarios", "L", "68", False, "alta"),
    S("Servicios profesionales, científicos y técnicos", "M", "69,70,71,72,73,74,75", False, "alta"),
    S("Servicios administrativos y de apoyo a empresas", "N", "77,78,80,81,82", False, "alta"),
    S("Administración pública y defensa", "O", "84", False, "alta"),
    S("Educación", "P", "85", False, "alta", "público y privado: reparte entre N32 y N33 del BCP"),
    S("Salud y asistencia social", "Q", "86,87,88", False, "alta", "público y privado: reparte entre N32 y N33 del BCP"),
    S("Arte, recreación y deportes", "R", "90,91,92,93", False, "alta"),
    S("Otros servicios personales y de reparación", "S", "94,95,96,97,98", False, "media"),
]
SECTORES: list[Sector] = [replace(s, id=f"S{i:02d}") for i, s in enumerate(_BORRADOR, start=1)]


def prefijos(sector: Sector) -> list[str]:
    return [p.strip() for p in sector.ciiu4.split(",")]


def atomo_de(prefijo: str) -> str:
    """Átomo de `clasificaciones_locales` al que pertenece un prefijo CIIU."""
    if prefijo.startswith("014"):
        return "014"
    if prefijo.startswith("01"):
        return "01x"
    if prefijo.startswith("10"):
        return next((a for a in ("1071", "1072", "101", "104", "105", "106") if prefijo.startswith(a)), "10o")
    return prefijo[:2]


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
    for k in GRUPOS:
        mapa = atomo_a_categoria(CLASIFICACIONES[k])
        grupos = sorted({g for a in atomos_de_sector(sector) for g in (mapa[a] or ["SIN_GRUPO"])})
        out[k] = "+".join(grupos)
    return out


def cruces(sector: Sector) -> dict[str, str]:
    """Clasificaciones en las que el sector cruza grupos, salvo el solape público/privado permitido."""
    return {k: g for k, g in grupos_de_sector(sector).items()
            if "+" in g and not (k == "cnaep33" and sector.ciiu4 in MIXTOS_PUBLICO_PRIVADO)}


def tabla_taxonomia() -> pd.DataFrame:
    filas = []
    for s in SECTORES:
        filas.append({
            "sector_id": s.id, "nombre": s.nombre, "seccion_ciiu": s.seccion, "ciiu4": s.ciiu4,
            "atomos": ",".join(atomos_de_sector(s)), "entra_en_comercio": s.comercio,
            "confianza": s.confianza, **{f"grupo_{k}": v for k, v in grupos_de_sector(s).items()},
            "notas": s.notas,
        })
    return pd.DataFrame(filas)


def main() -> None:
    df = tabla_taxonomia()
    df.to_csv(RAIZ / "data" / "clean" / "taxonomia_sectores_tape.csv", index=False, encoding="utf-8")
    print(f"{len(df)} sectores; con comercio: {int(df['entra_en_comercio'].sum())}")


if __name__ == "__main__":
    main()
