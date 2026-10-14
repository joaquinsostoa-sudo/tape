"""Puente del tercer nivel del mapa MIC (la actividad «específica», texto libre de cada industria) -> clase CIIU Rev.4 -> sector TAPE.

Por qué: el puente de subsectores (`mic_sector.py`, 73 filas) reparte cada subsector con pesos estimados; la actividad específica de cada una de las 17.080 industrias dice mucho más (CARPINTERIA,
OLERIA, HERRERIA, TABACALERA...). Los 1.744 textos distintos se resuelven con reglas ordenadas (primera coincidencia) sobre el texto normalizado y con confianza por fila (regla 5 de CLAUDE.md):
- El texto se parte en actividades (` Y `, `/`, `,`); cada parte se clasifica por separado; las partes sin regla (VENTA, REPARACIONES...) se ignoran si otra sí la tiene. Con varias clases distintas
  el peso se reparte por igual y la confianza baja a `baja` (salvo que todas caigan en el mismo sector).
- `HEREDAR`: la actividad es ambigua y se usan los pesos del subsector. `GENERICO`: «INDUSTRIA», «FABRICA»...: sin sector. Sin regla: se hereda el subsector (`fuente = heredado_subsector`, `baja`).
- Concordancia: si el sector de la regla no está entre los del subsector (el MIC pone TABACALERA en «cal y derivados»), la fila se marca `discrepancia_subsector`, se usa la regla (el texto
  específico informa más que un subsector mal puesto) y la confianza baja un escalón.
Las clases son una estimación del equipo hasta tener el CIIU oficial de cada empresa; las filas `baja` y las discrepancias van a la cola de revisión.

Uso: uv run python -m src.puentes.mic_especifico
"""
from __future__ import annotations

import re
import unicodedata

import pandas as pd

from .taxonomia_tape import RAIZ, sectores_de_clase

PUNTOS = RAIZ / "data" / "clean" / "industrias_mic_puntos.parquet"
LOCALIZADAS = RAIZ / "data" / "clean" / "industrias_mic_localizadas.parquet"
PUENTE_SUBSECTOR = RAIZ / "data" / "clean" / "puente_mic_subsector_sector.csv"
SALIDA = RAIZ / "data" / "clean" / "puente_mic_especifico_ciiu.csv"
SALIDA_DISTRITO = RAIZ / "data" / "clean" / "industrias_distrito_sector_tape_esp.csv"
COLA = RAIZ / "data" / "clean" / "puente_mic_especifico_revision.csv"

HEREDAR, GENERICO = "HEREDAR", "GENERICO"
ORDEN_CONF = {"alta": 2, "media": 1, "baja": 0}

