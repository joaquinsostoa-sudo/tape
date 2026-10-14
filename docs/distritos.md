# Equivalencia de distritos: Censo 2011 ↔ límites 2012 ↔ ciudades 2022

Código: `src/puentes/distritos.py` · salidas (en `data/clean/`, no versionadas): `puente_distritos_2012.csv` (248 polígonos de 2012) y `puente_distritos_2022.csv` (263 ciudades del Censo 2022 / mapa MIC).

## Para qué
El Censo Económico 2011 (datos de 2010) trae 234 distritos con nombre y sin código; los límites de 2012 tienen 247 polígonos y el Censo 2022 tiene 263 distritos. Para comparar el mapa MIC 2026 con el censo hay que llevar todo a una **unidad común: el distrito del Censo 2011** (`unidad_2011`). Un distrito posterior se asigna a sí mismo si ya existía, o a su distrito padre si se creó después.

## Cómo
1. **2011 ↔ 2012.** Emparejamiento óptimo uno a uno de los nombres dentro de cada departamento (similitud sobre nombres normalizados y sobre una llave fonética que ignora títulos, «Ex ...», y las grafías guaraníes YBY/YVY, YPEJHU/YPE JHU; y 0,85 si las palabras de un nombre están contenidas en el otro, p. ej. San Pedro ⊂ San Pedro del Ykuamandiyú).
2. Los polígonos de 2012 sin pareja son **distritos nuevos**: su padre es el vecino (de 2011) con el que comparten la frontera más larga. Confianza `baja`, a revisar por el equipo.
3. **2022 ↔ 2012.** Igual por nombres. Las ciudades de 2022 sin pareja son nuevas: su padre es el polígono de 2012 que contiene su punto (`baja`).
Confianza: alta si la similitud es ≥ 0,9, media entre 0,7 y 0,9, baja si el padre se infiere por vecindad o por punto.

## Resultado
| | Filas | igual | nuevo desde padre | otros |
|---|---|---|---|---|
| 2012 | 248 polígonos | 234 | 12 | 2 fragmentos de San Juan del Paraná (< 1 km²) |
| 2022 | 263 ciudades | 234 | 28 | 1 sin correspondencia (María Antonia, Paraguarí: su punto cae fuera de los límites) |

Los **234 distritos del censo tienen exactamente un polígono de 2012** (comprobado en un test). 222 filas de 2012 y 222 de 2022 son de confianza alta.

## Control con el mapa MIC
Con el puente, las **17.080 industrias del MIC** quedan asignadas a una unidad de 2011 (ninguna sin unidad). Entre unidades, el número de industrias del MIC 2026 y las unidades manufactureras del censo (2010) tienen una correlación de rango de **0,81** (231 unidades con industrias en el MIC, 160 con manufactura en el censo; totales 17.080 contra 21.134). Es la señal de que ambas fuentes ven la misma geografía industrial.

## Hallazgos y límites
- **«Bella Vista» es un solo objeto de dos partes en los límites de 2012** (Amambay e Itapúa): se separó por departamento. No era un distrito faltante en el censo; faltaba la segunda parte.
- Dos polígonos de San Juan del Paraná son fragmentos de 0,24 y 0,15 km²: se tratan como parte del distrito principal.
- **Padres de los distritos nuevos por frontera, no por historia legal.** El criterio de la frontera más larga puede equivocarse (por ejemplo, Liberación → General Resquín, Yabebyry → Ayolas, Villa Franca → San Juan Bautista de Ñeembucú, Dr. Raúl Peña → Naranjal). Las leyes de creación de distritos darían el padre exacto: el equipo debe validar las 12 + 28 filas `baja`.
- María Antonia (Paraguarí) queda sin unidad; ya había un problema de coordenadas con ella en el mapa MIC.
- Los distritos creados entre 2010 y 2012 que no estaban en el censo se agregan a su padre: pierden resolución, pero el backtest se hace en la unidad de 2011.
