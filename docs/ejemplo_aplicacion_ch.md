# Ejemplo de aplicación del capital humano: una industria que exige formación específica y una que no

Fecha: 2026-10-16. Código: `src/puentes/ejemplo_ch.py` y `src/figuras/ejemplo_ch.py` (pruebas en `tests/test_ejemplo_ch.py`). Figura: `docs/figuras/ejemplo_ch_S40_S09.png`. Fichas por distrito: `data/model/ejemplo_ficha_S40.csv` y `data/model/ejemplo_ficha_S09.csv`.

**Esto es una ilustración, no un resultado ni una decisión declarada.** La regla de puntaje es simple y la elegí yo para el ejemplo; si te sirve, se formaliza y se declara antes de usarla.

## Las dos industrias
| Industria | Requisito de habilidades (NBER) | ¿Exige formación específica? (D28, corte 0,28) | Industrias hoy en el mapa MIC |
|---|---|---|---|
| **S40 Electrónica y equipo eléctrico** | 0,44 (111 productos, confianza alta) | **Sí** | 30, en 14 distritos |
| **S09 Frigoríficos y productos cárnicos** | 0,16 (25 productos, confianza alta) | **No** | 116, en 53 distritos (52 en los controles: uno sin coordenadas) |

## Cómo se aplica, en cuatro pasos
1. **¿La industria exige formación específica?** Se mira el NBER (D28).
2. **Base del distrito:** el percentil del índice v2 a 30 km (adultos con secundaria, salud y graduados transversales accesibles).
3. **Formación específica del sector:** el percentil del pool de graduados de técnico y grado de las carreras que sirven al sector, a 30 km (cuenta completa).
4. **Puntaje:** si la industria **exige**, el promedio de la base y la formación específica; si **no exige**, solo la base. Se marca cuál de las dos partes limita al distrito.

## Qué sale
**Los diez primeros son casi los mismos en las dos industrias**: todos del Gran Asunción.

| Electrónica y equipo eléctrico (exige) | Puntaje | Frigoríficos (no exige) | Puntaje |
|---|---|---|---|
| Asunción | 99,7 | Fernando de la Mora | 99,9 |
| Fernando de la Mora | 99,6 | Asunción | 99,5 |
| San Lorenzo | 99,5 | San Lorenzo | 99,4 |
| Lambaré | 98,7 | Luque | 98,6 |
| Nueva Asunción | 97,8 | Lambaré | 98,5 |
| Luque | 97,8 | Ñemby | 97,3 |
| Villa Elisa | 97,6 | Villa Elisa | 97,2 |
| Ñemby | 97,5 | Capiatá | 97,2 |
| San Antonio | 97,0 | Nueva Asunción | 97,1 |
| Capiatá | 96,5 | San Antonio | 96,7 |

La diferencia aparece **fuera de la capital**. Mismos distritos, las dos industrias (percentiles):

| Distrito | Base | Formación específica electrónica | Puntaje electrónica | Formación específica frigoríficos | Puntaje frigoríficos | Parte que limita electrónica |
|---|---|---|---|---|---|---|
| Ciudad del Este | 74 | **88** | 81 | 28 | 74 | base |
| Encarnación | 59 | 61 | 60 | 63 | 59 | base |
| Villarrica | 76 | 74 | 75 | 85 | 76 | formación específica |
| Coronel Oviedo | 77 | 75 | 76 | 75 | 77 | formación específica |
| Hohenau | 52 | 38 | 45 | 41 | 52 | formación específica |
| Pedro Juan Caballero | 36 | 22 | 29 | 45 | 36 | formación específica |
| Concepción | 27 | 10 | 19 | 15 | 27 | formación específica |

Cómo se lee, con dos casos:
- **Ciudad del Este** tiene mejor formación específica en electricidad y electrónica (88) que base general (74): para electrónica sube (81); para frigoríficos su formación en alimentos es baja (28), pero como esa industria no la exige, **no le resta** (74).
- **Concepción** tiene base baja (27) y formación específica aún más baja para electrónica (10): lo que le falta, para esa industria, es sobre todo **formación específica**. Para frigoríficos solo importa la base.

Por la misma razón, algunos distritos suben o bajan de lugar según la industria: **mejoran cuando la industria exige formación** Pilar (lugar 125 de 262 en electrónica contra 189 en frigoríficos), Mbaracayú, Humaitá, Ñacunday y Domingo Martínez de Irala, porque tienen más formación específica que base; **mejoran cuando no la exige** distritos de Itapúa como La Paz, Alto Verá, Natalio y Mayor Otaño, porque su base es mejor que su formación específica.

## Dos controles honestos
1. **El puntaje no describe mejor que la población dónde están hoy las industrias.** Distritos con la industria que están en el 20 % superior:

| Industria | Con industria hoy | Por puntaje | Por población | Por base | Por formación específica |
|---|---|---|---|---|---|
| Electrónica | 14 | 11 | 12 | 10 | 12 |
| Frigoríficos | 52 | 23 | 27 | 23 | 24 |

La industria está donde hay más gente, y el puntaje sigue en buena medida al tamaño. **Esto no valida el puntaje ni lo descarta**: el mapa MIC es una foto de 2026 (un stock) y la industria puede estar donde está por muchas otras razones.
2. **La base y la formación específica se parecen demasiado** (correlación de rangos 0,93 en electrónica y 0,84 en frigoríficos): las dos siguen la cercanía a los polos del Gran Asunción, porque los graduados están en las sedes de las instituciones. Ningún distrito tiene base alta (60 o más) con formación específica baja (menos de 50), y solo 6 tienen formación alta con base baja (Pilar y distritos del Alto Paraná alrededor de Ciudad del Este). **La formación específica agrega información sobre todo en los márgenes**, no en el ranking general.

## Límites que hay que tener presentes
- **La regla de puntaje es ilustrativa** (promedio simple, 30 km, sede principal); con otra regla, otra escala o el reparto parejo los resultados cambian.
- **La formación específica de los frigoríficos mezcla carreras de alimentos compartidas con los otros 10 sectores de alimentos** y con ingeniería industrial: el cruce llega al campo de estudio y no distingue un frigorífico de una lechería. En electrónica mezcla electricidad, electrónica e ingeniería industrial.
- **Distancia en línea recta:** Nueva Asunción, en el Chaco, queda a 3,8 km de Asunción pero **al otro lado del río**; por camino está bastante más lejos. Por eso aparece entre los 5 primeros en electrónica con 3.172 habitantes. En el Chaco y en distritos con ríos de por medio la distancia en línea recta sobrestima la cercanía real.
- **Foto de 2026 contra flujo de graduados 2013-2025**, no es una serie; el mapa MIC es un stock.
- Resultados como asociación, no causalidad. No es una predicción de dónde conviene instalar una industria.

## Qué hace falta para convertirlo en una herramienta
1. Decidir la **regla de combinación** (promedio, mínimo de las dos partes, o umbral por parte) y declararla antes de usarla.
2. Reemplazar la distancia en línea recta por **tiempo de viaje por ruta**, al menos para el Chaco.
3. Afinar las carreras por industria (más allá del campo de estudio).
4. Incorporar la **brecha** explícita (qué falta y cuánto) y las otras capas (energía, logística) como diagnóstico, según D16.
