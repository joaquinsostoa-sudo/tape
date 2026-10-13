# World Development Indicators

- **Institución:** Banco Mundial
- **Registro:** fila `wdi` de `data/fuentes.csv`
- **Acceso:** API (api.worldbank.org/v2)
- **Cobertura:** 1960-actual, anual

## Qué esperamos aquí

Archivos esperados (los escribe `src/descargas/wdi.py`):
- `wdi_{INDICADOR}.json` o un `wdi_panel.csv` largo: `iso3, year, indicator, value`
- `wdi_metadata.json` con fecha y versión de la consulta

Todo automático por API; no hay que copiar nada a mano.

## Reglas

- No modificar, renombrar columnas ni resguardar versiones editadas: `data/raw` es solo lectura.
- Al copiar archivos, completar `fecha de descarga` y `versión` en `data/fuentes.csv`.
- Los archivos pesados están ignorados por git (solo se versionan los README).

## Indicadores agregados el 2026-10-12 (15 en total)
- `wdi_EG.ELC.HYRO.ZS_p1.json`: electricidad de fuentes hidroeléctricas, % del total (WDI).
- `wdi_IC.ELC.PRI.KH.DB1619_p1.json`: **precio de la electricidad** en centavos de USD por kWh, metodología Doing Business 2016-2020 (fuente `Doing Business`, id 1 de la API, con `&source=1`). Solo 2014-2019; la fuente está discontinuada desde 2021. Trae una fila por ciudad (por ejemplo Delhi y Mumbai) además de la fila del país con el promedio ponderado: `src/limpieza/dotaciones.py` se queda con la del país. Es la medida de energía de la capa de dotaciones (decisión D4, mejora).
