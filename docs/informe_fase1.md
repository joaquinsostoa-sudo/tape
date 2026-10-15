# Informe de la Fase 1: módulo nacional de TAPE

Fecha: 2026-10-14. **Estado: cierre preliminar** (a confirmar por el equipo; los pendientes de la sección 8 no lo bloquean). Proyecto TAPE (Territorio, Actividades y Potencial Económico), LabDE. Autores del trabajo: Joaquín Sostoa y Everoli (borradores de modelos), con Claude. Todo es **asociación, no causalidad**, con la incertidumbre que se indica en cada resultado. Los documentos de detalle están enlazados en cada sección; las hipótesis y los criterios se declararon en `docs/supuestos.md` antes de correr cada prueba.

## 1. Resumen
**Pregunta de la Fase 1:** ¿qué actividades puede añadir Paraguay a lo que ya exporta, y las capacidades del país (capital humano, energía, capital, logística y otras) mejoran esa predicción?

**Lo que encontramos:**
1. **La cercanía a lo que el país ya sabe hacer predice qué producto entrará después.** La *densidad* de Hidalgo y Hausmann ordena los productos candidatos de cada país entre 3 y 4 veces mejor que el azar (fuera de muestra, 2005-2020, con HS4 y con HS6), y 2 veces mejor en países que el modelo no vio. Es una mejora grande en términos relativos y modesta en absolutos: las entradas son raras (2 a 3 % de los candidatos).
2. **Las capas de capacidades no mejoran esa predicción.** Con cinco formas del modelo (logit con efectos fijos, XGBoost, sin efectos fijos, requisito revelado, nivel sector), cinco definiciones de la entrada, HS4 y HS6, y países excluidos, el modelo con capas no supera a la densidad sola en la lista corta de cada país. La única señal en contra es una diferencia de 0,0006 en AUC-PR con HS6, sin consecuencia práctica, que se registra para replicarla.
3. **Las dotaciones sí explican lo que se produce hoy** en parte: capital humano y capital físico en manufactura, y sobre todo los recursos naturales (tierra cultivable, petróleo, gas, carbón). Pero eso es especialización actual, no entrada futura.
4. **Casos de Paraguay:** el etanol estaba 8.º entre 1.019 candidatos antes de despegar; los arneses (maquila e inversión extranjera) no se anticipaban.
5. **Decisión D16:** las capas pasan a ser **diagnóstico de brechas**, no motor de predicción; la densidad es el motor. La condición de paso del plan (capas mejoran a la densidad) **no se cumple**, y el equipo decidió entrar a la Fase 2 con esa lectura, reabriendo la pregunta con datos de ciudad.

**Entregables:** datos reproducibles desde el archivo original de CEPII; depuración del comercio; dotaciones y requisitos; modelo y pruebas; lista de sectores candidatos; herramienta de diagnóstico de brechas para Paraguay (mapa de productos, lista y ficha).

## 2. La densidad, en palabras simples
Un país no produce cualquier cosa: produce lo que sus capacidades permiten, y los productos que usan capacidades parecidas tienden a exportarse juntos. Hidalgo, Klinger, Barabási y Hausmann (2007) midieron esa cercanía: dos productos están **próximos** si los países que exportan uno suelen exportar el otro. La **densidad** de un producto para un país es el promedio de la proximidad entre ese producto y todo lo que el país ya exporta con ventaja. Si Paraguay exporta carne, soja y aceites, un producto cercano a esos tendrá densidad alta.

La teoría dice que las capacidades no se observan una por una, y que la proximidad ya las resume. Eso es coherente con lo que encontramos: medidas directas de capacidades (educación, electricidad, logística) no agregan nada a lo que la proximidad ya contiene. Puede ser también que las medimos mal, y no lo descartamos.

**Qué mide el resultado.** Si para un país tomamos sus 20 productos con mayor densidad entre unos 1.000 candidatos, alrededor del 9-10 % entra efectivamente en los siguientes 5 años; el azar acertaría el 2,5 %. Es un ordenamiento útil, no una probabilidad calibrada.

*Referencias (citadas de memoria: verificarlas antes de publicar):* Hidalgo, Klinger, Barabási y Hausmann (2007), «The Product Space Conditions the Development of Nations», *Science*; Hidalgo y Hausmann (2009), PNAS; para regiones dentro de un país, Neffke, Henning y Boschma (2011) para Suecia y trabajos posteriores para España.

