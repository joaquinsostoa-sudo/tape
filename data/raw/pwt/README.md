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

## PWT 11.0 (2026-10-14)
`pwt110.xlsx` (5,8 MB, descarga manual de Joaquín desde https://www.rug.nl/ggdc/productivity/pwt/): 185 países, 1950-2023, hoja `Data`. Reemplaza a `pwt1001.xlsx` (PWT 10.01, hasta 2019), que se conserva.
Frente a 10.01: el capital humano es casi igual (correlación 0,9985); el stock de capital real `rnna` se reestimó (correlación 0,98, cociente mediano 1,21); empleo y población, iguales.
Con PWT 11.0 el capital humano, el capital por trabajador y el salario llegan hasta 2023. `src/limpieza/dotaciones.py` usa 11.0 si existe y, si no, 10.01.
Salario medio: remuneración media por trabajador en USD corrientes de mercado = `labsh` × `cgdpo` × `pl_gdpo` / `emp` (promedio de toda la economía; 139 países).
