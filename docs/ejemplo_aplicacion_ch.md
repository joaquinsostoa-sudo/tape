# Ejemplo de aplicación del capital humano: una industria que exige formación específica y una que no

Fecha: 2026-10-16. Código: `src/puentes/ejemplo_ch.py` y `src/figuras/ejemplo_ch.py` (11 pruebas en `tests/test_ejemplo_ch.py`). Regla declarada antes de implementar: D31 en `docs/supuestos.md`.
Figura: `docs/figuras/ejemplo_ch_S40_S09.png`. Salidas (en `data/model/`): `ejemplo_diagnostico_S40.csv`, `ejemplo_diagnostico_S09.csv`, `ejemplo_sensibilidad_S40.csv` y `ejemplo_sensibilidad_S09.csv` (más las fichas `ejemplo_ficha_*.csv`).

**Es un ejemplo de uso, no una predicción ni una recomendación de localización.** «Lista» solo quiere decir que al distrito no le falta capital humano frente a quienes ya producen; falta cruzarlo con la densidad (lo que ya produce el distrito), la energía y la logística.

## Las dos industrias
| Industria | NBER | ¿Exige formación específica? (D28) | Productores hoy (mapa MIC 2026) |
|---|---|---|---|
| **S40 Electrónica y equipo eléctrico** | 0,44 | **Sí** | 14 distritos (30 industrias) |
| **S09 Frigoríficos y productos cárnicos** | 0,16 | **No** | 52 distritos con coordenadas (53 en el mapa; 116 industrias) |

## Cómo se aplica (D31)
1. **Dos partes por distrito:** la **base** (percentil del índice v2 a 30 km: adultos con secundaria, salud y graduados transversales accesibles) y la **formación específica** del sector (percentil del pool de graduados de técnico y grado de sus carreras, a 30 km).
2. **Referencia = los distritos que hoy ya tienen la industria.** El umbral de cada parte es el **percentil 10 de los productores**. Si hay menos de 10 productores se usa la mediana de todos los distritos.
3. **Cuatro categorías** (si la industria no exige formación específica, solo cuenta la base y las categorías son «lista» y «falta base»):

| Categoría | Qué significa | Qué hace falta |
|---|---|---|
| **Lista** | Base y formación específica en el umbral de los productores o por encima | No le falta capital humano |
| **Falta formación específica** | La base está, la formación del sector no | Educación técnica del sector |
| **Falta base** | La formación está, la base general no | Educación general y servicios del distrito |
| **Faltan ambas** | Las dos están por debajo | El capital humano por sí solo no es el atajo: otra industria más cercana a su perfil, o traer talento |

4. **Orden:** el **mínimo** de las dos partes (el eslabón más débil). El promedio no se usa porque las partes se complementan y no se reemplazan.
5. **Brecha en graduados:** en «falta formación específica», cuántos graduados accesibles faltan para llegar al umbral (en unidades del pool ponderado por distancia, orden de magnitud).

## Electrónica (exige formación específica)
Umbrales (percentil 10 de los 14 productores): **base 71 y formación específica 77**.

| Categoría | Distritos | De los cuales ya producen hoy |
|---|---|---|
| Lista | 52 | 11 |
| Falta formación específica | 19 | 1 |
| Falta base | 8 | 1 |
| Faltan ambas | 183 | 1 |
| Sin dato (María Antonia) | 1 | 0 |

- **Dónde se podría producir mejor:** los **41 distritos «listos» que hoy no tienen electrónica**. Once son de Central y el resto, sobre todo de Cordillera (Caacupé, San Bernardino, Altos, Emboscada), Paraguarí (Yaguarón, Carapeguá, Pirayú) y Presidente Hayes, más Presidente Franco (Alto Paraná). Los primeros por el mínimo son Ñemby, Villa Elisa, San Antonio y Mariano Roque Alonso. **Los de Presidente Hayes (Nueva Asunción, Ñanawa, José Falcón, Villa Hayes) están sobrestimados**: están cerca de Asunción en línea recta, pero al otro lado del río.
- **Falta formación específica (19)**: la base es de productor, pero faltan graduados de electricidad y electrónica accesibles. Coronel Oviedo (faltan ≈ 120), Villarrica (≈ 150), Caaguazú (≈ 270), Quiindy (≈ 100), San José de los Arroyos (≈ 85). La acción es educación técnica del sector.
- **Falta base (8, todos del Alto Paraná)**: Hernandarias, Minga Guazú, Dr. Raúl Peña, Juan E. O'Leary, Los Cedrales, San Cristóbal, Santa Fe del Paraná y Yguazú tienen formación específica fuerte (78 a 86) pero base por debajo del umbral. La formación técnica ya está; lo que falta es educación general y servicios.
- **Faltan ambas (183)**: incluye Encarnación, Hohenau, Concepción y Pedro Juan Caballero.

