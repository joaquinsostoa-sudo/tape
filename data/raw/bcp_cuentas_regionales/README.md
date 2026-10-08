# Cuentas regionales

- **Institución:** BCP
- **Registro:** fila `bcp_cuentas_regionales` de `data/fuentes.csv`
- **Acceso:** Web del BCP
- **Cobertura:** 2021-2023 anual

## Qué esperamos aquí

Archivos esperados: Excel de cuentas regionales (VAB por actividad y departamento).

## Reglas

- No modificar, renombrar columnas ni resguardar versiones editadas: `data/raw` es solo lectura.
- Al copiar archivos, completar `fecha de descarga` y `versión` en `data/fuentes.csv`.
- Los archivos pesados están ignorados por git (solo se versionan los README).
