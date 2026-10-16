# Proximidad geográfica del pool de capital humano

Fecha: 2026-10-16. Código: `src/puentes/proximidad.py` (5 pruebas en `tests/test_proximidad.py`). Reglas declaradas antes de construir: D30 en `docs/supuestos.md`, con las decisiones de Joaquín.
Salidas (en `data/clean/`): `proximidad_distrito.csv` (una fila por distrito), `proximidad_graduados_sector.csv` (pool de graduados por sector, distrito, escenario y escala) y `proximidad_control.csv`.

## En palabras simples
La gente no siempre trabaja donde vive o estudió: se mueve por zonas aledañas. Por eso lo que hay en un distrito (graduados, sedes de educación superior, adultos con secundaria, establecimientos de salud) **también cuenta para los distritos cercanos**, con un peso que baja a medida que se alejan.

> pool del distrito = suma, sobre todos los distritos, de (lo que hay allí) × exp(− distancia / escala)

La **escala** dice qué tan lejos llega la gente. No se puede calibrar con datos (la EPHC no pregunta por traslado al trabajo), así que se publican **tres escalas**: 15, 30 (la principal) y 60 km. En palabras: con cada escala el aporte de un distrito se reduce a la mitad cada **10, 21 y 42 km**, respectivamente.

Es **disponibilidad y no ocupación**: una persona cuenta en varios distritos, así que los pools de distritos distintos **no se pueden sumar**.

## Qué se midió
| Oferta | De dónde sale |
|---|---|
| Graduados de técnico y grado | `titulos_distrito.csv` y `titulos_sector_distrito.csv` (transversales, total y por sector con cuenta completa), en los dos escenarios de sede |
| Sedes de educación superior | pares (institución, distrito) distintos del listado del MEC 2018 y ANEAES: 813 en 134 distritos (hasta 162 en un distrito) |
| PEA con secundaria completa | PEA 2022 × escolaridad estimada del distrito (aproximación: la tasa es de 25 a 64 años y la PEA de 15 y más) |
| Red de salud | 212 establecimientos del mapa MIC |

También se guarda la distancia a la sede de educación superior más cercana: mediana 0 km (el 51 % de los distritos tiene una), p90 42 km y máximo 143 km.

## Qué cambia: ejemplos (pool de graduados transversales, sede principal)
| Distrito | Propios | 15 km | 30 km | 60 km |
|---|---|---|---|---|
| Itauguá | 0 | 15.197 | 33.651 | 53.743 |
| Eusebio Ayala | 4 | 1.832 | 12.036 | 34.385 |
| Encarnación | 5.543 | 5.545 | 5.628 | 7.769 |
| Concepción | 795 | 795 | 871 | 3.482 |
| Horqueta | 0 | 51 | 267 | 2.839 |
| Arroyito | 0 | 7 | 124 | 2.080 |
| San Lázaro (incluye Vallemí) | 0 | 0 | 6 | 329 |
| Filadelfia | 0 | 33 | 63 | 176 |

Antes, solo 26 distritos tenían graduados transversales. Con la proximidad, casi todos reciben algo de pool (251 de 263 a 15 km). Eso **resuelve el problema de la tercera parte de la base**, que era casi un sí o no.

Para un sector concreto, por ejemplo Farmacéutica (S31, técnico y grado, escala de 30 km): Asunción tiene 4.723 graduados propios y un pool de 8.982; Eusebio Ayala, que no tiene ninguno, tiene un pool de 2.276; Concepción, 10.

## Los dos índices (se publican ambos, sin elegir uno)
- **v1** (D29): escolaridad propia, distancia a salud y graduados transversales por 1.000 habitantes del propio distrito.
- **v2** (D30): promedio de pesos iguales de los percentiles de los pools de PEA con secundaria, salud y graduados transversales, por escala y escenario.

Comparación: el v1 y el v2 (30 km) se parecen poco (correlación de rangos 0,47). El v2 premia al **Gran Asunción** porque mide cantidad accesible: los 8 distritos más altos son Fernando de la Mora, Asunción, San Lorenzo, Luque, Lambaré, Ñemby, Villa Elisa y Capiatá. Concepción pasa del 78 (v1) al 27 (v2, 30 km) porque el pool que rodea a la ciudad es chico frente al del área metropolitana; Itauguá pasa de 52 a 94.

## Control
| Qué se mide | Resultado |
|---|---|
| Con escala casi cero (0,01 km) el pool coincide con la oferta propia | diferencia máxima 0,000 |
| Correlación de rangos del índice v2 entre 15 y 30 km | 0,94 |
| Entre 30 y 60 km | 0,95 |
| Entre 15 y 60 km | 0,83 |
| Distritos que cambian más de 10 puntos de índice v2 entre 15 y 60 km | **134 de 263** |
| Distrito sin pool (sin coordenadas) | María Antonia |

**La escala importa mucho para parte de los distritos**: el orden general se mantiene (0,83 a 0,95) pero la mitad de los distritos se mueve más de 10 puntos entre 15 y 60 km. Concepción, por ejemplo, sale 57 con 15 km y 16 con 60 km.

## Límites que hay que tener presentes
1. **La escala es un supuesto** y los resultados dependen de ella: por eso se publican tres.
2. **El pool mide cantidad accesible y no calidad.** Crece con la población cercana, así que el v2 favorece a las áreas metropolitanas. Es lo que se quiere para «cuántos trabajadores podría reclutar una industria», pero no para comparar la calidad del capital humano entre distritos de distinto tamaño.
3. **El decaimiento nunca llega a cero:** un distrito lejano recibe una fracción mínima de los grandes centros. Por eso «pool mayor que cero» no distingue (251 a 262 de 263 distritos); hay que mirar el valor o el percentil.
4. **El título dice dónde estudió la persona, no dónde vive.** La proximidad supone que se queda cerca de la sede; quien estudia en Asunción y vuelve a su distrito aparece en el lugar equivocado. Los títulos con ubicación de confianza baja (51 %) trasladan esa incertidumbre.
5. **Distancia en línea recta** entre los puntos de ciudad de los distritos, no por camino. En el Chaco los distritos son enormes y el punto de la ciudad no los representa.
6. **El pool de PEA con secundaria** usa la escolaridad estimada (D29) y deja afuera a los 8 distritos del Chaco sin dato (marcados `pea_secundaria_incompleta`).
7. **Las sedes** son una aproximación: una institución con sede en un distrito cuenta una, y los nombres de una misma institución en el MEC y en ANEAES pueden no unirse del todo.
8. Resultados como asociación, no causalidad.

## Cómo se usa
Para la Fase 2, la columna `pool_*` de `proximidad_distrito.csv` y `pool` de `proximidad_graduados_sector.csv` reemplazan el conteo propio del distrito, en línea con el término espacial del modelo territorial (M2). Hay que usar la escala de 30 km como principal y mostrar la sensibilidad.

## Qué falta
1. **Datos de traslado al trabajo** (el Censo 2022 podría tener lugar de trabajo o estudio): permitirían calibrar la escala.
2. **Tiempo de viaje por ruta** en lugar de línea recta: requiere una red vial ruteable que hoy no tenemos.
3. Decidir cuál índice (v1 o v2) usar en cada análisis y si el pool por habitante (áreas de captación) merece una tabla aparte.
