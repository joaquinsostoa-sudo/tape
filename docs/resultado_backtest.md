# Backtest fuera de muestra del modelo nacional (primera versión, 2026-10-13)

**Provisorio.** Primera corrida de la tarea 1.11 (`src/modelos/backtest_nacional.py`) con la base de Ever en lectura (HS4, sin marca de reexportaciones, ver `docs/resultado_logit_provisorio.md`). Resultados como asociación, no causalidad.

## Cómo se hizo
- **Esquema (D2 a):** para cada ventana de prueba t0 se entrena solo con las ventanas cuyo resultado ya se conocía en t0 (v + 5 ≤ t0) y se predice la entrada de t0 a t0 + 5. Pruebas: 2005 (entrena con 2000), 2010 (con 2000 y 2005) y 2015 (con 2000, 2005 y 2010).
- **Modelo:** logit con efectos fijos de país y producto constantes entre ventanas, más un indicador de ventana, penalización suave (C = 10). La densidad se estandariza con la media y el desvío del entrenamiento.
- **Muestra común:** los países con todas las capas vigentes (D15), para que todos los modelos se evalúen sobre las mismas filas (112, 124 y 125 países; 2.581, 2.374 y 2.116 entradas).
- **Modelos:** `azar` (tasa base); `densidad_cruda` (ordenar por densidad); `prior_producto` (tasa histórica de entrada del producto); `densidad_sola` (logit con densidad y efectos fijos, la comparación que exige el proyecto); `capas` (el mismo logit con las interacciones r·a).
- **Métricas:** precision@10 y @20 **por país** (la lista corta de cada país, promedio entre países con al menos una entrada), precision@100 y @500 agrupadas, AUC-PR y Brier. Intervalos del 95 % por remuestreo de países (300 repeticiones; 200 para el AUC-PR).

## Resultados
| Prueba | Modelo | p@20 por país | p@100 agrupada | AUC-PR | Brier |
|---|---|---|---|---|---|
| **2005→2010** (tasa base 2,8 %) | azar | 0,028 | 0,028 | 0,028 | |
| | densidad cruda | 0,057 | 0,110 | 0,043 | |
| | prior de producto | 0,080 | 0,120 | 0,045 | 0,027 |
| | **densidad sola** | **0,088** | 0,110 | 0,063 | 0,028 |
| | **capas** | **0,091** | 0,110 | 0,063 | 0,028 |
| **2010→2015** (2,3 %) | azar | 0,023 | 0,023 | 0,023 | |
| | densidad cruda | 0,051 | 0,050 | 0,035 | |
| | prior de producto | 0,071 | 0,110 | 0,042 | 0,022 |
| | **densidad sola** | **0,085** | 0,150 | 0,055 | 0,023 |
| | **capas** | **0,082** | 0,160 | 0,055 | 0,023 |
| **2015→2020** (2,0 %) | azar | 0,020 | 0,020 | 0,020 | |
| | densidad cruda | 0,052 | 0,050 | 0,033 | |
| | prior de producto | 0,061 | 0,080 | 0,037 | 0,020 |
| | **densidad sola** | **0,075** | 0,110 | 0,050 | 0,020 |
| | **capas** | **0,074** | 0,110 | 0,051 | 0,020 |

**Diferencia `capas` − `densidad_sola`** (intervalo del 95 % por remuestreo de países):

| Prueba | p@10 por país | p@20 por país | AUC-PR |
|---|---|---|---|
| 2005→2010 | +0,004 (−0,006; +0,013) | +0,003 (−0,003; +0,008) | +0,000 (−0,000; +0,001) |
| 2010→2015 | +0,004 (−0,005; +0,013) | −0,003 (−0,009; +0,003) | +0,000 (−0,000; +0,001) |
| 2015→2020 | −0,001 (−0,007; +0,007) | −0,001 (−0,006; +0,003) | +0,001 (−0,000; +0,001) |

## Lo que se ve
1. **La condición de paso a la Fase 2 no se cumple (todavía).** El modelo con capas **no supera** a la densidad sola en ninguna ventana: las diferencias son de ±0,004 en precision@20 por país, con intervalos que incluyen el cero, y de ±0,001 en AUC-PR. Los intervalos miden unos ±0,006 en precision@20 y ±0,01 en precision@10: mejoras menores que eso no se distinguen.
2. **Las capas casi no mueven el ranking:** el puntaje con capas y sin ellas tiene una correlación de rangos de 0,995, y el aporte de las capas al logit tiene un desvío de 0,12 contra 0,71 de la densidad (ventana 2015). Los coeficientes son significativos dentro de la muestra (ver el otro documento) pero su efecto es chico.
3. **Lo que sí predice es la densidad combinada con los efectos fijos.** Con la densidad sola y los efectos de país y de producto, la precision@20 por país es 3 a 4 veces la tasa base (0,075 a 0,088 contra 0,020 a 0,028). La densidad cruda, sin efectos fijos, llega a 2 a 2,6 veces (0,051 a 0,057). El efecto de producto solo («los productos que entraron antes siguen entrando») ya da 0,061 a 0,080.
4. **Las cifras dentro de la muestra del baseline de Ever (precision@20 de 0,40 a 0,60) eran un artefacto:** fuera de muestra, la precision@100 agrupada va de 0,11 a 0,16 y no se compara con la literatura (otro panel y otra definición de la entrada).
5. **Calibración deficiente en los extremos:** en el decil superior de probabilidad, el modelo predice 0,11 a 0,14 y la frecuencia real es 0,06 a 0,08 (el doble); en los deciles bajos subestima. Las probabilidades sirven para ordenar, no para leerlas como valores. Brier igual a la tasa base: sin ganancia en probabilidad.
6. **Paraguay (2015→2020):** 13 entradas en 998 productos; la lista de 20 acertó 1 (tabaco, 2403), igual con y sin capas. Los casos de Paraguay se estudian aparte (arneses, frigoríficos, biocombustibles).

## Qué NO prueba este resultado
- No prueba que las capacidades no importen: puede ser que las capas estén mal medidas (precio de la electricidad solo 2014-2019, requisitos de la tecnología de EE. UU., LPI de percepción y arrastrado hacia atrás en 2000 y 2005), o que midan lo mismo que el desarrollo general (correlación 0,94 del capital físico con el PIB per cápita).
- Anacronismos aceptados que favorecerían a las capas en las pruebas de 2005 y 2010 (usan información posterior); aun así no ganan.
- Con una sola ventana de entrenamiento (prueba 2005) los efectos fijos están poco estimados.

## Opciones para seguir (a decidir)
1. **XGBoost de control (tarea 1.10):** ver si una relación no lineal entre capas y entradas mejora la predicción. Si tampoco, la conclusión es robusta.
2. **Capas sin efectos fijos de producto y país** (Mundlak, D2 b): los efectos fijos pueden estar absorbiendo lo que las capas aportan.
3. **Revisar la medición de las capas** (por ejemplo, requisitos con la tecnología de otros países o intensidades por sector de cada país).
4. **Aceptar que el modelo nacional (M1) es densidad + efectos fijos** y usar las dotaciones como **diagnóstico de brechas** (M3) y no como parte de la probabilidad. Habría que corregir la condición de paso del plan.

## Cómo repetirlo
```bash
uv run python -m src.modelos.backtest_nacional
```
Escribe `data/model/backtest_resultados.csv`, `backtest_resultados_diferencias.csv` y `backtest_resultados_calibracion.csv`.
