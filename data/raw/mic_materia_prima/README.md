# Régimen de materia prima

- **Institución:** MIC
- **Registro:** fila `mic_materia_prima` de `data/fuentes.csv`
- **Acceso:** Web MIC / solicitud
- **Cobertura:** Mensual

## Qué esperamos aquí

Archivos esperados: listado mensual del régimen (empresa, insumo/actividad, departamento). Excel/CSV.

## Reglas

- No modificar, renombrar columnas ni resguardar versiones editadas: `data/raw` es solo lectura.
- Al copiar archivos, completar `fecha de descarga` y `versión` en `data/fuentes.csv`.
- Los archivos pesados están ignorados por git (solo se versionan los README).