# (patrón sobre el texto normalizado, clases [(clase, peso)] | HEREDAR | GENERICO, confianza). La primera coincidencia gana: va lo específico antes que lo general.
REGLAS: list[tuple[str, object, str]] = [
    (r"AGUA MINERAL|AGUATERIA|EMBOTELL|BEBIDA|REFRESC|GASEOSA", [("1104", 1.0)], "alta"),
    (r"CERVECER", [("1103", 1.0)], "alta"),
    (r"ALCOHOL|DESTILER", [("1101", 1.0)], "media"),
    (r"HIELO|HIELERIA", [("3530", 1.0)], "media"),
    (r"CURA DE TABACO|SE SECA TABACO", [("0163", 1.0)], "media"),
    (r"TABAC", [("1200", 1.0)], "alta"),
    (r"YERBA", [("1079", 1.0)], "media"),
    (r"FRIGORIFIC|MATADERIA|MATADERO|CARNIC|EMBUTIDO|FIAMBRE|GRASERIA|PRODUCTOS AVICOLAS", [("1010", 1.0)], "alta"),
    (r"LACTEO|QUESER|QUESO|LECHE|YOGUR|MANTECA", [("1050", 1.0)], "alta"),
    (r"HELAD", [("1050", 1.0)], "media"),
    (r"ACEITE|ACEITERA|OLEAGINOS|OLEOGINOS", [("1040", 1.0)], "alta"),
    (r"AZUCAR|CANA DULCE|MIEL DE CANA|MIEL NEGRA|MELAZA|INGENIO", [("1072", 1.0)], "media"),
    (r"APICULT", [("0149", 1.0)], "alta"),
    (r"FABRICA DE MIEL|MIEL", [("1079", 1.0)], "media"),
    (r"PASTA|FIDEO", [("1074", 1.0)], "alta"),
    (r"ALMIDON|MANDIOCA", [("1062", 1.0)], "media"),
    (r"MOLIN|HARIN|ARROCERA|FABRICA DE ARROZ|MAIZ|CEREAL", [("1061", 1.0)], "media"),
    (r"BALANCEAD|ALIMENTOS PARA ANIMALES|COMIDA PARA PERRO|NUTRICION ANIMAL", [("1080", 1.0)], "alta"),
    (r"SILO|ACOPIO|GRANOS|GRANELERO|ALGODON", [("0163", 1.0)], "media"),
    (r"SEMILLER|SEMILLAS", [("0164", 1.0)], "media"),
    (r"BANANA", [("1030", 1.0)], "media"),
    (r"PANADERIA|PANIFICAD|CHIPA|CHIPERIA|TORTAS|MASAS|PASTELERIA|GALLETIT", [("1071", 1.0)], "alta"),
    (r"CONFITERIA|ALFAJOR|DULCES|BOMBON|CARAMELO", [("1073", 1.0)], "media"),
    (r"EMPANADAS|ROTISERIA", [("1075", 1.0)], "media"),
    (r"LOMITERIA", [("5610", 1.0)], "baja"),
    (r"SAL$|PROCESADORA DE SAL", [("0893", 1.0)], "baja"),
    (r"PRODUCTOS ALIMENTICIOS|ELABORACION DE ALIMENTOS|FABRICA DE ALIMENTOS|ALIMENTOS", [("1079", 1.0)], "baja"),
    (r"CHANCHERIA|CRIA DE CHANCHO|PORCIN", [("0145", 1.0)], "alta"),
    (r"AVICULTURA|AVICOLA|HUEVOS|POLLO", [("0146", 1.0)], "media"),
    (r"HORTICULTURA|FRUTILLA|TOMATE|HORTALIZA", [("0113", 1.0)], "media"),
    (r"CHIA|EMPRESA AGRICOLA|PRODUCCION AGRICOLA|AGRICOLA", [("0119", 1.0)], "baja"),
    (r"FORESTAL", [("0210", 1.0)], "media"),
    (r"MADERERO", [("0220", 1.0)], "media"),
    (r"ASERRADERO", [("1610", 1.0)], "alta"),
    (r"MULTILAMINADO|TERCIADA|COMPENSADO", [("1621", 1.0)], "media"),
    (r"MUEBLE|MOBILIARIO|MUEBLERIA|SOMMIER|COLCHON", [("3100", 1.0)], "alta"),
    (r"CAJAS DE MADERA|EMBALAJES DE MADERA", [("1623", 1.0)], "alta"),
    (r"CARPINTER|EBANISTER|PUERTAS|ABERTURAS DE MADERA", [("1622", 0.6), ("3100", 0.4)], "media"),
    (r"ESENCIA|PETITGRAIN", [("2029", 1.0)], "alta"),
    (r"FERTILIZANTE|ABONO|AGROQUIM", [("2021", 1.0)], "alta"),
    (r"PINTURA", [("2022", 1.0)], "alta"),
    (r"FARMAC|MEDICAMENT", [("2100", 1.0)], "alta"),
    (r"LIMPIEZA|JABON|COSMETIC|PERFUM", [("2023", 1.0)], "alta"),
    (r"ESCOBA|VELAS", [("3290", 1.0)], "media"),
    (r"PAPEL HIGIENICO", [("1709", 1.0)], "alta"),
    (r"PAPELERIA", [("1709", 1.0)], "baja"),
    (r"PAPEL|CARTON", [("1702", 1.0)], "alta"),
    (r"IMPRENTA|GRAFICA|SERIGRAFIA|PUBLICITARIA|LETREROS|SELLOS|IMPRESIONES", [("1811", 1.0)], "media"),
    (r"BOLSAS", [("1702", 1.0)], "media"),
    (r"PRODUCTOS QUIMICOS|INDUSTRIA QUIMICA", [("2029", 1.0)], "baja"),
    (r"OXIGENO", [("2011", 1.0)], "media"),
    (r"ATELIER", [("1410", 1.0)], "media"),
    (r"TABAQUERIA", [("1200", 1.0)], "media"),
    (r"CENTRO DE CURA", [("0163", 1.0)], "media"),
    (r"COCO", [("1040", 1.0)], "media"),
    (r"PLASTIC|POLIETILENO|PVC|ISOPOR", [("2220", 1.0)], "alta"),
    (r"GOMERIA", [("4520", 1.0)], "baja"),
    (r"PELOTAS|CAUCHO|GOMA", [("2219", 1.0)], "media"),
    (r"RECICL|RECICAL", [("3830", 1.0)], "alta"),
    (r"EFLUENTES|CLOACAL", [("3700", 1.0)], "media"),
    (r"COMPOSTURA DE CALZADO", [("9529", 1.0)], "media"),
    (r"CALZADO|ZAPAT", [("1520", 1.0)], "alta"),
    (r"CURTIEMBRE", [("1511", 1.0)], "alta"),
    (r"TALABARTER|MARROQUIN", [("1512", 1.0)], "alta"),
    (r"HAMACA|COLCHA|TOLDOS", [("1392", 1.0)], "alta"),
    (r"CONFECCION|COSTURA|INDUMENTARIA|PRENDAS|ROPA|UNIFORME|PANTALON|VESTIR|VESTIDO|GUANTES", [("1410", 1.0)], "alta"),
    (r"TEJIDOS Y ALAMBRES", [("2599", 1.0)], "baja"),
    (r"TEXTIL|TEJIDOS", [("1311", 1.0)], "media"),
    (r"GUITARRA", [("3220", 1.0)], "alta"),
    (r"BILLAR", [("3230", 1.0)], "media"),
    (r"ARTESANIA", [("3290", 1.0)], "baja"),
    (r"ASTILLERO", [("3011", 1.0)], "alta"),
    (r"CARROCERIA", [("2920", 1.0)], "media"),
    (r"CALDERA", [("2513", 1.0)], "media"),
    (r"FUNDICION", [("2431", 1.0)], "alta"),
    (r"ACEROS", [("2410", 1.0)], "baja"),
    (r"EXTINTOR|BASCULA|BALANZA|BUJES", [("2829", 1.0)], "media"),
    (r"IMPLEMENTOS AGRICOLAS", [("2821", 1.0)], "media"),
    (r"MAQUINAS INDUSTRIALES", [("2829", 1.0)], "baja"),
    (r"TORNERIA|MECANIZAD|SOLDADURA", [("2592", 1.0)], "alta"),
    (r"OLLAS", [("2599", 1.0)], "alta"),
    (r"HOJALATERIA|FABRICA DE CHAPAS", [("2599", 1.0)], "media"),
    (r"CHAPERIA", [("4520", 1.0)], "media"),
    (r"HERRERIA|TINGLADO|HERRAJE|ALUMINIO|ESTRUCTURAS METALICAS", [("2511", 1.0)], "alta"),
    (r"METALURG|METALMECANIC|ALAMBRES", [("2599", 0.7), ("2420", 0.3)], "media"),
    (r"FERRETERIA|REPARACIONES|VENTA|AUTOSERVICE", [], "baja"),  # actividades comerciales o de servicio: no deciden por sí solas
    (r"POSTES|COLUMNAS|HORMIGON|CONCRETO|PREFABRIC|PREMOLDEADO|PILETAS|CIELO RASO|PLANTERAS|CORDONES|MATERIALES DE CONSTRUCCION", [("2395", 1.0)], "media"),
    (r"PLANTA ASFALTICA", [("2399", 1.0)], "media"),
    (r"MARMOL|GRANITO", [("2396", 1.0)], "alta"),
    (r"BALDOSA|BALDOSERIA|PISOS", [("2396", 1.0)], "media"),
    (r"ALFARERIA", [("2393", 1.0)], "media"),
    (r"OLERIA|LADRILL|TEJAS|CERAMICA", [("2392", 1.0)], "alta"),
    (r"VIDRIERIA|VIDRIO|BOTELLAS", [("2310", 1.0)], "media"),
    (r"\bCAL\b|CALERA|CEMENTO|YESO", [("2394", 1.0)], "alta"),
    (r"ARENERA|CANTERA|MINERA|MOLINO MINERO|TRITURADORA|PIEDRA", [("0810", 1.0)], "alta"),
    (r"CARBON|CARBONERIA|CHARQUE", HEREDAR, "media"),
    (r"^(INDUSTRIA|INDUSTRIAL|FABRICA|PLANTA INDUSTRIAL|PARQUE INDUSTRIAL|PLANTA PROCESADORA|PRODUCTORA|DISTRIBUIDORA|PUERTO|LABORATORIO|AGROINDUSTRIAL|AGROINDUSTRIA)$", GENERICO, "baja"),
]
# Reglas sobre el texto completo, antes de partirlo en actividades (la partición rompería estas expresiones).
PRIORIDAD: list[tuple[str, str, str]] = [
    (r"MOLINO MINERO|MOLINO DE PIEDRA", "0810", "media"),
    (r"TEJIDOS Y ALAMBRES", "2599", "media"),
    (r"PANADERIA|PANIFICAD", "1071", "alta"),  # «panadería y confitería» es una panadería
]
_PRIORIDAD = [(re.compile(p), c, conf) for p, c, conf in PRIORIDAD]
_REGLAS = [(re.compile(p), c, conf) for p, c, conf in REGLAS]


