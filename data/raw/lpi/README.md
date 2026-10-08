# Logistics Performance Index

- **Institución:** Banco Mundial
- **Registro:** fila `lpi` de `data/fuentes.csv`
- **Acceso:** Descarga directa o indicador WDI (LP.LPI.OVRL.XQ)
- **Cobertura:** 2007, 2010, 2012, 2014, 2016, 2018, 2023 (bienal irregular)

## Qué esperamos aquí

Archivos esperados:
- `lpi_*.xlsx` por edición (portal LPI), o indicador `LP.LPI.OVRL.XQ` vía WDI (en ese caso queda en `wdi`)

Si el portal no deja bajar automáticamente, copiar aquí los Excel de cada edición.

## Reglas

- No modificar, renombrar columnas ni resguardar versiones editadas: `data/raw` es solo lectura.
- Al copiar archivos, completar `fecha de descarga` y `versión` en `data/fuentes.csv`.
- Los archivos pesados están ignorados por git (solo se versionan los README).
