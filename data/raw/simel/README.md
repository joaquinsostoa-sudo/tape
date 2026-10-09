# Datos laborales y formación (SIMEL)

- **Institución:** MTESS / IPS / INE / SNPP
- **Registro:** fila `simel` de `data/fuentes.csv`
- **Acceso:** Web
- **Cobertura:** Variable

## Qué esperamos aquí

Archivos esperados: tablas de empleo formal (IPS) y formación (SNPP) por actividad y departamento.

## Reglas

- No modificar, renombrar columnas ni resguardar versiones editadas: `data/raw` es solo lectura.
- Al copiar archivos, completar `fecha de descarga` y `versión` en `data/fuentes.csv`.
- Los archivos pesados están ignorados por git (solo se versionan los README).

## Archivos presentes (2026-10-09)
Diez tablas en CSV SDMX, bajadas con `uv run python -m src.descargas.simel` (idempotente). Columnas: dimensiones (`REF_AREA`, `TIPEST`, `ECO`, ...), `TIME_PERIOD`, `OBS_VALUE` y notas.
- Establecimientos y puestos inscritos: `DF_ESTNB_TIPEST_ECO`, `DF_ESTNB_AREAREF_TIPEST`, `DF_PUESTONB_TIPEST_ECO`, `DF_PUESTONB_AREAREF_TIPEST` (2022-Q1 a 2026-Q2).
- Formación: `DF_AFSINANB_AREAREF_ECO`, `DF_AFSNPPNB_FLIAPRO`, `DF_MATRNB_AREAREF_SEXO`, `DF_CERSNPP_AREAREF_SEXO` (hasta 2026-Q1).
- Informalidad por departamento: `DF_INFORNAC_AREAREF`, `DF_INFORPRIV_AREAREF` (2022-2025).
