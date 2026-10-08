# Límites administrativos de Paraguay (departamentos, distritos)

- **Institución:** DGEEC/INE o geoBoundaries
- **Registro:** fila `limites_admin` de `data/fuentes.csv`
- **Acceso:** Descarga directa
- **Cobertura:** Vigente

## Qué esperamos aquí

Archivos esperados: shapefile o GeoJSON de nivel ADM1 (departamentos) y ADM2 (distritos) de Paraguay, con códigos oficiales.

## Reglas

- No modificar, renombrar columnas ni resguardar versiones editadas: `data/raw` es solo lectura.
- Al copiar archivos, completar `fecha de descarga` y `versión` en `data/fuentes.csv`.
- Los archivos pesados están ignorados por git (solo se versionan los README).
