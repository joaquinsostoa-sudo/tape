# ANEAES: carreras y programas acreditados y no acreditados

- **Institución:** Agencia Nacional de Evaluación y Acreditación de la Educación Superior
- **Registro:** fila `aneaes` de `data/fuentes.csv`
- **Archivos (entregados a mano, 2026-10-09):** `carreras_grado_acreditadas.xls` (567), `carreras_grado_no_acreditadas.xls` (52), `programas_posgrado_acreditados.xls` (168), `programas_posgrado_no_acreditados.xls` (5), `instituciones_acreditadas.xls` (25, casi todas de formación docente).
- Son consultas exportadas del sistema de la ANEAES; los `.xls` tienen la estructura dañada y solo abren con `xlrd` y `ignore_workbook_corruption=True`.
- Traen institución, facultad y sede (texto libre; "No aplica" cuando falta). No traen clasificador de carrera (CINE).
- `src/limpieza/aneaes.py` los une en `data/clean/aneaes_programas.parquet` con la marca `acreditada` y el nivel (grado/posgrado). Las no acreditadas traen fecha de resolución en lugar de vigencia.
