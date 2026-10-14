# Ficha de brechas de Paraguay: prototipo con arneses y etanol (2026-10-13)

**Prototipo descriptivo.** Código: `src/modelos/ficha_brechas.py` (cálculo) y `src/figuras/ficha_brechas.py` (figura); figuras: `docs/figuras/ficha_brechas_8544.png` (arneses) y `ficha_brechas_2207.png` (etanol);
tablas: `data/model/ficha_brechas_8544.csv` y `ficha_brechas_2207.csv` (2010 y 2015). **Actualizado el 2026-10-14 con PWT 11.0** (capital humano, capital por trabajador y salario) y la capa «mano de obra barata». Pedido de Joaquín: mostrar qué le falta a Paraguay, dotación por dotación, para producir un producto.

## Qué calcula
Para un producto HS4 y un año, el percentil de Paraguay en cada dotación entre los países D8 (0 = el menos dotado, 100 = el más dotado) frente al percentil mediano de:
1. **todos los productores** (presencia D13: RCA ≥ 1 sostenido), sin Paraguay;
2. **productores de ingreso parecido** al de Paraguay (el mismo tercio de PIB per cápita), para separar la dotación del desarrollo general;
3. **productos vecinos** en el espacio producto: los 15 de mayor proximidad φ (D3), cada uno con la mediana de sus productores, ponderados por φ (estabiliza productos con pocos productores).

La **brecha** es la referencia menos la posición de Paraguay, en puntos de percentil: positiva («falta») si Paraguay está por debajo, negativa («sobra») si está por encima. Solo se informa de «falta» o «sobra» con una diferencia de al menos 10 puntos.

## Arneses y cables aislados (HS 8544; los arneses, HS 854430, son parte)
Paraguay pasó de exportaciones casi nulas (USD 0,05 millones en 2000) a USD 350 millones en 2024, con ventaja (RCA ≥ 1) desde 2014. En 2015 hay 41 productores (NIC, TUN, MDA, MAR, HND, ROU, MKD, EGY, SRB, PHL entre los que más destacan), 16 de ingreso parecido y 15 vecinos; la densidad de Paraguay (0,12) es mayor que la de 81 % de los productos que todavía no tiene.

| Dotación | Paraguay (percentil 2015) → mediana de productores | Brecha 2010: todos / ingreso parecido / vecinos | Brecha 2015: todos / ingreso parecido / vecinos |
|---|---|---|---|
| Capital humano | 41 → 65 | **falta 27** / **falta 17** / **falta 23** | **falta 24** / **falta 14** / **falta 24** |
| Capital por trabajador | 43 → 59 | **falta 15** / similar / **falta 11** | **falta 16** / **falta 11** / **falta 21** |
| Logística (LPI) | 48 → 64 | **falta 14** / similar / **falta 12** | **falta 16** / similar / **falta 20** |
| Electricidad barata | 91 → 52 | sobra 38 / sobra 33 / sobra 43 | sobra 39 / sobra 30 / sobra 38 |
| Mano de obra barata | 63 → 46 | sobra 16 / similar / sobra 20 | sobra 17 / similar / sobra 24 |
| Tierra cultivable | 94 → 60 | sobra 37 / sobra 39 / sobra 41 | sobra 34 / sobra 33 / sobra 38 |
| Agua dulce | 83 → 50 | sobra 36 / sobra 50 / sobra 34 | sobra 33 / sobra 48 / sobra 34 |

- **La brecha ya existía antes de la entrada (2010) y es parecida en 2015**: Paraguay entró en arneses con menos capital humano y menos capital por trabajador que los productores típicos. La brecha de logística desaparece al compararse con productores de ingreso parecido.
- **La mano de obra de Paraguay no es más cara que la del productor típico** (percentil 63 en mano de obra barata contra 46 de los productores): con la remuneración media por trabajador de toda la economía, el salario no explica la brecha. Sí hay productores más baratos (Nicaragua, Honduras), y esta medida es un promedio de toda la economía, no de la manufactura.
- **Lo que explica la entrada sigue sin estar en las dotaciones**: el ensamblaje de arneses es intensivo en mano de obra y entró con el régimen de maquila; el régimen fiscal es la variable que falta (pendiente).

## Etanol (HS 2207; el biodiesel no se separa a 4 dígitos en HS92)
Paraguay pasó de 0 en 2012 a USD 24 millones en 2014 y USD 195 millones en 2022 (162 en 2024). En 2015 hay 44 productores (CUB, SWZ, PAK, GTM, BOL, JAM, BRA, MUS, SDN, HUN), 15 de ingreso parecido y 15 vecinos; la densidad de Paraguay (0,15) es mayor que la de 94 % de los productos que todavía no tiene.

| Dotación | Paraguay (percentil 2015) → mediana de productores | Brecha 2010: todos / ingreso parecido / vecinos | Brecha 2015: todos / ingreso parecido / vecinos |
|---|---|---|---|
| Capital humano | 41 → 50 | **falta 18** / **falta 14** / **falta 23** | similar / **falta 13** / **falta 18** |
| Capital por trabajador | 43 → 45 | similar / similar / **falta 12** | similar / similar / **falta 15** |
| Logística (LPI) | 48 → 53 | similar / similar / **falta 15** | similar / similar / **falta 15** |
| Electricidad barata | 91 → 44 | sobra 50 / sobra 49 / sobra 45 | sobra 47 / sobra 40 / sobra 45 |
| Mano de obra barata | 63 → 54 | sobra 17 / similar / sobra 22 | similar / similar / sobra 21 |
| Tierra cultivable | 94 → 52 | sobra 39 / sobra 54 / sobra 40 | sobra 41 / sobra 56 / sobra 39 |
| Agua dulce | 83 → 44 | sobra 36 / sobra 25 / sobra 36 | sobra 39 / sobra 30 / sobra 36 |

- **Las brechas son chicas** y **Paraguay tiene excedente de electricidad barata, mano de obra barata, tierra y agua**, consistente con que haya logrado exportar.
- **Cuidado con el excedente de tierra y agua:** los productores de etanol son de todo tipo y la mediana de tierra de sus productores es cercana al percentil 52; la tierra no distingue a quién produce etanol, de modo que ese excedente no es una ventaja demostrada.

## Qué se puede y qué no se puede decir
- Se puede decir: «frente a los países que hoy exportan este producto con ventaja, Paraguay está por debajo en capital humano y capital por trabajador, y por encima en electricidad, tierra y agua».
- **No se puede decir** que cerrar una brecha lleve a producir: el backtest (`docs/resultado_backtest.md`) no encontró que las dotaciones predigan qué producto nuevo aparece. Y arneses lo ilustra: Paraguay entró con brechas.
- **Falta la variable que probablemente decida estos casos:** el régimen fiscal y de inversión (maquila, zonas francas, Ley de Inversiones), en diseño (ver `docs/ESTADO.md`); en etanol, también el costo del insumo agrícola y la política de mezcla.
- Es un solo país y dos productos, a 4 dígitos (los arneses van con otros cables aislados). Las referencias son medianas de pocos productores y mezclan países muy distintos.
- Referencias con pocos productores se marcan con confianza «media» o «baja» (el umbral es de 5 productores por referencia); aquí las tres referencias de los dos productos tienen al menos 15.

## Cómo repetirlo
```bash
uv run python -m src.modelos.ficha_brechas      # tablas
uv run python -m src.figuras.ficha_brechas      # figuras
```
Para otro producto: agregarlo a `PRODUCTOS` (HS4) en `src/modelos/ficha_brechas.py`.
