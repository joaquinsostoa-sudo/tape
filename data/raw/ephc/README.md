# EPHC microdatos

- **Institución:** INE
- **Registro:** fila `ephc` de `data/fuentes.csv`
- **Acceso:** Web del INE
- **Cobertura:** 2022-2025

## Qué esperamos aquí

Archivos esperados: microdatos EPHC por año o trimestre (SAV/DTA/CSV), diccionarios de variables y el clasificador de actividad. Una subcarpeta por año.

## Reglas

- No modificar, renombrar columnas ni resguardar versiones editadas: `data/raw` es solo lectura.
- Al copiar archivos, completar `fecha de descarga` y `versión` en `data/fuentes.csv`.
- Los archivos pesados están ignorados por git (solo se versionan los README).
