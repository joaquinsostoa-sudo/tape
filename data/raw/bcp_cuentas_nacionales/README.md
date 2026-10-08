# Cuentas nacionales

- **Institución:** BCP
- **Registro:** fila `bcp_cuentas_nacionales` de `data/fuentes.csv`
- **Acceso:** Web del BCP
- **Cobertura:** 1991-2025 anual

## Qué esperamos aquí

Archivos esperados: Excel de cuentas nacionales (PIB por actividad, corrientes y constantes) tal como se publicó.

## Reglas

- No modificar, renombrar columnas ni resguardar versiones editadas: `data/raw` es solo lectura.
- Al copiar archivos, completar `fecha de descarga` y `versión` en `data/fuentes.csv`.
- Los archivos pesados están ignorados por git (solo se versionan los README).
