# Reservas probadas de energía (Energy Institute, vía Our World in Data)

Bajadas el 2026-10-13 con `uv run python -m src.descargas.reservas` (idempotente; manifiesto en `MANIFEST.json`).

| Archivo | Gráfico de Our World in Data | Unidad | Años |
|---|---|---|---|
| `petroleo_reservas_probadas.csv` | `oil-proved-reserves` | m3 | 1980-2021 |
| `gas_reservas_probadas.csv` | `natural-gas-proved-reserves` | m3 | 1980-2021 |
| `carbon_reservas_probadas.csv` | `coal-proved-reserves` | toneladas | 2008-2023 (no cubre 2000 ni 2005) |

Columnas: `entity`, `code` (ISO3; las filas `OWID_*` son agregados), `year` y el valor. Cobertura: unos 215 países; cerca de la mitad
tiene reservas mayores que cero en 2015 (Paraguay, cero). Fuente de origen: Energy Institute, Statistical Review of World Energy.
Licencia: CC BY 4.0 de Our World in Data; confirmar las condiciones de reutilización del Energy Institute antes de publicar.
Son dotaciones físicas (no rentas: las rentas de recursos de WDI son valor de producción y serían circulares con las exportaciones).
