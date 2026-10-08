# Atlas of Economic Complexity: datos de comercio y complejidad

- **Institución:** Growth Lab, Harvard
- **Registro:** fila `atlas` de `data/fuentes.csv`
- **Acceso:** Descarga directa (Harvard Dataverse)
- **Cobertura:** 1962-último año (SITC); 1995+ (HS)

## Qué esperamos aquí

Archivos esperados (Harvard Dataverse, colección Atlas):
- `country_hsproduct4digit_year*.csv` (o `.dta`): exportaciones, RCA, PCI, COG, distancia por país-producto-año
- `hs_product*.csv` / clasificación de productos (nombres, secciones)
- `location_country*.csv`

Descarga: `src/descargas/atlas.py` usa la API de Dataverse; si falla, bajar a mano y dejar los archivos aquí.

## Reglas

- No modificar, renombrar columnas ni resguardar versiones editadas: `data/raw` es solo lectura.
- Al copiar archivos, completar `fecha de descarga` y `versión` en `data/fuentes.csv`.
- Los archivos pesados están ignorados por git (solo se versionan los README).
