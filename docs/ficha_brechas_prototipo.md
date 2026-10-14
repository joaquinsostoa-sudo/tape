# Ficha de brechas de Paraguay: prototipo con arneses y etanol (2026-10-13)

**Prototipo descriptivo.** Código: `src/modelos/ficha_brechas.py` (cálculo) y `src/figuras/ficha_brechas.py` (figura); figuras: `docs/figuras/ficha_brechas_8544.png` (arneses) y `ficha_brechas_2207.png` (etanol);
tablas: `data/model/ficha_brechas_8544.csv` y `ficha_brechas_2207.csv` (2010 y 2015). Pedido de Joaquín: mostrar qué le falta a Paraguay, dotación por dotación, para producir un producto.

## Qué calcula
Para un producto HS4 y un año, el percentil de Paraguay en cada dotación entre los países D8 (0 = el menos dotado, 100 = el más dotado) frente al percentil mediano de:
1. **todos los productores** (presencia D13: RCA ≥ 1 sostenido), sin Paraguay;
2. **productores de ingreso parecido** al de Paraguay (el mismo tercio de PIB per cápita), para separar la dotación del desarrollo general;
3. **productos vecinos** en el espacio producto: los 15 de mayor proximidad φ (D3), cada uno con la mediana de sus productores, ponderados por φ (estabiliza productos con pocos productores).

La **brecha** es la referencia menos la posición de Paraguay, en puntos de percentil: positiva («falta») si Paraguay está por debajo, negativa («sobra») si está por encima. Solo se informa de «falta» o «sobra» con una diferencia de al menos 10 puntos.

## Arneses y cables aislados (HS 8544; los arneses, HS 854430, son parte)
Paraguay pasó de exportaciones casi nulas (USD 0,05 millones en 2000) a USD 350 millones en 2024, con ventaja (RCA ≥ 1) desde 2014. En 2015 hay 41 productores (NIC, TUN, MDA, MAR, HND, ROU, MKD, EGY, SRB, PHL entre los que más destacan), 16 de ingreso parecido y 15 vecinos; la densidad de Paraguay (0,12) es mayor que la de 81 % de los productos que todavía no tiene.

| Dotación (percentil de Paraguay → mediana de productores) | Brecha 2010 (todos / ingreso parecido / vecinos) | Brecha 2015 |
|---|---|---|
| Capital humano (38 → 65; 2015: 40 → 64) | **+27** / +17 / +23 | **+24** / +15 / +25 |
| Capital por trabajador (36 → 59; 2015: 35 → 59) | **+23** / +12 / +22 | **+24** / +18 / +29 |
| Logística, LPI (49 → 63; 2015: 48 → 64) | +14 / −2 / +12 | +16 / +3 / +20 |
| Electricidad barata (91 → 52) | sobra 38 | sobra 39 |
| Tierra cultivable (95 → 58) | sobra 37 | sobra 34 |
| Agua dulce (83 → 47) | sobra 36 | sobra 33 |

- **La brecha ya existía antes de la entrada (2010) y era parecida a la de 2015**: Paraguay entró en arneses con menos capital humano y menos capital por trabajador que los productores típicos. La brecha de logística desaparece al compararse con productores de ingreso parecido.
- **Lo que explica la entrada no está en las dotaciones**: el ensamblaje de arneses es intensivo en mano de obra y entró con el régimen de maquila; los salarios y el régimen no figuran en las capas. Es el tipo de «salto largo» (IED, maquila) que el proyecto trata como categoría aparte de política.

## Etanol (HS 2207; el biodiesel no se separa a 4 dígitos en HS92)
Paraguay pasó de 0 en 2012 a USD 24 millones en 2014 y USD 195 millones en 2022 (162 en 2024). En 2015 hay 44 productores (CUB, SWZ, PAK, GTM, BOL, JAM, BRA, MUS, SDN, HUN), 15 de ingreso parecido y 15 vecinos; la densidad de Paraguay (0,15) es mayor que la de 94 % de los productos que todavía no tiene.

| Dotación | Brecha 2010 (todos / ingreso parecido / vecinos) | Brecha 2015 |
|---|---|---|
| Capital humano (38 → 55) | +18 / +14 / +23 | +13 / +14 / +19 |
| Capital por trabajador (36 → 51) | +15 / +16 / +23 | +7 / +14 / +23 |
| Logística, LPI | 0 / +3 / +15 | +5 / −4 / +15 |
| Electricidad barata | sobra 50 | sobra 47 |
| Tierra cultivable | sobra 39 | sobra 41 |
| Agua dulce | sobra 36 | sobra 39 |

- **Las brechas son chicas** (capital humano de unos 13 a 18 puntos; capital por trabajador y logística, similares a los productores) y **Paraguay tiene excedente de electricidad barata, tierra y agua**, consistente con que haya logrado exportar.
- **Cuidado con el excedente de tierra y agua:** los productores de etanol son de todo tipo y su mediana de tierra es solo el percentil 52; la tierra no distingue a quién produce etanol, de modo que ese excedente no es una ventaja demostrada.

## Qué se puede y qué no se puede decir
- Se puede decir: «frente a los países que hoy exportan este producto con ventaja, Paraguay está por debajo en capital humano y capital por trabajador, y por encima en electricidad, tierra y agua».
- **No se puede decir** que cerrar una brecha lleve a producir: el backtest (`docs/resultado_backtest.md`) no encontró que las dotaciones predigan qué producto nuevo aparece. Y arneses lo ilustra: Paraguay entró con brechas.
- **Faltan variables que probablemente decidan estos casos:** salarios y régimen de maquila (arneses), costo del insumo agrícola y política de mezcla (etanol). Son candidatos para la siguiente versión.
- Es un solo país y dos productos, a 4 dígitos (los arneses van con otros cables aislados). Las referencias son medianas de pocos productores y mezclan países muy distintos.
- Referencias con pocos productores se marcan con confianza «media» o «baja» (el umbral es de 5 productores por referencia); aquí las tres referencias de los dos productos tienen al menos 15.

## Cómo repetirlo
```bash
uv run python -m src.modelos.ficha_brechas      # tablas
uv run python -m src.figuras.ficha_brechas      # figuras
```
Para otro producto: agregarlo a `PRODUCTOS` (HS4) en `src/modelos/ficha_brechas.py`.
