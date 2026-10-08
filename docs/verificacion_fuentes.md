# Verificación de fuentes de Fase 1 (tarea 0.2)

Fecha: 2026-10-08. Método: consulta directa a las páginas oficiales, a la API de Harvard Dataverse y a la API del Banco Mundial, y pedidos HEAD a las URLs de descarga. Las licencias se leyeron de los metadatos o de las páginas; **no es asesoría legal**, y el uso comercial de BACI y del resto debe confirmarse con el texto de cada licencia (la propuesta comercial lo exige).

## Resumen

| Fuente | Versión vigente | Último año | Licencia | Descarga automática |
|---|---|---|---|---|
| BACI (CEPII) | **V202601** (30-ene-2026) | **2024** (todas las revisiones HS) | Etalab 2.0 | Sí. `BACI_HS92_V202601.zip`, **2,3 GB**, HTTP 200 |
| Atlas (Growth Lab) | Dataverse v18 (HS92), publicado 2026-04-22 | 2024 | **CC0 1.0** | Sí, API de Dataverse |
| WDI (Banco Mundial) | API v2 | Según indicador | CC BY 4.0 | Sí; los 13 indicadores del plan existen |
| Penn World Table | **11.0** (7-oct-2025) | **2023**, 185 países | CC BY 4.0 | Parcial: el enlace directo devolvió 403 a una consulta automática; probar con GET o bajar a mano |
| LPI | Ediciones 2007–2023 (encuesta, **cerrada**); ahora "LPI 2.0" (2023–2024) | 2023 | Por confirmar | Serie por WDI (`LP.LPI.OVRL.XQ`); el portal bloquea lectura automática (403) |
| Concordancias UNSD (HS↔CPC 2.1, CPC 2.1↔CIIU 4) | Vigentes | — | Uso libre con cita | Sí, HTTP 200 |
| Concordancias WITS (HS↔CIIU) | — | — | Uso libre con cita | Sí, HTTP 200 |
| ILOSTAT | — | — | **No confirmada** | Bulk `.csv.gz`; falta el código del indicador |

## Diferencias con el documento técnico

1. **BACI**: el "1995–2024 (?)" se confirma. HS92 cubre 1995–2024. Hay siete revisiones (HS92, 96, 02, 07, 12, 17, 22).
2. **PWT**: la versión es 11.0 (no 10.01) y llega a 2023. El panel 2000–2020 queda cubierto.
3. **LPI**: la encuesta terminó en 2023. Para Paraguay WDI trae 2007, 2010, 2012, 2014, 2016, 2018 y 2022 (corresponde a la edición 2023). La cobertura es bienal e irregular, y hay que fijar una regla de imputación.
4. **HS→CIIU Rev.4**: **WITS solo trae HS→CIIU Rev.2 y Rev.3, no Rev.4.** UNSD no publica un puente directo HS→CIIU 4. El camino oficial es HS→CPC 2.1→CIIU 4, y la tabla HS↔CPC 2.1 de UNSD solo apareció para **HS 2012 y HS 2017**. Hay que llevar HS92 a HS2012/2017 con las tablas de conversión de revisión (ver abajo). Es una cadena de tres pasos y cada uno suma ambigüedad.
5. **Atlas**: el archivo `hs92_country_product_year_4.csv` (431 MB) y el `_6` (968 MB) **ya traen** exportaciones, RCA, PCI, COG, distancia, ECI y COI. Sirven para contrastar nuestro cálculo propio de RCA y densidad. Existen además `Product Space Networks` y `Growth Projections and Complexity Rankings`, y el dataset de **tablas de conversión HS92↔HS96↔HS02↔HS07↔HS12↔HS17↔HS22 con pesos** (CC0), que es lo que necesitamos para la cadena.
6. **Atlas, tamaño**: los archivos bilaterales por año pesan ~14 GB. No hacen falta: BACI cubre lo bilateral.
7. **Licencias**: Atlas es CC0, lo más permisivo. BACI usa Etalab 2.0 (exige citar la fuente; su compatibilidad con uso comercial hay que confirmarla leyendo el texto). ILOSTAT sigue sin confirmar.

## Pendiente de esta tarea
- Confirmar con GET la URL de PWT 11.0 (`dataverse.nl/api/access/datafile/554105`, Excel).
- Código del indicador de ILOSTAT (empleo por rama CIIU Rev.4) y sus términos de uso.
- Confirmar si UNSD publica HS2022/HS2007 ↔ CPC 2.1 (la prueba de URL de HS2022 dio 404, no significa que no exista).
- Texto de la licencia Etalab 2.0 y términos de LPI 2.0.