## 3. Datos y construcción
| Pieza | Qué es | Dónde |
|---|---|---|
| Comercio | BACI HS92 (CEPII), 1995-2024, exportaciones e importaciones por país y producto HS6, procesado desde el zip; la tabla HS4 coincide con el panel anterior (4.976.887 filas, diferencia relativa máxima 1,5 × 10⁻¹⁵) | `docs/baci_limpieza.md` |
| Depuración (D6) | Marca de reexportaciones (importaciones ≥ 0,5 × exportaciones del mismo producto, año y país) aplicada solo a Paraguay y a Hong Kong, Singapur, Países Bajos y Bélgica; energía HS 2716 excluida | `docs/depuracion_d6.md` |
| Muestra (D8) | Población ≥ 1 millón y exportaciones ≥ USD 1.000 millones en el año inicial (112 a 144 países, 97 % del comercio) | `docs/supuestos.md` |
| Presencia y entrada | RCA ≥ 1 en 2 de los 3 años que terminan en t (D13); entrada = RCA_t < 0,5 y RCA_t+5 ≥ 1 (D7); φ y densidad con datos de los 5 años que terminan en t (D3), sin ver el futuro | `docs/supuestos.md` |
| Dotaciones por país | Capital humano, capital por trabajador (PWT 11.0), logística (LPI, con la primera edición arrastrada hacia atrás, D14), precio de la electricidad, salario, impuesto a las utilidades, tierra cultivable, agua, reservas de petróleo, gas, carbón y minerales | `docs/dotaciones.md` |
| Requisitos por producto | Intensidad de energía, capital y habilidades de NBER-CES vía el puente NAICS → HS (D4); 1.095 productos HS4 con requisito completo | `docs/puente_requisitos.md` |
| Taxonomía | 67 sectores TAPE sobre CIIU Rev.4 y puente HS → sector con confianza por fila | `docs/taxonomia.md`, `docs/puente_hs_sector.md` |

## 4. Resultados

### 4.1 La densidad predice (backtest nacional)
Esquema de la decisión D2 (a): para cada ventana de prueba se entrena solo con ventanas cuyo resultado ya se conocía y se predice la siguiente. Pruebas 2005→2010, 2010→2015 y 2015→2020 con 112, 124 y 125 países y 2.581, 2.374 y 2.116 entradas. Métrica principal: precision@20 por país (la lista corta de cada uno). `docs/resultado_backtest.md`.

| Prueba | Tasa base | Azar | Densidad cruda | Prior de producto | **Densidad sola** (efectos de país y producto) | Con capas |
|---|---|---|---|---|---|---|
| 2005→2010 | 2,8 % | 0,028 | 0,057 | 0,080 | **0,088** | 0,091 |
| 2010→2015 | 2,3 % | 0,023 | 0,051 | 0,071 | **0,085** | 0,082 |
| 2015→2020 | 2,0 % | 0,020 | 0,052 | 0,061 | **0,075** | 0,074 |

La densidad con efectos de país y producto ordena 3 a 4 veces mejor que el azar. Con HS6 (4.000 productos): 3,5 a 4,1 veces; en países retenidos del entrenamiento, 2,1 veces. **Calibración deficiente en los extremos:** en el decil superior el modelo predice 0,11 a 0,14 y la frecuencia real es 0,06 a 0,08; las puntuaciones sirven para ordenar, no para leerlas como probabilidades.

### 4.2 Las capas no mejoran la lista corta
Diferencia de precision@20 por país entre el modelo con capas y la densidad sola, con intervalo del 95 % por remuestreo de países (siempre incluye el cero salvo donde se indica):

