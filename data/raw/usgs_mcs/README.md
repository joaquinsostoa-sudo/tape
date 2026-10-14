# USGS, Mineral Commodity Summaries (reservas y producción mundiales de minerales) — DESCARGA MANUAL

**Estado: pendiente de descarga a mano (2026-10-13).** ScienceBase (`sciencebase.gov`) bloquea el acceso automático (error 403) y no se intentó sortearlo.

Qué conseguir: en la página del data release «Mineral Commodity Summaries 2026 Data Release» (USGS, DOI 10.5066/P1WKQ63T,
https://doi.org/10.5066/P1WKQ63T; licencia CC0) el CSV con la **producción y las reservas mundiales por país y mineral**. El nombre exacto no se
pudo verificar (puede ser `MCS2026_World_Data.csv` o un CSV agregado como `MCS2026_Commodities_Data.csv`); revisar que traiga una columna de
reservas por país. Guardarlo en esta carpeta (`data/raw/usgs_mcs/`) sin cambiar el nombre y avisar para registrarlo en `data/fuentes.csv`.

Uso previsto: emparejar por producto las reservas de cada mineral (hierro, cobre, bauxita, etc.) con los capítulos HS 26 y 72 a 81.
