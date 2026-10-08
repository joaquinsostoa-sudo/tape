# Maquila (CNIME)

- **Institución:** MIC / CNIME
- **Registro:** fila `mic_maquila` de `data/fuentes.csv`
- **Acceso:** Web MIC / solicitud
- **Cobertura:** Mensual

## Qué esperamos aquí

Archivos esperados: listado mensual de proyectos aprobados (empresa, producto/actividad, departamento, fecha, inversión, empleo). Excel o CSV tal como se publicó, un archivo por corte.

## Reglas

- No modificar, renombrar columnas ni resguardar versiones editadas: `data/raw` es solo lectura.
- Al copiar archivos, completar `fecha de descarga` y `versión` en `data/fuentes.csv`.
- Los archivos pesados están ignorados por git (solo se versionan los README).