| Prueba de robustez | Resultado |
|---|---|
| Logit con interacciones requisito × dotación (D2) | +0,003 / −0,003 / −0,001 |
| XGBoost con SHAP (no linealidades) | +0,005 / −0,010 (−0,020; −0,003) / +0,006: una ventana a favor, una en contra |
| Sin efectos fijos (tipo Mundlak) | las interacciones no aportan; el modelo es 0,022 a 0,033 peor que el que usa efectos fijos |
| Cinco definiciones alternativas de la entrada (h = 10, 2 de 3 años, RCA < 0,25, < 1, ≥ 1,5) | las capas no superan a la densidad en las 16 combinaciones; en una empeoran (−0,010) |
| Requisito revelado por los países productores (en lugar de NBER-CES) | −0,003 / −0,003 / −0,006; criterio declarado no cumplido en las 6 combinaciones |
| Nivel sector TAPE (50 sectores, 67 a 96 entradas por ventana) | 0,000 / +0,011 (0,000; +0,028) / +0,009 (0,000; +0,021) en precision@5: indicio débil en la dirección esperada, con intervalos en el borde del cero y muy pocas entradas |
| HS6 en lugar de HS4 | p@20 −0,000 / −0,005 / −0,005; AUC-PR **+0,0006** en 2005 y 2010 con intervalo sin el cero (0,8 % relativo): criterio declarado A1 incumplido, registrado como hallazgo a replicar |
| Países excluidos comparables a Paraguay (10 por ventana, 29 países-ventana) | +0,0017 (−0,012; +0,016): no se detecta mejora, con poca potencia |
| Depuración D6 (alcance a) | densidad sola cambia menos de 0,01; capas sin mejora en las tres ventanas |

Detalles: `docs/resultado_backtest.md`, `docs/resultado_punto3.md`, `docs/depuracion_d6.md`.

### 4.3 Qué explican las dotaciones: la especialización actual
Prueba de corte transversal (¿las dotaciones explican lo que el país produce hoy?), declarada antes de correrla. `docs/resultado_presente.md`, `docs/resultado_bloques.md`.

| Término | Coeficiente | p |
|---|---|---|
| Capital humano × intensidad de habilidades | 0,193 | < 0,001 |
| Capital físico × intensidad de capital | 0,072 | 0,021 |
| Logística × valor/peso | −0,093 (signo contrario al esperado) | 0,016 |
| Energía × intensidad energética | 0,041 | 0,48 |
| Tierra cultivable × productos de tierra | 0,218 | 0,0015 |
| Petróleo, gas y carbón (reservas por persona) × sus productos | +1,95 / +5,01 / +1,39 | < 0,001 |
| Agua dulce, hidroelectricidad, minerales (USGS) | no significativos | 0,25 a 0,70 |

Las dotaciones **sí** se asocian con la especialización: capital humano y capital físico en manufactura y, sobre todo, los recursos naturales con sus bloques de productos. Pero el capital humano pierde fuerza al controlar por el PIB per cápita (se confunde con el desarrollo general) y la logística sale con el signo contrario en todas las versiones. El cuadro de bloques de Lall × terciles de dotación, con la ficha de Paraguay (ventaja grande en primarios agropecuarios, tercil alto en tierra, agua y electricidad barata), está en `docs/resultado_bloques.md` y `docs/figuras/bloques_dotaciones_2015.png`.

### 4.4 Casos de Paraguay (4 eventos, descriptivo)
| Caso | Producto | Ventana | Puesto con densidad (de ~1.020 candidatos) |
|---|---|---|---|
| Biocombustibles | 2207 etanol | 2010→2015 | **8** |
| Frigoríficos | 0210 carne salada o seca | 2005→2010 | 331 |
| Arneses | 8544 | 2010→2015 | 465 |
| Frigoríficos | 0209 grasa de cerdo y aves | 2010→2015 | 683 |

Criterio declarado (la mitad o más de los eventos entre el 10 % superior): no cumplido (1 de 4). El etanol sí se anticipaba; los arneses, no (entraron por maquila e inversión extranjera); la carne bovina ya tenía ventaja antes de 2000 y no es una entrada medible con estas ventanas.

### 4.5 Sectores candidatos de Paraguay (D1 a, corte 2024)
Puntuación por producto agregada a sector por la media ponderada por comercio mundial, con máximo y conteo entre los 100 mejores candidatos. Los más robustos (media alta y varios productos en el top): ganadería, molinería, textiles y cultivos anuales; los que encabezan la media (cemento, tabaco, petróleo refinado) dependen de pocos productos. Las puntuaciones ordenan, no son probabilidades. `docs/candidatos_sector.md`.

