"""Industrias del mapa MIC por distrito y sector TAPE (conteos fraccionarios según el puente de subsectores).

Cada industria se reparte entre sectores TAPE con los pesos de `puente_mic_subsector_sector.csv`; las que
caen en subsectores genéricos quedan como `sin_sector`. Es la primera tabla territorial de TAPE
(presencia sectorial por distrito) y alimenta la densidad doméstica del Módulo 2.
"""
from __future__ import annotations

import pandas as pd

from .taxonomia_tape import RAIZ

LOCALIZADAS = RAIZ / "data" / "clean" / "industrias_mic_localizadas.parquet"
PUENTE = RAIZ / "data" / "clean" / "puente_mic_subsector_sector.csv"
SALIDA = RAIZ / "data" / "clean" / "industrias_distrito_sector_tape.parquet"


def _norm(s: pd.Series) -> pd.Series:
    return s.str.replace("--C--", ",", regex=False)  # el visor codifica la coma como --C--


def repartir(localizadas: pd.DataFrame, puente: pd.DataFrame) -> pd.DataFrame:
    """Conteo fraccionario por (departamento, distrito, sector_id, confianza)."""
    pts = localizadas.assign(sector_mic=_norm(localizadas.sector), subsector_mic=_norm(localizadas.subsector))
    m = pts.merge(puente.fillna({"sector_id": ""}), on=["sector_mic", "subsector_mic"], how="left", validate="m:m")
    sin_puente = m.peso.isna().sum()
    if sin_puente:
        raise ValueError(f"{sin_puente} industrias sin fila en el puente")
    # los subsectores sin_sector tienen peso 0: se cuentan completos como sin_sector
    m["n"] = m.peso.where(m.sector_id != "", 1.0)
    return m.groupby(["departamento", "distrito", "sector_id", "confianza"], as_index=False).n.sum().rename(
        columns={"n": "n_industrias"})


def main() -> None:
    t = repartir(pd.read_parquet(LOCALIZADAS), pd.read_csv(PUENTE, dtype={"sector_id": str}))
    t.to_parquet(SALIDA, index=False)
    print(f"{len(t)} filas; industrias: {t.n_industrias.sum():.0f}; sin sector: {t[t.sector_id == ''].n_industrias.sum():.0f}")


if __name__ == "__main__":
    main()
