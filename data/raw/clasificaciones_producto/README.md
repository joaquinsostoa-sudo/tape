# Clasificaciones de productos

- `lall/qehwps44.pdf` (145 KB, descargado el 2026-10-13): Lall, S. (2000), «The Technological Structure and Performance of Developing Country
  Manufactured Exports, 1985-98», QEH Working Paper 44, Queen Elizabeth House, Universidad de Oxford
  (https://www.qeh.ox.ac.uk/sites/default/files/pdf_docs/qehwps44.pdf). El Anexo, Tabla 1 (páginas 34 y 35) lista 230 códigos SITC Rev.2 de 3 dígitos
  en diez subgrupos (primarios; manufacturas basadas en recursos agropecuarias y otras; tecnología baja textil y otras; media automotriz, de proceso y de
  ingeniería; alta electrónica y otras). No hay versión en formato de datos: `src/puentes/clasificacion_lall.py` la lee del PDF por la posición de las columnas.
  Licencia: documento de trabajo académico, de acceso libre; citar la fuente.
- Salida: `data/clean/clasificacion_lall_hs4.csv` (HS92 de 4 dígitos con clase, bloque y confianza por fila; ver `docs/clasificacion_lall.md`).
