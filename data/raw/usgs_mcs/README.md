# USGS, Mineral Commodity Summaries 2026 (reservas y producción mundiales de minerales) — DESCARGA MANUAL

**Estado: descargado a mano el 2026-10-13 por Joaquín** (ScienceBase bloquea el acceso automático, error 403; no se intentó sortearlo).

- Archivo: `696a75d5d4be0228872d3bf8.csv` (ID del ítem de ScienceBase; 3,2 MB, 8.886 filas). Es el CSV agregado de `Mineral Commodity Summaries 2026 Data Release`
  (USGS, DOI 10.5066/P1WKQ63T, https://doi.org/10.5066/P1WKQ63T), licencia CC0.
- **Codificación: Windows-1252** (no UTF-8). Leer con `pd.read_csv(..., encoding="cp1252")`.
- Columnas: `MCS chapter`, `Section`, `Commodity`, `Country`, `Statistics`, `Statistics_detail`, `Unit`, `Year`, `Value`, `Notes`,
  `Is critical mineral 2025`, `Other notes`. `Value` es texto con comas de miles y marcas como «—», «s» o vacío.
- **Reservas:** `Statistics == "Reserves"` y variantes (729 filas), 53 minerales, 105 países, solo los años 2023 a 2025 (una foto actual, no una serie).
  USGS informa reservas solo de los principales productores: **que un país no aparezca no significa que sus reservas sean cero**. Paraguay no aparece en ninguna fila.
  Las unidades varían por mineral (toneladas, miles de toneladas, quilates, metros cúbicos); hay que convertir por mineral.
- El segundo archivo bajado, `MCS2026_Fig1_Minerals_in_Economy.csv` (cifras de la economía de EE. UU.), no se usa y no se copió.

Uso previsto: emparejar por producto las reservas de cada mineral (hierro, cobre, bauxita, etc.) con los capítulos HS 26 y 72 a 81.
