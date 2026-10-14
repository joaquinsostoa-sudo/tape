"""Distritos nuevos cuyo distrito de origen está confirmado por la ley de creación (revisión normativa del equipo, 2026-10-14, repertorio de la Biblioteca del Congreso / BACN).

Dos listas: `CORREGIDOS` (la ley contradice o completa el padre inferido por geografía) y `CONFIRMADOS` (la ley confirma el padre inferido). Los distritos no incluidos aquí siguen con el padre
inferido (`fuente_padre = inferido`, confianza `baja`): Dr. Bottrell, Tte. Esteban Martínez, Villa Franca, Yabebyry, Ybyrarobana, Karapa'í, Itacuá y Boquerón (la ley de Boquerón no permite
asumir un padre único sin revisar el polígono legal).
Cuando la ley toma territorio de varios distritos, `padres` los lista todos; el puente reparte el distrito en partes iguales entre los distritos del Censo 2011 a los que remiten (el reparto real
depende del polígono legal, que no tenemos). Fuente de los números de ley: la revisión pegada por el equipo; no se verificaron contra el texto de cada ley.
"""
from __future__ import annotations

# nuevo distrito -> (departamento, padres, ley). Los nombres de los padres se buscan entre los distritos del mismo departamento.
CORREGIDOS: dict[str, tuple[str, list[str], str]] = {
    "3 de Mayo": ("CAAZAPA", ["Yuty"], "Ley 4604"),
    "Nueva Toledo": ("CAAGUAZU", ["Raúl Arsenio Oviedo", "Mariscal Francisco Solano López"], "Ley 4494"),
    "Tavapy": ("ALTO PARANA", ["Santa Rosa del Monday"], "Ley 4322"),
    "Liberación": ("SAN PEDRO", ["Choré", "Guayaibí"], "información institucional (sin número de ley)"),
    "Laurel": ("CANINDEYU", ["Ybyrarobaná", "Nueva Esperanza"], "Ley 6498"),
    "Yby Pytá": ("CANINDEYU", ["Villa Ygatimí", "Curuguaty", "Corpus Christi"], "Ley 4894"),
    "Paso Horqueta": ("CONCEPCION", ["San Alfredo", "Concepción"], "Ley 6518"),
    "San José del Rosario": ("SAN PEDRO", ["Villa del Rosario", "General Elizardo Aquino"], "Ley 6674"),
    "San Vicente Pancholo": ("SAN PEDRO", ["General Isidoro Resquín"], "Ley 5715"),
}
CONFIRMADOS: dict[str, tuple[str, list[str], str]] = {
    "Dr. Raúl Peña": ("ALTO PARANA", ["Naranjal"], "Ley 4725"),
    "José Félix López": ("CONCEPCION", ["Concepción"], "Ley 4418"),
    "Zanja Pyta": ("AMAMBAY", ["Pedro Juan Caballero"], "Ley 4417"),
    "Cerro Corá": ("AMAMBAY", ["Pedro Juan Caballero"], "Ley 6555"),
    "Maracaná": ("CANINDEYU", ["Curuguaty"], "Ley 5673"),
    "Puerto Adela": ("CANINDEYU", ["Salto del Guairá"], "Ley 6098"),
    "Arroyito": ("CONCEPCION", ["Horqueta"], "Ley 5742"),
    "Paso Barreto": ("CONCEPCION", ["Concepción"], "Ley 4926"),
    "San Alfredo": ("CONCEPCION", ["Concepción"], "Ley 4927"),
    "Campo Aceval": ("PRESIDENTE HAYES", ["Tte. 1ro Manuel Irala Fernández"], "Ley 6554"),
    "Nueva Asunción": ("PRESIDENTE HAYES", ["Villa Hayes"], "Ley 6731"),
}
