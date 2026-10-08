"""Puente subsector del mapa MIC -> sector TAPE (tabla manual, una sola vez, con confianza por fila).

Cada subsector se reparte entre clases CIIU Rev.4 con pesos (suman 1); la clase determina el sector
TAPE. Los subsectores genéricos ("industria general", "otros industriales") no se pueden asignar y
quedan como `sin_sector`. Los pesos son una estimación del equipo: se reemplazan al conseguir el
detalle oficial (p. ej. la lista de empresas con su CIIU).
"""
from __future__ import annotations

import pandas as pd

from .taxonomia_tape import RAIZ, sectores_de_clase

RESUMEN = RAIZ / "data" / "raw" / "mic_mapa" / "industrias_sector_subsector_2026-10-08.csv"
SALIDA = RAIZ / "data" / "clean" / "puente_mic_subsector_sector.csv"

# subsector -> (confianza, [(clase CIIU, peso), ...]); lista vacía = sin_sector
M: dict[str, tuple[str, list[tuple[str, float]]]] = {
    "AGROINDUSTRIA GENERAL": ("sin_sector", []),
    "APICULTURA Y MIEL": ("media", [("0149", 0.3), ("1079", 0.7)]),
    "BALANCEADOS Y NUTRICION ANIMAL": ("alta", [("1080", 1.0)]),
    "PRODUCCION PECUARIA Y GRANJAS": ("media", [("0146", 0.6), ("0145", 0.2), ("0141", 0.2)]),
    "SILOS, ACOPIO Y GRANOS": ("media", [("0163", 0.8), ("1061", 0.2)]),
    "TABACO Y DERIVADOS": ("alta", [("1200", 1.0)]),
    "ACEITES Y OLEAGINOSAS": ("alta", [("1040", 1.0)]),
    "ALIMENTOS PROCESADOS": ("baja", [("1079", 0.5), ("1030", 0.25), ("1075", 0.25)]),
    "AZUCAR, ALCOHOL Y CANA": ("media", [("1072", 0.6), ("1101", 0.2), ("2011", 0.2)]),
    "BEBIDAS Y AGUA": ("alta", [("1104", 1.0)]),
    "EMBUTIDOS Y FIAMBRES": ("alta", [("1010", 1.0)]),
    "ESENCIAS, AROMAS Y EXTRACTOS": ("baja", [("1079", 0.5), ("2029", 0.5)]),
    "FRIGORIFICOS Y CARNICOS": ("alta", [("1010", 1.0)]),
    "HELADOS": ("alta", [("1050", 1.0)]),
    "HIELO Y AGUA": ("media", [("1104", 0.5), ("3530", 0.5)]),
    "LACTEOS": ("alta", [("1050", 1.0)]),
    "MOLINERIA, HARINAS Y ALMIDONES": ("media", [("1061", 0.7), ("1062", 0.3)]),
    "PANIFICADOS Y CONFITERIA": ("media", [("1071", 0.8), ("1073", 0.2)]),
    "PASTAS Y FIDEOS": ("alta", [("1074", 1.0)]),
    "YERBA MATE Y HIERBAS": ("media", [("1079", 1.0)]),
    "ARTESANIA Y MANUALIDADES": ("baja", [("3290", 0.6), ("1392", 0.4)]),
    "FABRICA DE BALANCEADOS DE LA COOPERATIVA": ("alta", [("1080", 1.0)]),
    "ELECTRICIDAD Y ELECTRONICA": ("media", [("2790", 1.0)]),
    "REFRIGERACION Y CLIMATIZACION": ("baja", [("2819", 0.5), ("4322", 0.5)]),
    "CARBON, LENA Y COMBUSTIBLES SOLIDOS": ("baja", [("0220", 0.7), ("1920", 0.3)]),
    "COMBUSTIBLES Y LUBRICANTES": ("baja", [("1920", 0.5), ("4730", 0.5)]),
    "ASERRADEROS Y MADERA ASERRADA": ("alta", [("1610", 1.0)]),
    "CAJAS, ENVASES Y EMBALAJES DE MADERA": ("alta", [("1623", 1.0)]),
    "CARPINTERIA Y EBANISTERIA": ("media", [("1622", 0.6), ("3100", 0.4)]),
    "MUEBLES Y MOBILIARIO": ("alta", [("3100", 1.0)]),
    "PRODUCTOS DE MADERA": ("alta", [("1629", 1.0)]),
    "BASCULAS Y BALANZAS": ("media", [("2829", 1.0)]),
    "MAQUINARIA, EQUIPOS Y REPUESTOS": ("media", [("2829", 0.6), ("2930", 0.2), ("3312", 0.2)]),
    "ALUMINIO Y ABERTURAS": ("alta", [("2511", 1.0)]),
    "ASTILLEROS Y EMBARCACIONES": ("alta", [("3011", 1.0)]),
    "HERRERIA Y ESTRUCTURAS METALICAS": ("alta", [("2511", 1.0)]),
    "HOJALATERIA Y CHAPERIA": ("baja", [("2599", 0.5), ("4520", 0.5)]),
    "METALURGIA Y FUNDICION": ("alta", [("2431", 1.0)]),
    "METALURGIA Y METALMECANICA": ("media", [("2599", 0.7), ("2420", 0.3)]),
    "PRODUCTOS METALICOS": ("alta", [("2599", 1.0)]),
    "TORNERIA Y MECANIZADO": ("alta", [("2592", 1.0)]),
    "BALDOSAS, MARMOL Y REVESTIMIENTOS": ("alta", [("2396", 1.0)]),
    "CAL Y DERIVADOS": ("alta", [("2394", 1.0)]),
    "CANTERAS Y ARIDOS": ("alta", [("0810", 1.0)]),
    "CEMENTO, YESO Y AFINES": ("alta", [("2394", 1.0)]),
    "CERAMICA, LADRILLOS Y OLERIA": ("alta", [("2392", 1.0)]),
    "MATERIALES DE CONSTRUCCION": ("media", [("2395", 0.5), ("2399", 0.5)]),
    "PREFABRICADOS Y HORMIGON": ("alta", [("2395", 1.0)]),
    "VIDRIO Y VIDRIERIA": ("alta", [("2310", 1.0)]),
    "FABRICA Y VENTA DE MOBILIARIO DE METAL Y CARPINTERIA": ("media", [("3100", 1.0)]),
    "INDUSTRIA GENERAL Y MULTIACTIVIDAD": ("sin_sector", []),
    "OTROS INDUSTRIALES": ("sin_sector", []),
    "GRAFICA, IMPRENTA Y SENALETICA": ("alta", [("1811", 1.0)]),
    "PAPEL, CARTON Y EMBALAJES": ("alta", [("1702", 1.0)]),
    "BOLSAS Y ENVASES PLASTICOS": ("alta", [("2220", 1.0)]),
    "CAUCHO Y GOMA": ("alta", [("2219", 1.0)]),
    "PLASTICOS Y ENVASES": ("alta", [("2220", 1.0)]),
    "AGROQUIMICOS Y FERTILIZANTES": ("alta", [("2021", 1.0)]),
    "COSMETICA Y PERFUMERIA": ("alta", [("2023", 1.0)]),
    "PINTURAS Y RECUBRIMIENTOS": ("alta", [("2022", 1.0)]),
    "PRODUCTOS DE LIMPIEZA": ("alta", [("2023", 1.0)]),
    "QUIMICOS, FARMACIA Y LABORATORIO": ("media", [("2029", 0.4), ("2100", 0.4), ("2011", 0.2)]),
    "RECICLAJE DE PAPEL Y CARTON": ("alta", [("3830", 1.0)]),
    "RECICLAJE DE PLASTICOS": ("alta", [("3830", 1.0)]),
    "RECICLAJE GENERAL": ("alta", [("3830", 1.0)]),
    "RECICLAJE METALICO": ("alta", [("3830", 1.0)]),
    "SERVICIOS INDUSTRIALES Y MANTENIMIENTO": ("media", [("3312", 1.0)]),
    "CALZADOS": ("alta", [("1520", 1.0)]),
    "COLCHONES, TAPICERIA Y HOGAR": ("baja", [("3100", 0.5), ("1392", 0.3), ("9524", 0.2)]),
    "CONFECCION E INDUMENTARIA": ("alta", [("1410", 1.0)]),
    "CUERO Y MARROQUINERIA": ("alta", [("1512", 1.0)]),
    "TEXTILES Y TEJIDOS": ("alta", [("1311", 1.0)]),
    "FABRICA DE HAMACAS Y COLCHAS DE LA COOPERATIVA": ("alta", [("1392", 1.0)]),
}