def normalizar(texto: str) -> str:
    """Mayúsculas, sin tildes ni signos raros (hay guiones blandos y caracteres rotos en el visor) y con espacios simples."""
    t = unicodedata.normalize("NFKD", str(texto).upper())
    t = "".join(c for c in t if c.isascii())
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9/, ]", " ", t)).strip()


def partes(texto: str) -> list[str]:
    """Actividades separadas por « Y », «/» o «,»."""
    return [p.strip() for p in re.split(r"\bY\b|/|,", normalizar(texto)) if p.strip()]


def clasificar_parte(parte: str) -> tuple[object, str, str] | None:
    """Primera regla que coincide con la parte: (clases | HEREDAR | GENERICO, confianza, patrón); None si ninguna."""
    for rx, clases, conf in _REGLAS:
        if rx.search(parte):
            return clases, conf, rx.pattern
    return None


def desde_reglas(texto: str) -> tuple[list[tuple[str, float]], str, str] | str | None:
    """Clases (clase, peso) del texto completo, confianza y reglas usadas; HEREDAR o GENERICO si alguna parte lo pide y ninguna otra aporta clases; None si ninguna parte tiene regla."""
    clases: dict[str, float] = {}
    confs: list[str] = []
    sectores_por_parte: list[set[str]] = []
    usadas: list[str] = []
    marca = None
    completo = normalizar(texto)
    for rx, clase, conf in _PRIORIDAD:
        if rx.search(completo):
            return [(clase, 1.0)], conf, rx.pattern
    for p in partes(texto):
        r = clasificar_parte(p)
        if r is None:
            continue
        c, conf, patron = r
        usadas.append(patron)
        if isinstance(c, str):
            marca = c
            continue
        for clase, peso in c:
            clases[clase] = clases.get(clase, 0.0) + peso
        if c:
            confs.append(conf)
            sectores_por_parte.append({sectores_de_clase(k)[0] for k, _ in c})
    if not clases:
        return marca
    total = sum(clases.values())
    lista = [(k, v / total) for k, v in clases.items()]
    conf = min(confs, key=lambda x: ORDEN_CONF[x])
    if len(sectores_por_parte) > 1 and not set.intersection(*sectores_por_parte):  # actividades sin ningún sector en común (la ambigüedad de una sola regla no cuenta)
        conf = "baja"
    return lista, conf, "; ".join(usadas)