## Frigoríficos (no exige formación específica)
Umbral de base (percentil 10 de los 52 productores): **38**. Solo cuenta la base.

| Categoría | Distritos | De los cuales ya producen hoy |
|---|---|---|
| Lista | 172 | 46 |
| Falta base | 90 | 6 |
| Sin dato | 1 | 0 |

Hay **126 distritos «listos» sin frigorífico hoy** (los mayores: Presidente Franco, Hernandarias, Areguá, Ypané, Caacupé, Villa Hayes). Los **90 que faltan base** son sobre todo de Canindeyú (16), Ñeembucú (15), Concepción (14), San Pedro (13) y Amambay (6); los más grandes: Pedro Juan Caballero, Concepción, Santa Rosa del Aguaray, Horqueta, Pilar, Curuguaty y Salto del Guairá.

## El contraste: los mismos distritos, las dos industrias
| Distrito | Base | Formación específica electrónica | Electrónica | Frigoríficos |
|---|---|---|---|---|
| Ciudad del Este | 74 | 88 | **lista** | **lista** (su formación en alimentos es baja, 28, pero esa industria no la exige) |
| Encarnación | 59 | 61 | faltan ambas | **lista** |
| Villarrica | 76 | 74 | falta formación específica (a 3 puntos del umbral) | lista |
| Coronel Oviedo | 77 | 75 | falta formación específica (a 2 puntos) | lista |
| Hohenau | 52 | 38 | faltan ambas | lista |
| Pedro Juan Caballero | 36 | 22 | faltan ambas | falta base |
| Concepción | 27 | 10 | faltan ambas | falta base |

Lectura: **Encarnación y Hohenau no están listos para electrónica pero sí para frigoríficos**, porque la electrónica exige más formación que ellos tienen. **Concepción** necesita base para cualquiera de las dos.

## Cuánto dependen las categorías de las decisiones (sensibilidad)
Distritos que cambian de categoría frente al caso principal:

| Variante | Electrónica | Frigoríficos |
|---|---|---|
| Umbral en la mediana de todos los distritos (en vez de los productores) | **95** de 263 | 41 |
| Escala de 15 km | 37 | 39 |
| Escala de 60 km | 51 | 23 |
| Reparto parejo entre sedes | 16 | 24 |

**El umbral y la escala cambian mucho el resultado.** Con la mediana de todos los distritos, por ejemplo, electrónica pasa de 52 a 115 distritos «listos». Además **69 distritos de electrónica y 52 de frigoríficos están a menos de 10 puntos de un umbral** (columna `cerca_del_umbral`): su categoría es frágil.

## Controles honestos
1. **Alrededor del 90 % de los productores salen «listos» por construcción**, porque el umbral es el percentil 10 de ellos mismos (11 de 14 en electrónica, 46 de 52 en frigoríficos). **No es evidencia de que el criterio funcione.**
2. **El puntaje no describe mejor que la población dónde están hoy las industrias.** Distritos con la industria que están en el 20 % superior: electrónica 10 por puntaje contra 12 por población; frigoríficos 23 contra 27. El mapa MIC es una foto de 2026 y la industria puede estar donde está por otras razones.
3. **La base y la formación específica se parecen mucho** (correlación de rangos 0,93 en electrónica y 0,84 en frigoríficos): las dos siguen la cercanía al Gran Asunción. La formación específica agrega información sobre todo en los márgenes.

## Límites que hay que tener presentes
- **Pocos productores:** 14 en electrónica, la mayoría del Gran Asunción, así que el umbral es el de un distrito metropolitano y exigente.
- **La formación específica viene del campo de estudio y no del sector exacto:** la de frigoríficos mezcla carreras de alimentos compartidas con otros 10 sectores y con ingeniería industrial.
- **Distancia en línea recta:** Nueva Asunción queda a 3,8 km de Asunción pero al otro lado del río.
- **Foto de 2026 contra flujo de graduados 2013-2025.**
- Los percentiles son relativos a los distritos de Paraguay. Resultados como asociación, no causalidad.

## Qué falta para convertirlo en herramienta
1. Cruzarlo con **densidad, energía y logística** (D16): «lista» no es «conviene producir».
2. **Tiempo de viaje por ruta** en lugar de línea recta, al menos para el Chaco.
3. **Afinar las carreras por industria** (más allá del campo de estudio).
4. **Más productores de referencia** (por ejemplo, otros años del mapa o proyectos de maquila) para que el umbral sea más estable.
