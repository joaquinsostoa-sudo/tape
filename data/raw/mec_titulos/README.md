# Registro de títulos (MEC)

Registro: fila `mec_titulos` de `data/fuentes.csv`. Portal: https://datos.mec.gov.py/data/registros_titulos (formulario de búsqueda, licencia CC BY 4.0; sin enlace de descarga visible).

## Estructura observada (por la vista de la interfaz, 2026-10-08)
Columnas: Año, Mes, Documento, Nombre Completo, Carrera, Título, Número de Resolución, Fecha de Resolución, Número de Resolución de Suspensión, Fecha de Resolución de Suspensión, Tipo de Institución, Institución, Sexo.

Calidad que se vio en el ejemplo:
- Año aparece como 1, 2, 3...: son los primeros registros históricos y parecen mal cargados; las fechas de resolución salen como `0001-02-09`.
- `Institución` incluye la sede en el texto (`UNIVERSIDAD NACIONAL DE ASUNCIÓN - CAACUPE`) y a veces no (`... DE ASUNCIÓN`): hay que normalizar.
- `Título` repite o completa la carrera (`LICENCIADO/A EN ENFERMERIA`); `Carrera` es la variable útil (`ABOGACIA` y `DERECHO` son lo mismo).
- `Tipo de Institución`: Universidad, Instituto de Formación Docente, Extranjero.

## Privacidad
Hay nombre completo y documento de personas. TAPE solo necesita conteos por carrera, institución y mes: **descartar Documento y Nombre Completo al limpiar** y no copiar datos personales a `data/clean`.

## Qué esperamos aquí
Un CSV/XLSX con esas columnas, tal como se descargue. Si el portal no deja bajarlo, una solicitud de acceso a la información al MEC o contactar a la Dirección de Datos Abiertos.