def heredar(subsector: str, puente: pd.DataFrame) -> list[tuple[str, str, float, str]]:
    """Filas (sector_id, ciiu4, peso, confianza) del subsector en el puente de subsectores."""
    s = puente[puente.subsector_mic == subsector]
    return [(r.sector_id if isinstance(r.sector_id, str) else "", str(r.ciiu4) if isinstance(r.ciiu4, str) else "", float(r.peso), r.confianza) for r in s.itertuples()]


def mapear(especifico: str, subsector: str, puente: pd.DataFrame) -> list[dict]:
    """Filas del puente para una actividad específica (una por sector TAPE)."""
    base = {"especifico": especifico, "subsector": subsector}
    sectores_sub = {s for s in puente[puente.subsector_mic == subsector].sector_id.dropna() if s}
    r = desde_reglas(especifico)

    def heredado(fuente: str, disc: bool = False, regla: str = "") -> list[dict]:  # disc y regla se dejan por compatibilidad con la fila de salida
        filas = [{**base, "sector_id": s, "ciiu4": c, "peso": p, "confianza": "baja" if conf != "sin_sector" else "sin_sector", "fuente": fuente, "regla": regla,
                  "discrepancia_subsector": disc} for s, c, p, conf in heredar(subsector, puente)]
        return filas or [{**base, "sector_id": "", "ciiu4": "", "peso": 0.0, "confianza": "sin_sector", "fuente": fuente, "regla": regla, "discrepancia_subsector": disc}]

    if r is None:
        return heredado("heredado_subsector")
    if r == GENERICO:
        return [{**base, "sector_id": "", "ciiu4": "", "peso": 0.0, "confianza": "sin_sector", "fuente": "regla", "regla": "generico", "discrepancia_subsector": False}]
    if r == HEREDAR:
        return [{**base, "sector_id": s, "ciiu4": c, "peso": p, "confianza": conf, "fuente": "heredado_subsector", "regla": "ambigua", "discrepancia_subsector": False}
                for s, c, p, conf in heredar(subsector, puente)] or heredado("heredado_subsector")
    clases, conf, regla = r
    por_sector: dict[str, list[tuple[str, float]]] = {}
    for clase, peso in clases:
        por_sector.setdefault(sectores_de_clase(clase)[0], []).append((clase, peso))
    discrepancia = bool(sectores_sub) and not (set(por_sector) & sectores_sub)
    if discrepancia:  # el texto específico informa más que un subsector mal puesto; la confianza baja un escalón y la fila va a revisión
        conf = {"alta": "media", "media": "baja", "baja": "baja"}[conf]
    return [{**base, "sector_id": s, "ciiu4": ",".join(sorted(c for c, _ in v)), "peso": sum(p for _, p in v), "confianza": conf, "fuente": "regla", "regla": regla,
             "discrepancia_subsector": discrepancia} for s, v in por_sector.items()]


