# Comercio exterior de Paraguay (aduana)

- **Institución:** DNIT / BCP
- **Registro:** fila `dnit_comercio_py` de `data/fuentes.csv`
- **Acceso:** Portal / solicitud
- **Cobertura:** Mensual

## Qué esperamos aquí

Archivo esperado: exportaciones mensuales por NCM, país destino y (si existe) aduana/departamento de origen, en CSV o Excel. Indicar rango de fechas y si incluye peso. Copiar tal cual se descargó.

## Reglas

- No modificar, renombrar columnas ni resguardar versiones editadas: `data/raw` es solo lectura.
- Al copiar archivos, completar `fecha de descarga` y `versión` en `data/fuentes.csv`.
- Los archivos pesados están ignorados por git (solo se versionan los README).
