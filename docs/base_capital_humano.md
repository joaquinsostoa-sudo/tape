# Base de capital humano por distrito

Fecha: 2026-10-16. Código: `src/puentes/base_capital_humano.py` (5 pruebas en `tests/test_base_capital_humano.py`). Reglas declaradas antes de construir: D29 en `docs/supuestos.md`, con las decisiones de Joaquín.
Salidas (en `data/clean/`): `base_capital_humano_distrito.csv` (una fila por distrito) y `base_capital_humano_control.csv`.

## En palabras simples
La **base** de capital humano de un distrito dice cuánta preparación general tiene la gente, sin mirar un sector en particular. Tiene tres partes:
1. **Escolaridad:** qué porcentaje de los adultos de 25 a 64 años terminó la secundaria (12 o más años de estudio).
2. **Red de salud:** qué tan cerca está el establecimiento de salud más cercano (en kilómetros).
3. **Carreras transversales:** cuántos graduados de derecho, contabilidad, administración, economía y marketing (técnico y grado) hay por cada 1.000 habitantes.

Cada parte se convierte en un **percentil entre los 263 distritos** (0 es el peor y 100 el mejor; en la distancia, estar más cerca es mejor) y el **índice es el promedio simple de las tres**. Las tres partes también se guardan por separado.

## Cómo se estimó la escolaridad
No hay dato de secundaria por distrito (el Censo 2022 por distrito no está en nuestras tablas). Se estimó así: la EPHC 2022-2025 da la tasa **urbana y rural de cada departamento**, y se pesan con el **porcentaje urbano de la matrícula 2023 del distrito**:

> tasa del distrito = % urbano × tasa urbana del departamento + (1 − % urbano) × tasa rural del departamento

Por qué esta fórmula: en la EPHC la diferencia urbano-rural es enorme (62 % contra 32 % en el país; 49 % contra 24 % dentro de Concepción), y la proporción urbana de la matrícula es una señal de cuánta población de cada distrito vive en cada área. Ejemplos: Concepción (ciudad, 88 % urbano) 47,5 %; San Lázaro, que incluye Vallemí (7 % urbano), 25,9 %; Ciudad del Este 52,4 %; Asunción 77,2 %.

**Es una estimación y no un dato.** Supone que dentro de un departamento y un área la tasa es igual en todos los distritos y que el % urbano de la matrícula aproxima el de la población. Se reemplaza cuando consigamos el nivel educativo del Censo 2022 por distrito, y entonces se mide cuánto se equivocó.

## Control
| Qué se mide | Resultado |
|---|---|
| Distritos | 263 |
| Con estimación de escolaridad | 255. Los 8 que faltan son los de **Boquerón y Alto Paraguay**: la EPHC no los cubre (el código 15 suma unas 98.000 personas, es Presidente Hayes solo). No se imputan. |
| Índice parcial (falta una parte) | 9: los 8 del Chaco y **María Antonia** (sin coordenadas, sin distancia a salud). Quedan marcados `parcial` y se calculan con las dos partes disponibles. |
| Promedio de los distritos frente a la EPHC departamental | Diferencia de **−3,8 a +1,6 puntos** (mayor desvío: Canindeyú −3,8; Concepción −2,3). Se informa en `base_capital_humano_control.csv` y no se reescala. |
| Correlación entre los percentiles de las partes | escolaridad–salud 0,37; escolaridad–transversales 0,27; salud–transversales 0,28 (miden cosas distintas) |

**Resultado:** el índice (sede principal) va de 1,8 a 94,1. Los más altos son Pilar, San Lorenzo, San Ignacio, San Estanislao, Luque, Asunción, Fernando de la Mora y Caacupé; los más bajos son distritos de Canindeyú (Laurel, Maracaná, Puerto Adela, Yby Pytá) y San Vicente Pancholo. 29 distritos tienen índice mayor a 60 y 113 menor a 30. Entre los dos escenarios de sede el índice de **27 distritos** cambia más de 10 puntos.

## Límites que hay que tener presentes
1. **La tercera parte casi no varía:** solo **26 de los 263 distritos** (53 en el escenario de reparto parejo) tienen graduados transversales ubicados, porque los títulos se asignan a la sede de la institución. Con el 90 % de los distritos en cero, **cualquier valor positivo salta al percentil 90**: Eusebio Ayala, con unos 4 graduados (0,2 por mil), queda entre los diez mejores. En la práctica esta parte funciona como «hay una sede de educación superior en el distrito». Es una consecuencia de usar percentiles con una variable casi toda en cero, y queda para que Joaquín decida si se cambia (por ejemplo, usar el nivel por habitante en vez del percentil, o una marca de sí o no).
2. **Para los empates se eligió el valor más bajo** (los ceros quedan abajo). Con el promedio de los empates los ceros quedaban en el percentil 45, a mitad de tabla, e inflaban a los distritos sin graduados; se corrigió antes de documentar. Es una decisión de implementación que no estaba en la declaración.
3. **La red de salud es parcial:** 212 establecimientos del mapa MIC (IPS y Ministerio de Salud) en 125 de los 263 distritos. La distancia es en línea recta desde el punto de la ciudad del distrito, no por camino. Es la parte con más error en distritos grandes.
4. **La escolaridad es una estimación** (ver arriba) y supone igualdad dentro de departamento y área.
5. **Los percentiles son relativos** a los distritos de Paraguay: un 80 no significa un nivel absoluto.
6. **El índice mezcla partes de naturaleza distinta** con pesos iguales por decisión de Joaquín; con el 51 % de los títulos ubicado con confianza baja (D17), la tercera parte hereda esa incertidumbre.
7. Resultados como asociación, no causalidad.

## Cómo se usa
Es la «base» sobre la que se apoya el capital humano específico de `docs/carrera_sector.md`: la base general del distrito más la formación por sector (técnico y grado). Para la Fase 2 son columnas por distrito (`escolaridad_pct`, `salud_km`, `transversal_x1000_*`, `indice_*`), con la marca `parcial` donde corresponde.

## Qué falta
1. El **nivel educativo del Censo 2022 por distrito** (INE) para reemplazar la estimación y medir su error.
2. Un **listado completo de establecimientos de salud** (hoy son 212).
3. Decidir sobre el límite 1 (tercera parte).
