# Penn World Table

- **Institución:** Groningen Growth and Development Centre (Univ. Groningen)
- **Registro:** fila `pwt` de `data/fuentes.csv`
- **Acceso:** Descarga directa (Excel/Stata)
- **Cobertura:** 1950-2019/2023 según versión (verificar)

## Qué esperamos aquí

Archivos esperados:
- `pwt{versión}.xlsx` (hoja `Data`) o `pwt{versión}.dta`

Descarga: `src/descargas/pwt.py`; si falla, bajar desde la URL de fuentes.csv y dejar el archivo aquí.

## Reglas

- No modificar, renombrar columnas ni resguardar versiones editadas: `data/raw` es solo lectura.
- Al copiar archivos, completar `fecha de descarga` y `versión` en `data/fuentes.csv`.
- Los archivos pesados están ignorados por git (solo se versionan los README).
