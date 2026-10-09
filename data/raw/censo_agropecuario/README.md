# Censo Agropecuario Nacional 2022 (CAN 2022)

- **Institución:** Ministerio de Agricultura y Ganadería (MAG); confirmar organismo ejecutor y licencia
- **Registro:** fila `censo_agropecuario` de `data/fuentes.csv`
- **Archivo (entregado a mano, 2026-10-09):** `CAN2022_Volumen_I.xlsx`, 78 cuadros más un índice.

## Qué trae
Tabulados por **departamento y tamaño de finca** (no por distrito), con comparación 2008-2022 en varios cuadros: fincas y superficie, tenencia, uso de la tierra, cultivos con superficie y producción (algodón, soja, trigo, maíz, mandioca, arroz, yerba, tomate, frutas, etc.), ganadería (cabezas por especie), agua e infraestructura, maquinaria, asistencia técnica, crédito, insumos y destino de la venta.

## Límites
- Nivel departamental: sirve como dato grueso para el módulo territorial, sin desagregar al distrito.
- El rendimiento no viene dado; se calcula producción / superficie por cultivo y departamento.
- Hojas en formato de tabla de publicación (encabezados en varias filas): requieren extracción cuidadosa.
- Pendiente: confirmar si el Volumen II u otro tomo trae datos por distrito.

## Fincas por distrito (agregado 2026-10-09)
- `CAN2022_fincas_por_distrito.xlsx` (129 KB): cantidad de fincas y superficie (ha) por **distrito y estrato de tamaño de finca**, una hoja por departamento (17, sin Capital). Código de distrito de 4 cifras (departamento + distrito).
- **Verificado:** los distritos suman exactamente el total de cada departamento; esos totales son idénticos al Cuadro 1 del Volumen I (17 de 17); el país suma 291.497 fincas y 30.401.660 ha.
- Para anonimizar, los estratos extremos se agregan en algunos distritos ("De 1.000 y más", "(*) Estrato agregado"): los totales son comparables entre distritos, los estratos no.
- **Inconsistencia de la fuente:** en Mayor José J. Martínez (Ñeembucú, código 1210) los estratos suman 489 fincas y 12.846 ha, y el total del distrito dice 492 fincas y 22.933 ha.
- Hay 259 distritos; 14 vienen con cero fincas (principalmente distritos urbanos de Central). Asunción, Ciudad del Este, Itacuá y Nueva Asunción no tienen fila: quedan vacíos al unir con la tabla de 263 distritos del mapa MIC (no se trata como cero).
- Limpieza: `src/limpieza/can_distrito.py` -> `data/clean/can_fincas_totales.csv`, `can_fincas_estratos.csv` y `can_fincas_distrito.csv` (unión con las 263 ciudades del mapa MIC; 32 nombres distintos se resuelven con una tabla de equivalencias por código).
- Lo que **no** hay por distrito: cultivos, superficie sembrada, producción ni ganadería (solo por departamento, en el Volumen I).
