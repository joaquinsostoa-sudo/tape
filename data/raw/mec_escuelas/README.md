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

## Archivos agregados (2026-10-15)
- `instituciones_20261015.csv` (19 MB): listado de instituciones y establecimientos del portal, años **2012, 2014, 2015, 2016 y 2018** (no hay años recientes). 54.644 filas; en 2018, 22.866 filas y, de ellas, 819 de educación superior (664 establecimientos, 430 instituciones, 133 distritos, un campus por fila). Trae nombre de la institución, nivel o modalidad (`niveles_modalidades`: bachillerato técnico, formación profesional, iniciación profesional agropecuaria, etc.), departamento y distrito con código. UTF-8. Es el archivo para ubicar las instituciones del registro de títulos.
- `establecimientos_2023_15102026_1549.xlsx` y `establecimientos_2022_15102026_1551.xlsx`: stock de establecimientos de cada año (8.847 y 9.151 filas; 8.890 códigos distintos en 2022). **Solo código, ubicación y coordenadas; sin nombre ni nivel.** Sirven para contar escuelas por distrito y zona; no sirven para ubicar universidades (solo 20 de los 157 códigos de educación superior de 2018 aparecen en 2023). Los nombres de archivo vienen del portal (la hora 15:49 es 2023 y 15:51 es 2022).
- `matriculaciones_departamentos_distritos_20261015.csv`: matriculados 2023 por distrito, zona y tipo de gestión (oficial, privado, privado subvencionado), hombres y mujeres. Un solo año, 263 distritos, 1.548.553 matriculados. **Sin nivel educativo ni carrera.**