def construir(puntos: pd.DataFrame, puente: pd.DataFrame) -> pd.DataFrame:
    """Puente de todas las actividades específicas (con su subsector más frecuente y el número de industrias)."""
    g = puntos.groupby(["especifico", "subsector"]).size().reset_index(name="n_industrias").sort_values(["especifico", "n_industrias"], ascending=[True, False])
    tot = puntos.groupby("especifico").size()
    principal = g.drop_duplicates("especifico")
    filas = []
    for r in principal.itertuples(index=False):
        for f in mapear(r.especifico, r.subsector, puente):
            filas.append({**f, "n_industrias": int(tot[r.especifico])})
    return pd.DataFrame(filas)


def por_distrito(localizadas: pd.DataFrame, puente_esp: pd.DataFrame) -> pd.DataFrame:
    """Industrias por distrito y sector TAPE (el peso reparte la industria entre sectores); las sin sector quedan con sector_id vacío."""
    m = localizadas.merge(puente_esp[["especifico", "sector_id", "peso", "confianza"]], on="especifico", how="left")
    m["n"] = m.peso.where(m.sector_id != "", 1.0)
    return m.groupby(["departamento", "distrito", "sector_id", "confianza"], as_index=False, dropna=False).n.sum().rename(columns={"n": "n_industrias"})


def main() -> None:
    puntos = pd.read_parquet(PUNTOS)
    puente = pd.read_csv(PUENTE_SUBSECTOR, dtype=str, keep_default_na=False).assign(peso=lambda d: d.peso.astype(float))
    p = construir(puntos, puente)
    p.to_csv(SALIDA, index=False, encoding="utf-8")
    cola = p[(p.confianza.isin(["baja"])) | p.discrepancia_subsector | p.fuente.str.startswith("heredado")].sort_values("n_industrias", ascending=False)
    cola.to_csv(COLA, index=False, encoding="utf-8")
    d = por_distrito(pd.read_parquet(LOCALIZADAS), p)
    d.to_csv(SALIDA_DISTRITO, index=False, encoding="utf-8")
    uno = p.drop_duplicates("especifico")
    n = puntos.shape[0]
    cob = uno.groupby(["fuente", "confianza"]).n_industrias.sum().reset_index()
    print(f"{p.especifico.nunique()} actividades específicas, {n} industrias")
    print((cob.assign(pct=lambda x: 100 * x.n_industrias / n)).round(1).to_string(index=False))
    print(f"discrepancias con el subsector: {int(uno.discrepancia_subsector.sum())} actividades, {int(uno[uno.discrepancia_subsector].n_industrias.sum())} industrias; cola de revisión: {cola.especifico.nunique()} actividades")


if __name__ == "__main__":
    main()