def construir(resumen: pd.DataFrame) -> pd.DataFrame:
    filas = []
    for r in resumen.itertuples(index=False):
        confianza, clases = M[r.subsector]
        if not clases:
            filas.append({"sector_mic": r.sector, "subsector_mic": r.subsector, "sector_id": "", "ciiu4": "",
                          "peso": 0.0, "confianza": "sin_sector"})
        for clase, peso in clases:
            (sector,) = sectores_de_clase(clase)
            filas.append({"sector_mic": r.sector, "subsector_mic": r.subsector, "sector_id": sector,
                          "ciiu4": clase, "peso": peso, "confianza": confianza})
    df = pd.DataFrame(filas)
    # una fila por (subsector, sector): se suman los pesos de las clases que caen en el mismo sector
    return df.groupby(["sector_mic", "subsector_mic", "sector_id", "confianza"], as_index=False).agg(
        ciiu4=("ciiu4", lambda s: ",".join(sorted(set(s)))), peso=("peso", "sum"))


def main() -> None:
    puente = construir(pd.read_csv(RESUMEN))
    puente.to_csv(SALIDA, index=False, encoding="utf-8")
    print(f"{puente.subsector_mic.nunique()} subsectores -> {puente[puente.sector_id != ''].sector_id.nunique()} sectores TAPE")


if __name__ == "__main__":
    main()
