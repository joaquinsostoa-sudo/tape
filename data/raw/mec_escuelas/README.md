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

## Archivos presentes (2026-10-09)
- `establecimientos_2012.pdf`: establecimientos escolares 2012, 635 páginas, impreso el 19/09/2014. Trae distrito, coordenadas y latitud/longitud. El nombre dice 2012 aunque se esperaba 2023.
- `instituciones_2018.csv`: 165 instituciones, año 2018, 158 de educación superior. Sin coordenadas y con cobertura incompleta (la UNA aparece solo con sus filiales del interior; su sede está en San Lorenzo). Codificación latin-1.
