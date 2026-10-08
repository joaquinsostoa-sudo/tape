"""Puente CNAEP 1.0 (5 dígitos) -> clase CIIU Rev.4 -> sector TAPE, con nivel de confianza por fila.

Sirve para llevar a la taxonomía TAPE cualquier dato que venga codificado en CNAEP (BCP, INE, MIC).
Confianza: alta si el código CNAEP corresponde a una sola clase CIIU en una página de alineado
directo; media si el alineado fue aproximado, se corrigió a mano, o el código se reparte entre
varias clases o sectores (en ese caso el peso queda repartido en partes iguales, hasta tener pesos
por valor); sin_sector si la clase no pertenece a ningún sector TAPE (división 99).
"""
from __future__ import annotations

import pandas as pd

from .taxonomia_tape import RAIZ, sectores_de_clase

ENTRADA = RAIZ / "data" / "clean" / "cnaep1_ciiu4.csv"
SALIDA = RAIZ / "data" / "clean" / "puente_cnaep_sector.csv"


def construir(cnaep_ciiu: pd.DataFrame) -> pd.DataFrame:
    filas = []
    for r in cnaep_ciiu.itertuples(index=False):
        sectores = sectores_de_clase(r.ciiu4)
        filas.append({"cnaep": r.cnaep, "ciiu4": r.ciiu4, "sectores": sectores,
                      "dudoso": r.alineacion == "aproximada" or bool(r.corregida_a_mano)})
    df = pd.DataFrame(filas)
    por_cnaep = df.groupby("cnaep")
    salida = []
    for cnaep, g in por_cnaep:
        pares = [(c, s) for c, ss in zip(g.ciiu4, g.sectores, strict=True) for s in ss]
        sectores = sorted({s for _, s in pares})
        dudoso = bool(g.dudoso.any())
        for s in sectores:
            confianza = "alta" if (len(g) == 1 and len(sectores) == 1 and not dudoso) else "media"
            salida.append({"cnaep": cnaep, "sector_id": s, "peso": 1 / len(sectores),
                           "ciiu4": ",".join(sorted({c for c, x in pares if x == s})), "confianza": confianza})
        if not sectores:
            salida.append({"cnaep": cnaep, "sector_id": "", "peso": 0.0,
                           "ciiu4": ",".join(g.ciiu4), "confianza": "sin_sector"})
    return pd.DataFrame(salida)


def main() -> None:
    puente = construir(pd.read_csv(ENTRADA, dtype=str).assign(
        uno_a_varios=lambda d: d.uno_a_varios == "True", corregida_a_mano=lambda d: d.corregida_a_mano == "True"))
    puente.to_csv(SALIDA, index=False, encoding="utf-8")
    print(f"{puente.cnaep.nunique()} códigos CNAEP; confianza: {puente.drop_duplicates('cnaep').confianza.value_counts().to_dict()}")


if __name__ == "__main__":
    main()
