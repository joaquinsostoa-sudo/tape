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
