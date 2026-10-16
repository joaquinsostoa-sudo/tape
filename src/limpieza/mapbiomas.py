"""Uso y cobertura del suelo por distrito (MapBiomas Paraguay, Colección 2, 1985-2023).

Fuente: `data/raw/mapbiomas_paraguay/Statistics-Paraguay-Col2-V1.xlsx`, hoja COVERAGE, filas de nivel político 4 (260 distritos). Las hectáreas de todas las clases suman la superficie del distrito.
Clases agrupadas: agricultura (3.2), pasturas (3.1), plantación forestal (3.3), bosque natural (1.1 a 1.3), vegetación herbácea natural (2.1 y 2.2), sin vegetación (4) y agua (5).
Se guardan los valores de 2023 y el promedio 2021-2023 de la agricultura. No mide rendimiento: dice **cuánta tierra es agrícola** en cada distrito, que es lo que la medida de hectáreas de fincas no distinguía de la ganadería extensiva.
Los distritos se unen a los 263 del Censo 2022 por nombre dentro del departamento (palabras contenidas y similitud, como en `base_capital_humano.a_clave_base`).

Salida: `data/clean/mapbiomas_uso_distrito.csv`. Uso: uv run --with openpyxl python -m src.limpieza.mapbiomas
"""
from __future__ import annotations

import pandas as pd

from src.puentes import base_capital_humano as bc
from src.puentes.taxonomia_tape import RAIZ

ENTRADA = RAIZ / "data" / "raw" / "mapbiomas_paraguay" / "Statistics-Paraguay-Col2-V1.xlsx"
SALIDA = RAIZ / "data" / "clean" / "mapbiomas_uso_distrito.csv"
GRUPOS = {
    "3.2 Agriculture": "agricultura", "3.1 Pasture": "pastura", "3.3 Forest Plantation": "plantacion_forestal",
    "1.1 Closed Natural Woodlands": "bosque_natural", "1.2 Open Natural Woodlands": "bosque_natural", "1.3 Flooded Natural Woodlands": "bosque_natural",
    "2.1 Flooded grasslands": "herbacea_natural", "2.2 Grassland": "herbacea_natural", "4. Non vegetated area": "sin_vegetacion", "5. Water bodies": "agua",
}
ANIOS_PROMEDIO = ("y2021", "y2022", "y2023")


def agrupar(cobertura: pd.DataFrame) -> pd.DataFrame:
    """Hectáreas por distrito y grupo de clases (2023), promedio 2021-2023 de la agricultura y la superficie total. `cobertura` son las filas de nivel distrito de la hoja COVERAGE."""
    d = cobertura.assign(grupo=cobertura["class_level_2"].map(GRUPOS))
    sin_grupo = d[d["grupo"].isna()]["class_level_2"].unique().tolist()
    if sin_grupo:
        raise ValueError(f"clases sin grupo: {sin_grupo}")
    claves = ["territory_level_3", "territory_level_4"]
    a = d.groupby(claves + ["grupo"])["y2023"].sum().unstack(fill_value=0.0).add_prefix("ha_").add_suffix("_2023")
    a["ha_total"] = a.sum(axis=1)
    prom = d[d["grupo"] == "agricultura"].assign(m=lambda x: x[list(ANIOS_PROMEDIO)].mean(axis=1)).groupby(claves)["m"].sum().rename("ha_agricultura_prom_2021_2023")
    a = a.join(prom).reset_index()
    for c in ("agricultura", "pastura", "plantacion_forestal", "bosque_natural", "herbacea_natural", "sin_vegetacion", "agua"):
        if f"ha_{c}_2023" not in a:
            a[f"ha_{c}_2023"] = 0.0
    a["pct_agricultura"] = 100 * a["ha_agricultura_2023"] / a["ha_total"]
    a["pct_pastura"] = 100 * a["ha_pastura_2023"] / a["ha_total"]
    return a


def main() -> None:
    d = pd.read_excel(ENTRADA, sheet_name="COVERAGE")
    a = agrupar(d[d["category"] == "POLITICAL_LEVEL_4"])
    base = bc.distritos_base()
    a = bc.a_clave_base(a, "territory_level_3", "territory_level_4", base)
    antes = len(a)
    a = a.drop_duplicates(["dep", "clave"])
    salida = base[["departamento", "distrito", "dep", "clave", "poblacion"]].merge(a.drop(columns=["territory_level_3", "territory_level_4", "nombre_distrito"]), on=["dep", "clave"], how="left")
    salida.drop(columns=["dep", "clave"]).round(2).to_csv(SALIDA, index=False, encoding="utf-8")
    sin = salida[salida["ha_total"].isna()]
    print(f"distritos de MapBiomas: {antes} | de los 263: con dato {int(salida['ha_total'].notna().sum())}, sin dato {len(sin)}: {sin['distrito'].tolist()}")
    print(f"superficie total de los distritos con dato: {salida['ha_total'].sum() / 1e6:.1f} millones de ha | agricultura 2023: {salida['ha_agricultura_2023'].sum() / 1e6:.2f} | pasturas: {salida['ha_pastura_2023'].sum() / 1e6:.2f}")
    print("distritos con más agricultura (ha):", salida.sort_values("ha_agricultura_2023", ascending=False).head(6)[["distrito", "ha_agricultura_2023", "pct_agricultura"]].round(1).values.tolist())
    print("distritos con mayor % agrícola:", salida.sort_values("pct_agricultura", ascending=False).head(6)[["distrito", "pct_agricultura"]].round(1).values.tolist())


if __name__ == "__main__":
    main()
