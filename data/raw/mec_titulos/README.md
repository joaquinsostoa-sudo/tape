# Registro de títulos (MEC)

Registro: fila `mec_titulos` de `data/fuentes.csv`. Portal: https://datos.mec.gov.py/data/registros_titulos (formulario de búsqueda, licencia CC BY 4.0; sin enlace de descarga visible).

## Archivo presente (2026-10-15)
`registros_titulos.csv.zip` (24 MB; dentro, `registros_titulos.csv` de 171 MB), bajado del portal por Joaquín. 748.043 títulos de 1966 a 2026 (2026 llega hasta octubre), 573 instituciones (`institucion_id`), 2.083 carreras y 1.028 títulos. Columnas: `anio, mes, documento, nombre_completo, carrera_id, carrera, titulo_id, titulo, numero_resolucion, fecha_resolucion, tipo_institucion_id, tipo_institucion, institucion_id, institucion, gobierno_actual, sexo`.

Calidad observada:
- **Cobertura:** hasta 2012 hay entre 1 y unos 4.700 títulos por año; en 2013 salta a 27.500. **Usar solo 2013-2025** (2026 incompleto).
- **No trae distrito ni departamento**, solo la institución. La ubicación se obtiene cruzando la institución con el listado de instituciones del MEC (`data/raw/mec_escuelas/instituciones_20261015.csv`); ver `docs/titulos_instituciones.md`.
- `institucion` a veces incluye el campus (`UNIVERSIDAD CATÓLICA ... - CAMPUS UNIVERSITARIO ALTO PARANA`) o la facultad (`UNIVERSIDAD NACIONAL DE ASUNCIÓN - DERECHO`) y la mayoría de las veces no; el mismo nombre aparece con espacios, comillas y mayúsculas distintos (2.047 nombres para 573 códigos).
- Los códigos `institucion_id` **no coinciden** con `codigo_institucion` del listado de instituciones del MEC: el cruce es por nombre.
- `tipo_institucion` mezcla mayúsculas y minúsculas (`UNIVERSIDAD` y `Universidad`).

## Privacidad (decisión de Joaquín, 2026-10-15; D17)
El archivo trae nombre completo, documento y sexo de personas. Es información pública (portal de datos abiertos del MEC, CC BY 4.0) y **se guarda completo aquí para registrar la fuente**. Reglas: (1) esta carpeta no se versiona (`data/raw/**` está en `.gitignore`; solo van el README y el MANIFEST) y **no está en el zip de datos manuales**; (2) el análisis de TAPE **no usa nombres ni documentos**: lo que sale de aquí hacia `data/clean/` son conteos por carrera, institución, año y mes; (3) no copiar el archivo fuera de esta carpeta.

## Qué esperamos aquí
Un CSV/XLSX con esas columnas, tal como se descargue. Si el portal no deja bajarlo, una solicitud de acceso a la información al MEC o contactar a la Dirección de Datos Abiertos.
