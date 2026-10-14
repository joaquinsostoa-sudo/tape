# Puente Censo Económico 2011 → CIIU Rev.4 → sector TAPE

Código: `src/puentes/censo_sector.py` · salidas (en `data/clean/`, no versionadas): `puente_censo2011_sector.csv` (una fila por código del censo y sector, con peso y confianza) y `censo2011_distrito_sector_tape.csv` (unidades, ocupados, remuneraciones, gastos e ingresos por distrito y sector TAPE).

## Método
1. El código del censo (228 códigos de 2 y 3 dígitos) se busca como prefijo entre las clases de 4 dígitos de la CIIU Rev.4 de la ONU. Si no hay ninguna clase con ese prefijo (códigos nacionales como 610, 620, 780, 800 o 870), se usa la división. Un código de 2 dígitos es el residual que el INE agrupó por reserva estadística: toma todas las clases de la división. Comercio no tiene clases en la concordancia (no produce bienes): se usan los prefijos de la taxonomía TAPE.
2. **Cada clase pesa lo mismo**; el peso de un sector es la fracción de clases que caen en él. Es neutro a propósito: no se usó ninguna fuente posterior a 2010 (por ejemplo la composición del mapa MIC 2026) para repartir, porque contaminaría el backtest territorial.
3. Confianza: `alta` si todas las clases caen en un sector; `media` si hay dos sectores o el código nacional no tiene grupo internacional exacto; `baja` si hay más de dos o es un residual de dos dígitos.
4. Las unidades de cada distrito se reparten entre sectores por el peso; el residual sin código («Otras actividades de industria», etc.) queda como `RESIDUAL_<sector del censo>`. Las 224.242 unidades del censo quedan asignadas (la suma se conserva).

## Inconsistencia señalada, no corregida en silencio
El censo usa una **adaptación nacional de la CIIU Rev.4**: la mayoría de los grupos de 3 dígitos coincide con la internacional, pero **no 107, 109, 111, 112, 202 y 209**. Se resuelven por el nombre de la rama (`DESVIACIONES`):
| Código | Nombre en el censo | Qué es en la CIIU internacional | Tratamiento |
|---|---|---|---|
| 107 | alimentos preparados para animales | 108 (piensos) | 1080, confianza alta |
| 109 | otros productos alimenticios n.c.p. | todo el grupo 107 (panadería, azúcar, confitería, pastas, comidas, otros) | 6 clases con peso igual, `baja` |
| 111 / 112 | bebidas alcohólicas / no alcohólicas | grupo 110 | 1101-1103 y 1104 |
| 202 | biocombustibles | no tiene clase (como en el puente HS) | 2011 (etanol), `media` |
| 209 | otros productos químicos n.c.p. | grupo 202 | 2021, 2022, 2023, 2029 con peso igual, `baja` |

## Cobertura en manufactura (21.134 unidades, divisiones 10 a 33)
| Confianza | % de las unidades manufactureras |
|---|---|
| alta | 78,2 |
| baja | 21,2 |
| media | 0,6 |

Lo que concentra la confianza baja: **109 (1.375 unidades)**, el residual de 2 dígitos de alimentos (10: 1.004), de minerales no metálicos (23: 992) y los otros minerales no metálicos (239: 756), más químicos (209: 215; 20: 129). Es el 21 % de la manufactura donde el reparto es neutro y puede estar lejos de la realidad: por ejemplo, en 109 y 10 lo esperable es que dominen las panaderías, y en 239 las olerías, pero el censo no lo dice.

## Decisión pendiente (del equipo)
Para el backtest territorial hay tres caminos con lo que no se conoce del 21 %:
- **(a)** Mantener el reparto neutro (lo que hay) y reportar la incertidumbre.
- **(b)** Repartir con la composición del mapa MIC 2026: más realista, pero **filtra información del futuro** hacia la validación; solo como sensibilidad.
- **(c)** Hacer el backtest en el nivel de grupo (varios sectores juntos) donde el reparto no importa: por ejemplo «alimentos» o «minerales no metálicos» en bloque.
Recomiendo (c) para el resultado principal y (a) como detalle; (b) queda como análisis de sensibilidad, declarado como tal.