### 4.6 Diagnóstico de brechas (herramienta de apoyo, no predictiva)
Compara a Paraguay con los países que ya producen cada bien, dotación por dotación, y marca límites duros (el recurso principal que falta) y productos «sin dato confiable de reservas». Entre los 277 productos cercanos que Paraguay no exporta: 9 con límite duro (carbón, petróleo, gas, fosfatos y tres por capital humano o capital por trabajador), 240 compatibles. El índice **no mejora la predicción de la densidad** (AUC 0,888 contra 0,891) y la hipótesis del exceso como costo de oportunidad dio signo contrario (+0,27): se usa para describir brechas, no para elegir candidatos. `docs/mapa_brechas.md`, `docs/figuras/mapa_limites_PRY_2019.png`; prototipo de herramienta (mapa de 1.239 productos, lista y ficha) publicado como artefacto privado.

## 5. Qué significa para el proyecto
| Pregunta del documento técnico | Con lo que encontramos |
|---|---|
| 1. Factibilidad | **Densidad** (y su ordenamiento de candidatos); las capas no la ajustan |
| 2. Valor | Sin cambio (PCI, salario, encadenamientos; Fase 3) |
| 3. Dónde | Densidad territorial (Fase 2); las capas se retoman con datos de ciudad |
| 4. Qué brechas | Brechas en percentiles frente a los productores y límites duros, **no** el contrafactual ΔP (no hay coeficientes confiables) |
| 5. Quién actúa | Por tipo de brecha; ε pasa a ser tolerancia de brecha (D10) |
| 6. Validación | Siempre contra la densidad sola; las capas no la mejoran |

**Condición de paso a la Fase 2 (el modelo con capas supera a la densidad sola): no se cumple.** La decisión D16 (2026-10-14) fija que las capas son diagnóstico y reabre la pregunta en la Fase 2: se repite el test de capas con datos de ciudad (dotaciones con variación dentro del país) con criterio declarado antes de correrlo; si superan a la densidad territorial en precision@k, se promueven a motor de predicción.

## 6. Limitaciones: lo que estos resultados NO prueban
- **No prueban que las capacidades no importen.** Pueden estar mal medidas: el precio de la electricidad solo existe para 2014-2019; los requisitos vienen de la tecnología de EE. UU.; el LPI es una percepción y su primera edición se arrastra hacia atrás; las capas están muy correlacionadas con el desarrollo general (correlación 0,94 del capital físico, 0,81 del capital humano y 0,75 de la logística con el log del PIB per cápita).
- **Anacronismos aceptados que favorecían a las capas en 2005 y 2010** (usan datos posteriores); aun así no ganan.
- **Entradas raras y un solo año:** la definición de la entrada con un solo año de RCA (D7) hace ruidosos los eventos; en la ventana 2005 se entrena con una sola ventana.
- **Los casos de Paraguay son 4 eventos:** descriptivos, sin inferencia.
- **Calibración:** las puntuaciones ordenan; no se pueden leer como probabilidades.
- **La depuración marca reexportaciones por la razón de importación/exportación**, que no captura la maquila (los arneses no se marcan) y marca comercio intraindustrial genuino si se aplica a todos los países (por eso solo a Paraguay y a cuatro centros de reexportación).
- **Fuentes provisorias:** las reservas minerales (USGS) solo listan grandes poseedores; el mapa del MIC viene del visor web sin licencia declarada.

## 7. Decisiones tomadas
| # | Decisión | Fecha | Detalle |
|---|---|---|---|
| D1 | Producto → sector: media ponderada por comercio mundial, con máximo y conteo | 2026-10-14 | `docs/candidatos_sector.md` |
| D2 | Efectos fijos y fuera de muestra, por propósito (coeficientes dentro de muestra; backtest con efectos constantes; Mundlak para países excluidos) | 2026-10-13 | `docs/supuestos.md` |
| D3 | φ con ventana de 5 años que termina en t, solo datos ≤ t | 2026-10-12 | |
| D4 | Requisitos con NBER-CES y puente NAICS → HS; energía = precio de la electricidad | 2026-10-12 | `docs/puente_requisitos.md` |
| D5 | HS92 a 4 dígitos para estimar; HS6 para el puente y la robustez | 2026-10-08 | `docs/resultado_punto3.md` |
| D6 | Reexportaciones marcadas; alcance: Paraguay y centros de reexportación | 2026-10-12 / 2026-10-14 | `docs/depuracion_d6.md` |
| D7 | Entrada con un solo año; robustez con 2 de 3 años | 2026-10-12 | |
| D8 | Muestra: población ≥ 1 millón y exportaciones ≥ USD 1.000 millones | 2026-10-12 | |
| D13 | Presencia = RCA ≥ 1 en 2 de 3 años | 2026-10-13 | |
| D14 | LPI arrastrado hacia atrás, con robustez | 2026-10-13 | |
| D15 | Capital físico (PWT) en lugar de crédito | 2026-10-13 | |
| D16 | Las capas son diagnóstico, no motor de predicción; reapertura con datos de ciudad | 2026-10-14 | `CLAUDE.md` |
| D10 | Umbral ε de las reglas de política | abierta (Fase 3) | |

