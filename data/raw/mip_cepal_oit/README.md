# Matriz insumo-producto

- **Institución:** CEPAL-OIT
- **Registro:** fila `mip_cepal_oit` de `data/fuentes.csv`
- **Acceso:** Propio / solicitud
- **Cobertura:** 2024

## Qué esperamos aquí

Archivo esperado: MIP 21x21 en Excel/CSV con documentación de las actividades.

## Reglas

- No modificar, renombrar columnas ni resguardar versiones editadas: `data/raw` es solo lectura.
- Al copiar archivos, completar `fecha de descarga` y `versión` en `data/fuentes.csv`.
- Los archivos pesados están ignorados por git (solo se versionan los README).

## Archivos presentes (2026-10-09)
`Simulador-MIP-Paraguay.xlsm`, entregado a mano. Hoja `Matrices Nacionales`: MIP de 21 sectores en millones de USD; además `Exportaciones` (por sector y destino), `Empleo`, `Ingreso Laboral`, `MRIO`. Según el usuario se elaboró con el BCP; falta confirmar autoría, año de la matriz y supuestos.
