# Puente MIC (actividad específica) → CIIU → sector TAPE

Código: `src/puentes/mic_especifico.py` · salidas (en `data/clean/`, no versionadas): `puente_mic_especifico_ciiu.csv` (una fila por actividad y sector), `puente_mic_especifico_revision.csv` (cola de revisión del equipo), `industrias_distrito_sector_tape_esp.csv` (industrias por distrito y sector con el nuevo puente).

## Qué es y por qué
El visor del MIC trae tres niveles: sector (19) → subsector (73) → **actividad específica** (texto libre de cada industria; 1.744 textos distintos para las 17.080 industrias). El puente por subsector (`mic_sector.py`) reparte cada subsector con pesos estimados. La actividad específica distingue lo que el subsector mezcla (por ejemplo «panadería y confitería», «marmolería» o «tabacalera» puestas bajo otros subsectores) y es el nivel correcto para asignar cada industria a un sector TAPE antes de modelar lo territorial.

## Cómo se asigna
Reglas ordenadas sobre el texto normalizado (primera coincidencia): lo específico va antes que lo general. El texto se parte en actividades (` Y `, `/`, `,`) y cada parte se clasifica por separado; las partes comerciales o de servicio (venta, reparaciones, ferretería) no deciden. Con actividades sin ningún sector en común el peso se reparte por igual y la confianza baja a `baja`. Una actividad ambigua se hereda del subsector (carbonería); un texto genérico («fábrica», «industria») queda sin sector. Si la regla contradice al subsector se usa la regla (el texto específico informa más que un subsector mal puesto), la fila se marca `discrepancia_subsector` y la confianza baja un escalón. Sin regla: se hereda el subsector con confianza `baja`.

## Cobertura (17.080 industrias)
| Fuente | Confianza | Industrias | % |
|---|---|---|---|
| regla | alta | 9.858 | 57,7 |
| regla | media | 5.899 | 34,5 |
| regla | baja | 322 | 1,9 |
| heredado del subsector | baja | 421 | 2,5 |
| heredado del subsector | sin sector | 361 | 2,1 |
| regla (genérico) | sin sector | 219 | 1,3 |

Quedan **580 industrias sin sector** (3,4 %), contra 715 con el puente por subsector. 96 actividades (365 industrias) contradicen al subsector del MIC. La cola de revisión (`puente_mic_especifico_revision.csv`) tiene 802 actividades ordenadas por número de industrias: filas `baja`, discrepancias y heredadas.

## Efecto frente al puente por subsector (industrias por sector TAPE)
Panificados 1.337 → 1.644 (+307) y confitería y pastas 361 → 62 (−300): «panadería y confitería» (313 industrias) es una panadería. Vidrio, piedra y no metálicos +118; pinturas, limpieza y cosmética +107; cerámica y ladrillos −103; el resto cambia poco (metal +55, madera +7, muebles +12).

## Límites
- Las clases CIIU son una estimación del equipo hasta tener el CIIU oficial de cada empresa (Censo Económico 2011 o registro del MIC): se reemplazan al conseguirlo.
- **Carpintería (3.191 industrias, 19 %) queda repartida 60/40 entre carpintería de obra (1622) y muebles (3100):** el texto no dice cuál. Es la mayor fuente de incertidumbre del puente; decide el equipo si se mantiene el reparto o se asigna entera a una clase.
- Las partes comerciales (venta) se ignoran: una industria que además vende se cuenta por su actividad productiva.
- Lo que el equipo debe validar primero: las 30 filas de mayor tamaño de la cola de revisión.
