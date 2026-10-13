# Dotaciones por país, a_ckt (tarea 1.5)

Fecha: 2026-10-12. Código: `src/limpieza/dotaciones.py`. Salidas: `data/clean/dotaciones.parquet` (235 países × 1990-2024) y `data/clean/dotaciones_cortes.csv` (los años de corte 2000, 2005, 2010, 2015, 2019 y 2024, versionado). Figura: `docs/figuras/dotaciones_paraguay.png` (`src/figuras/dotaciones_paraguay.py`). Pruebas: `tests/test_dotaciones.py`.

Son la contraparte de los requisitos por producto (`docs/puente_requisitos.md`): el modelo M1 multiplica lo que **exige un producto** por lo que **tiene un país**.

## Las cuatro capas
| Capa | Medida | Transformación | Fuente | Cobertura |
|---|---|---|---|---|
| Capital humano | índice `hc` (años de escolaridad y retornos) | ninguna | Penn World Table 10.01 | 144 países, 1990-2019 |
| Crédito | crédito interno al sector privado, % del PIB | logaritmo | WDI | 120 a 174 países según el año |
| Energía | consumo eléctrico per cápita (kWh) | logaritmo | WDI | 147 a 149 países |
| Logística | índice de desempeño logístico (LPI, 1 a 5) | ninguna | WDI | 163 a 169 países, desde 2007 |

Cada capa se guarda en bruto, estandarizada por año (`z_`, media 0 y desvío 1 entre los países con dato) y como percentil (`pct_`). La tabla trae además alternativas (matrícula terciaria y secundaria, acceso a electricidad), población y PIB per cápita. La muestra son los 235 países del catálogo de BACI; los agregados regionales de WDI se descartan.

## Decisiones de construcción (por revisar)
- **Energía** es un sustituto: el consumo eléctrico per cápita mide cuánta energía usa un país, no cuánto le cuesta. Es lo acordado en D4 (el precio real de la IEA es de pago). Un detalle importante para Paraguay: su consumo per cápita es bajo porque exporta la mayor parte de la energía de Itaipú y Yacyretá.
- **Logaritmo** en crédito y electricidad por la asimetría de las distribuciones. Lo que no es positivo queda vacío.
- **LPI:** hay ediciones solo en 2007, 2010, 2012, 2014, 2016, 2018 y 2022. Cada edición se arrastra **hacia adelante** hasta la siguiente y nunca hacia atrás, para no usar información futura. Antes de 2007 queda vacío, así que los cortes de 2000 y 2005 no tienen logística. La columna `lpi_edicion_anio` dice de qué edición viene cada valor.
- **No se imputa nada.** La muestra definitiva de países (D8, pendiente) y el tratamiento de los vacíos se fijan al armar el panel (tarea 1.7).

## Control: cobertura (países con dato por capa)
| Corte | Capital humano | Crédito | Energía | Logística |
|---|---|---|---|---|
| 2000 | 144 | 120 | 147 | 0 |
| 2005 | 144 | 152 | 148 | 0 |
| 2010 | 144 | 169 | 148 | 163 |
| 2015 | 144 | 174 | 149 | 165 |
| 2019 | 144 | 172 | 149 | 167 |
| 2024 | 0 | 147 | 149 | 169 |

En 2015, 116 de los 158 países con más de 1 millón de habitantes tienen las cuatro capas (73 %). Otros 27 países no tienen población en WDI ese año.

## Control: posición de Paraguay
Ver `docs/figuras/dotaciones_paraguay.png`. Desde 2015 Paraguay está entre el percentil 39 y el 60 en las cuatro capas: es decir, cerca de la mitad de la tabla. Antes la posición variaba más (por ejemplo, el crédito cayó al percentil 23 hacia 2007).

| Capa | Percentil 2015 | Último dato |
|---|---|---|
| Capital humano | 41 | 41 (2019) |
| Crédito | 48 | 60 (2022) |
| Energía | 43 | 46 (2022) |
| Logística | 53 | 49 (2022) |

## Hallazgo importante para el modelo: las capas están muy correlacionadas
Correlación entre las capas estandarizadas en 2015:

| | Capital humano | Crédito | Energía | Logística |
|---|---|---|---|---|
| Capital humano | 1,00 | 0,65 | 0,83 | 0,72 |
| Crédito | 0,65 | 1,00 | 0,73 | 0,76 |
| Energía | 0,83 | 0,73 | 1,00 | 0,70 |
| Logística | 0,72 | 0,76 | 0,70 | 1,00 |

Las cuatro miden, en buena medida, el desarrollo general de un país. En el logit de M1, las interacciones de cada capa con su requisito del producto van a competir entre sí, y separar sus efectos será difícil. Opciones para la tarea 1.9, por decidir: estimar capa por capa; incluir el PIB per cápita como control; o transformar las capas en componentes. No se resuelve acá.

## Límites
1. Capital humano llega a 2019 (PWT 10.01); para 2020-2024 queda vacío y hay que decidir qué usar en las predicciones actuales (por ejemplo, la matrícula de WDI).
2. Los z-scores se calculan con todos los países con dato; al fijar la muestra (D8) habrá que recalcularlos.
3. El crédito mide profundidad financiera, no acceso por sector.
4. Resultados como asociación, no como causalidad.