## 8. Estado de las tareas y pendientes
| Tarea | Estado |
|---|---|
| 1.1 Limpieza de BACI | Hecha (`docs/baci_limpieza.md`) |
| 1.2 Depuración D6 | Hecha, con la marca aplicada a Paraguay y centros de reexportación |
| 1.3 a 1.4 RCA, proximidad y densidad | Hechas en `logit_nacional.py` y `densidad_np.py` (versiones livianas) |
| 1.5, 1.6 Dotaciones y requisitos | Hechas |
| 1.7 a 1.8 Panel y modelo de referencia | Hechas |
| 1.9 a 1.11 Logit, XGBoost y backtest | Hechas, con todas las pruebas declaradas |

**Pendientes que no impiden cerrar la fase, pero hay que resolver:**
1. **Revisión con la aduana de la lista de productos reexportados de Paraguay** (cigarrillos, alimento para mascotas, vidrio, PET y panificados pueden ser falsos positivos; medicamentos y agroquímicos son probables reexportaciones).
2. **Referencia oficial de exportaciones de Paraguay por año (BCP o DNA)** para completar la verificación de BACI.
3. **Consolidar los borradores de Ever** (`depurar.py`, `importaciones.py`, `presencia.py`, `densidad.py`, `panel.py`, `evaluacion.py`, `logit_densidad.py`, `backtest.py`, `test_capas.py`) con las versiones actuales para no tener dos cálculos distintos del mismo resultado.
4. **Replicar la diferencia de AUC-PR de +0,0006 a HS6** (por ejemplo, con otras definiciones de la entrada).
5. **Sensibilidad de la lista de sectores candidatos** (otros años de corte, HS6, tabla bruta) y revisión de las asignaciones del puente HS que se vieron poco intuitivas (3101, 7116).
6. **Mejorar la medición de las capas** (más años de energía, requisitos propios para agro y servicios) antes de reabrir su papel como motor.

**Inconsistencias señaladas y no corregidas en silencio:** (i) la condición de paso a la Fase 2 del plan no se cumple y se resuelve por la decisión D16, no por el resultado; (ii) los códigos del Censo Económico 2011 de alimentos, bebidas y químicos (107, 109, 111, 112, 202, 209) no son la CIIU Rev.4 internacional (`docs/censo_sector.md`, relevante para la Fase 2); (iii) el borrador de Ever evalúa dentro de la muestra y con crédito en lugar de capital físico (`docs/NOTA_revision_modelos_Ever.md`).

## 9. Cómo reproducir
`uv run python -m src.descargas.todas` (fuentes automáticas), `uv run python -m src.reconstruir_todo` (tablas de `data/clean`; incluye BACI, unos 5 minutos), luego `uv run python -m src.limpieza.depuracion`, `src.modelos.backtest_nacional` (con `--expo data/model/exportaciones_hs4_depurado.parquet` para el RCA depurado), `src.modelos.robustez_hs6`, `paises_excluidos`, `casos_paraguay` y `candidatos_sector`. 252 pruebas automáticas (`uv run pytest`) y `ruff` limpio en el código nuevo. Los archivos de `data/raw` no se modifican; cada fuente está registrada en `data/fuentes.csv`.

## 10. Siguiente paso: Fase 2
Lo que ya hay para empezar: 17.080 industrias del mapa MIC 2026 asignadas a distrito y a sector (con la tabla de actividades específicas), 238 distritos del Censo Económico 2011 con 224.242 unidades, equivalencia de distritos con padres confirmados por ley en 20 de los 24 casos nuevos, y la tabla Censo 2011 → sector TAPE. Lo primero: las matrices de presencia 2010 y 2026 por distrito (a nivel de grupo de sectores como resultado principal y sector con reparto neutro como detalle, decisión del equipo), y declarar las hipótesis del backtest territorial hacia atrás antes de correrlo.
