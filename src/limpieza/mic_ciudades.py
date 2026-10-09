"""Ciudades (distritos) del mapa MIC, pestaña A: población del Censo 2022, PEA, edad mediana, coordenadas y distancias.

Une dos lecturas del visor (data/raw/mic_mapa/README.md): la tabla A3 (población y distancias por carretera a
Asunción, Ciudad del Este, Encarnación y el puerto de Central) y el mapa A1 (coordenadas, hombres, mujeres, PEA y
edad mediana). Las 263 ciudades son los distritos del Censo 2022. Las coordenadas son un punto por ciudad
(cabecera), no el polígono. Departamentos con el código del INE (0 = Asunción, 1 a 17), igual que SIMEL y la EPHC.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
RAW = RAIZ / "data" / "raw" / "mic_mapa"
TABLA = RAW / "capaA_ciudades_censo2022_2026-10-09.csv"
MAPA = RAW / "capaA_ciudades_mapa_2026-10-09.csv"
SALIDA = RAIZ / "data" / "clean" / "ciudades_mic.csv"
# El mapa y la tabla escriben distinto el nombre de dos ciudades: (código MIC, nombre del mapa) -> nombre de la tabla
ALIAS_MAPA = {("113", "BELLA VISTA NORTE"): "BELLA VISTA", ("104", "ÑUMI"): "NUMI"}


def cargar(tabla: Path = TABLA, mapa: Path = MAPA) -> pd.DataFrame:
    t = pd.read_csv(tabla, dtype={"departamento": str})
    m = pd.read_csv(mapa, dtype={"departamento": str})
    for df in (t, m):
        df["cod_mic"] = df.departamento.str[:3]
        df["departamento"] = df.departamento.str[5:].str.strip()
    m["ciudad"] = [ALIAS_MAPA.get((c, n), n) for c, n in zip(m.cod_mic, m.ciudad, strict=True)]
    m = m.rename(columns={"poblacion_2022": "poblacion_mapa"})
    df = t.merge(m.drop(columns="departamento"), on=["cod_mic", "ciudad"], how="outer", validate="1:1",
                 indicator=True)
    if (df._merge != "both").any():
        raise ValueError(f"ciudades sin par entre la tabla y el mapa: {df.loc[df._merge != 'both', 'ciudad'].tolist()}")
    if (df.poblacion_2022 != df.poblacion_mapa).any():
        raise ValueError("la población de la tabla y la del mapa no coinciden")
    df["dep_codigo"] = df.cod_mic.astype(int) - 100
    sin_coord = (df.lat == 0) & (df.lon == 0)  # el visor guarda 0,0 cuando falta la ubicación
    df.loc[sin_coord, ["lat", "lon"]] = np.nan
    cols = ["dep_codigo", "departamento", "zona", "ciudad", "poblacion_2022", "hombres", "mujeres", "pea",
            "edad_mediana", "lat", "lon", "dist_asu_km", "dist_cde_km", "dist_enc_km", "dist_puerto_central_km"]
    return df[cols].sort_values(["dep_codigo", "ciudad"]).reset_index(drop=True)


def main() -> None:
    df = cargar()
    df.to_csv(SALIDA, index=False, encoding="utf-8")
    print(f"{len(df)} ciudades; población {int(df.poblacion_2022.sum()):,}; sin coordenadas: "
          f"{df.loc[df.lat.isna(), 'ciudad'].tolist()}")


if __name__ == "__main__":
    main()
