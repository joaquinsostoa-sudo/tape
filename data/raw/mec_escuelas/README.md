# Establecimientos escolares

- **Institución:** MEC
- **Registro:** fila `mec_escuelas` de `data/fuentes.csv`
- **Acceso:** Web del MEC
- **Cobertura:** Foto actual

## Qué esperamos aquí

Archivo esperado: listado de establecimientos con ubicación (distrito/coordenadas), nivel y tipo.

## Reglas

- No modificar, renombrar columnas ni resguardar versiones editadas: `data/raw` es solo lectura.
- Al copiar archivos, completar `fecha de descarga` y `versión` en `data/fuentes.csv`.
- Los archivos pesados están ignorados por git (solo se versionan los README).
