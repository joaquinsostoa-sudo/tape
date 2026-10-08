# ILOSTAT indicadores laborales

- **Institución:** OIT
- **Registro:** fila `ilostat` de `data/fuentes.csv`
- **Acceso:** Descarga directa (bulk .csv.gz)
- **Cobertura:** Variable

## Qué esperamos aquí

Archivos esperados: indicadores elegidos en formato bulk `.csv.gz` (p. ej. `EAP_*`, `EMP_*`), tras decidir cuáles en el plan.

## Reglas

- No modificar, renombrar columnas ni resguardar versiones editadas: `data/raw` es solo lectura.
- Al copiar archivos, completar `fecha de descarga` y `versión` en `data/fuentes.csv`.
- Los archivos pesados están ignorados por git (solo se versionan los README).
