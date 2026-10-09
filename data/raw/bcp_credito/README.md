# Crédito por actividad

- **Institución:** BCP
- **Registro:** fila `bcp_credito` de `data/fuentes.csv`
- **Acceso:** Boletín estadístico
- **Cobertura:** Mensual 2020-2026

## Qué esperamos aquí

Archivos esperados: series mensuales de crédito por sector (boletín estadístico, Excel).

## Reglas

- No modificar, renombrar columnas ni resguardar versiones editadas: `data/raw` es solo lectura.
- Al copiar archivos, completar `fecha de descarga` y `versión` en `data/fuentes.csv`.
- Los archivos pesados están ignorados por git (solo se versionan los README).

## Archivos presentes (2026-10-09)
`Boletin_Bancos_Ago26.xlsm` (33 MB), entregado a mano. Hoja `5. Cred. por sector`: cartera total en Gs por 13 sectores (incluye CONSUMO y VIVIENDA) y por banco, solo para 2026/08. Hoja `6. Cred. por acti`: por actividad económica (cultivo de soja, arroz, etc.). Las demás hojas son tablas dinámicas de una sola fecha: la serie histórica requiere otros boletines.

**Serie mensual (2026-10-09):** `Creditos_bcp_sector_082026.xlsx`, extraída por el usuario desde el modelo del boletín: cartera total en Gs por sector (13) y banco, mes a mes. La fecha figura solo en la primera fila de cada mes (rellenar hacia abajo). La serie por actividad económica se descartó: trae solo tres actividades sueltas.
