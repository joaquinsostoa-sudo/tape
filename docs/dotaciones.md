# Dotaciones por país, a_ckt (tarea 1.5)

Fecha: 2026-10-12. Código: `src/limpieza/dotaciones.py`. Salidas: `data/clean/dotaciones.parquet` (235 países × 1990-2024) y `data/clean/dotaciones_cortes.csv` (los años de corte 2000, 2005, 2010, 2015, 2019 y 2024, versionado). Figura: `docs/figuras/dotaciones_paraguay.png` (`src/figuras/dotaciones_paraguay.py`). Pruebas: `tests/test_dotaciones.py`.

Son la contraparte de los requisitos por producto (`docs/puente_requisitos.md`): el modelo M1 multiplica lo que **exige un producto** por lo que **tiene un país**.

## Las cuatro capas
Todas se leen igual: **más es mejor**.

| Capa | Medida | Transformación | Fuente | Cobertura |
|---|---|---|---|---|
| Capital humano | índice `hc` (años de escolaridad y retornos) | ninguna | Penn World Table 10.01 | 144 países, 1990-2019 |
| Crédito | crédito interno al sector privado, % del PIB | logaritmo | WDI | 120 a 174 países según el año |
| **Energía** | **precio de la electricidad** (centavos de USD por kWh), promedio 2014-2019 | **menos el logaritmo** (barato = mejor) | Doing Business, Banco Mundial | 186 países; el mismo valor en todos los años |
| Logística | índice de desempeño logístico (LPI, 1 a 5) | ninguna | WDI | 163 a 169 países, desde 2007 |

Cada capa se guarda en bruto, estandarizada por año (`z_`, media 0 y desvío 1 entre los países con dato) y como percentil (`pct_`). La tabla trae además alternativas de energía (`z_consumo_electrico`, `z_hidro`), matrícula terciaria y secundaria, población y PIB per cápita. La muestra son los 235 países del catálogo de BACI; los agregados regionales de WDI se descartan.

## Por qué la energía es el precio y no el consumo
La primera versión usaba el consumo eléctrico per cápita, y estaba mal planteada: mide cuánta electricidad se **usa**, no cuánto **cuesta**, y Paraguay, con electricidad hidroeléctrica abundante y barata, salía como un país "pobre en energía". El indicador de **precio** (Doing Business 2016-2020, `IC.ELC.PRI.KH.DB1619`, 186 países) corrige eso: Paraguay paga 6,6 centavos por kWh, entre los más baratos del mundo. Es la mejora de D4 que se había dejado abierta (adoptada el 2026-10-12).

La fuente trae una fila por ciudad (Delhi, Mumbai, Nueva York, etc.) además de la del país con el promedio ponderado; el lector se queda con la del país.

## Decisiones de construcción (por revisar)
- **Precio promedio 2014-2019** como característica estable del país, aplicado a todos los años. Es anacrónico para las ventanas anteriores a 2014 (usa precios futuros), pero las tarifas cambian lentamente. En la robustez (tarea 1.11) conviene repetir el modelo solo con las ventanas de 2015 en adelante.
- **Logaritmo** en crédito y precio por la asimetría de las distribuciones. Lo que no es positivo queda vacío.
- **LPI:** hay ediciones solo en 2007, 2010, 2012, 2014, 2016, 2018 y 2022. Cada edición se arrastra **hacia adelante** hasta la siguiente y nunca hacia atrás, para no usar información futura. Antes de 2007 queda vacío, así que los cortes de 2000 y 2005 no tienen logística. `lpi_edicion_anio` dice de qué edición viene cada valor.
- **No se imputa nada.** La muestra definitiva de países (D8, pendiente) y el tratamiento de los vacíos se fijan al armar el panel (tarea 1.7).

## Control: cobertura (países con dato por capa)
| Corte | Capital humano | Crédito | Energía | Logística |
|---|---|---|---|---|
| 2000 | 144 | 120 | 186 | 0 |
| 2005 | 144 | 152 | 186 | 0 |
| 2010 | 144 | 169 | 186 | 163 |
| 2015 | 144 | 174 | 186 | 165 |
| 2019 | 144 | 172 | 186 | 167 |
| 2024 | 0 | 147 | 186 | 169 |

En 2015, 124 de los 158 países con más de 1 millón de habitantes tienen las cuatro capas (78 %). Otros 27 países no tienen población en WDI ese año.

## Control: posición de Paraguay
Ver `docs/figuras/dotaciones_paraguay.png`. **Paraguay es fuerte en energía (percentil 92)** y está cerca de la mitad en las otras tres capas.

| Capa | Percentil 2015 | Último dato |
|---|---|---|
| Capital humano | 41 | 41 (2019) |
| Crédito | 48 | 60 (2022) |
| **Energía** | **92** | 92 (valor estable) |
| Logística | 53 | 49 (2022) |

El crédito cayó al percentil 23 hacia 2007; desde 2015 está entre el 39 y el 60 (capital humano, crédito y logística).

## Colinealidad entre capas
Correlación entre las capas estandarizadas en 2015:

| | Capital humano | Crédito | Energía | Logística |
|---|---|---|---|---|
| Capital humano | 1,00 | 0,65 | 0,02 | 0,72 |
| Crédito | 0,65 | 1,00 | 0,06 | 0,76 |
| Energía | 0,02 | 0,06 | 1,00 | 0,00 |
| Logística | 0,72 | 0,76 | 0,00 | 1,00 |

- **El precio de la electricidad es independiente de las otras capas.** Con el consumo per cápita la correlación con el capital humano era 0,83, porque el consumo mide desarrollo. Con la proporción hidroeléctrica (`z_hidro`) es de -0,23.
- **Capital humano, crédito y logística sí están muy correlacionados entre sí** (0,65 a 0,76): miden en buena medida el desarrollo general. Para el logit de M1 hay opciones por decidir en la tarea 1.9: estimar capa por capa, incluir el PIB per cápita como control o transformar las capas en componentes.

## Límites
1. **El precio no es el industrial promedio**: es el costo de un almacén comercial estándar (140.000 kWh por mes) en la ciudad de negocios principal. Es la mejor medida comparable gratuita; las alternativas (Global Petrol Prices) son de pago.
2. **El indicador está discontinuado** (Doing Business, 2021) y solo cubre 2014-2019.
3. **Un precio bajo no siempre es abundancia**: entre los más baratos hay países con tarifas subsidiadas (Kuwait, Argelia, Catar, Kirguistán, Etiopía). Mide el costo para las empresas, no su causa.
4. Faltan 49 países sin precio (sobre todo economías chicas).
5. Capital humano llega a 2019 (PWT 10.01): para 2020-2024 queda vacío y hay que decidir qué usar en las predicciones actuales (por ejemplo, la matrícula de WDI).
6. Los z-scores se calculan con todos los países con dato; al fijar la muestra (D8) habrá que recalcularlos.
7. Resultados como asociación, no como causalidad.
