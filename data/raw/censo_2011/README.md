# Censo Económico Nacional 2011

- **Institución:** INE
- **Registro:** fila `censo_2011` de `data/fuentes.csv`
- **Acceso:** Web del INE / solicitud
- **Cobertura:** 2011

## Qué esperamos aquí

Archivos esperados: establecimientos por actividad CIIU y distrito (tabulados o microdatos) del censo 2011.

## Reglas

- No modificar, renombrar columnas ni resguardar versiones editadas: `data/raw` es solo lectura.
- Al copiar archivos, completar `fecha de descarga` y `versión` en `data/fuentes.csv`.
- Los archivos pesados están ignorados por git (solo se versionan los README).

Datos del censo 2011: se recopilan sector farmaceutico de varios distritos.

## Archivos
- `49d4bCEN2011_DIST_CUADRO_1.xlsx` (0,8 MB, descargado a mano por el equipo el 2026-10-14): Cuadro 1 del Censo Económico Nacional 2011 (datos del año 2010). Unidades económicas, personal ocupado por sexo, remuneraciones, gastos por compras e ingresos por suministro, por departamento, distrito, sector (Industria, Comercio, Servicios) y rama CIIU. 234 distritos, sin código de distrito. Limpieza: `src/limpieza/censo_2011.py` -> `data/clean/censo2011_distrito_rama.csv` y `censo2011_departamento_rama.csv`; detalle y límites en `docs/censo_2011.md`.

