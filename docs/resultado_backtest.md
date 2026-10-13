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

## Controles: XGBoost y variante sin efectos fijos (2026-10-13)
Dos pruebas de que el resultado no depende de la forma del modelo. Mismo esquema fuera de muestra, mismas filas.

**1. XGBoost con SHAP (tarea 1.10, `src/modelos/xgb_control.py`).** Dos modelos con hiperparámetros fijados de antemano (300 árboles, profundidad 4, tasa 0,05; sin ajustar en la prueba): `xgb_densidad` (densidad + país y producto como categorías) y `xgb_capas` (más las dotaciones a_k y los requisitos r_k; los árboles pueden armar solos las interacciones y las no linealidades).

| Diferencia `xgb_capas` − `xgb_densidad` | 2005→2010 | 2010→2015 | 2015→2020 |
|---|---|---|---|
| precision@20 por país | +0,005 (−0,003; +0,015) | **−0,010 (−0,020; −0,003)** | +0,006 (0,000; +0,014) |
| AUC-PR | +0,001 (−0,002; +0,004) | 0,000 (−0,001; +0,002) | +0,001 (−0,000; +0,003) |

- **Sin ganancia consistente:** una ventana a favor, una en contra y una neutra. XGBoost con país y producto rinde igual que el logit de densidad sola (precision@20 por país de 0,069 a 0,088).
- **SHAP (prueba 2015, `docs/figuras/xgb_shap.png`):** el modelo se apoya en el producto (|SHAP| 0,66), el país (0,49) y la densidad (0,36). Las capas pesan entre 0,007 y 0,044 (la mayor, la logística del país, que además hace de identificador del país).
- La precision@100 agrupada de XGBoost sube mucho en 2005 (0,17 a 0,20 contra 0,11 del logit), pero no en las otras ventanas (0,13 a 0,18): es volátil con tan pocas posiciones.

**2. Sin efectos fijos, estilo Mundlak (D2 b, `src/modelos/mundlak.py`).** Se quitan los efectos de país y producto (que absorben las dotaciones y los requisitos por separado) y se los reemplaza por la densidad media del país y del producto en la ventana. Se agregan por pasos: `mundlak_efectos` (a_k y r_k por separado) y `mundlak_capas` (más las interacciones r·a).

| Diferencia | 2005→2010 | 2010→2015 | 2015→2020 |
|---|---|---|---|
| `efectos` − `densidad` (precision@20) | **+0,010 (+0,003; +0,018)** | +0,001 (−0,006; +0,008) | −0,006 (−0,013; +0,001) |
| `efectos` − `densidad` (AUC-PR) | +0,003 (0,000; +0,006) | +0,001 (−0,002; +0,003) | +0,001 (0,000; +0,003) |
| `capas` − `efectos` (precision@20) | 0,000 (−0,006; +0,005) | +0,001 (−0,005; +0,007) | +0,004 (−0,001; +0,008) |
| `densidad Mundlak` − `densidad sola con efectos fijos` (precision@20) | **−0,033** (−0,049; −0,019) | **−0,033** (−0,048; −0,018) | **−0,022** (−0,036; −0,008) |

- **Las interacciones r·a no aportan nada** (tercera fila), con o sin efectos fijos.
- **Los efectos principales de las capas dan una ganancia chica solo en 2005**, la ventana con más anacronismos a favor (energía de 2014-2019 y LPI de 2007 aplicados a 2005). En 2010 y 2015 no hay ganancia.
- **Sin efectos fijos el modelo es mucho peor** (cuarta fila): la propensión histórica de cada país y de cada producto a entrar es información que la densidad media no recupera.
- **La logística del país tiene coeficiente negativo en todas las ventanas** (−0,23 a −0,33 estandarizado): los países mejor dotados tienen menos entradas, probablemente un efecto de madurez o convergencia (los ricos ya tienen RCA alto en lo que pueden producir), no de complementariedad.

**Conclusión de los controles:** el resultado nulo **resiste** a la no linealidad (XGBoost) y a quitar los efectos fijos (Mundlak): las capas, tal como están medidas, no mejoran la predicción fuera de muestra de la entrada por encima de la densidad y la propensión de país y producto.

## Robustez de la definición de la entrada (2026-10-13)
Se repitió el backtest con cinco definiciones alternativas (`src/modelos/robustez_entrada.py`) y se comparó `capas` contra `densidad_sola` en cada una. La definición base reproduce los resultados anteriores (control de consistencia).

| Definición | Pruebas | Entradas | Tasa base | precision@20 por país: densidad sola → con capas | Diferencia con capas (IC 95 %) | Diferencia AUC-PR |
|---|---|---|---|---|---|---|
| **Base** (RCA_t < 0,5 → RCA_t+5 ≥ 1) | 2005, 2010, 2015 | 2.116 a 2.581 | 2,0 a 2,8 % | 0,088→0,091 / 0,085→0,082 / 0,075→0,074 | +0,003 / −0,003 / −0,001 (todos con 0 dentro) | 0,000 a +0,001 |
| **h = 10** (2010→2020) | 2010 | 3.194 | 3,1 % | 0,097→0,094 | −0,003 (−0,010; +0,005) | +0,001 (+0,000; +0,002) |
| **2 de 3 años** | 2005, 2010, 2015 | 1.453 a 1.780 | 1,4 a 1,9 % | 0,061→0,060 / 0,067→0,065 / 0,058→0,056 | −0,001 / −0,002 / −0,002 (todos con 0 dentro) | 0,000 a +0,001 |
| **Parte de RCA < 0,25** | 2005, 2010, 2015 | 1.387 a 1.706 | 1,5 a 2,1 % | 0,065→0,064 / 0,063→0,063 / 0,057→0,060 | −0,001 / 0,000 / +0,003 (todos con 0 dentro) | 0,000 |
| **Parte de RCA < 1** | 2005, 2010, 2015 | 4.403 a 4.942 | 3,8 a 4,8 % | 0,145→0,146 / 0,136→0,134 / 0,142→0,132 | +0,001 / −0,002 / **−0,010 (−0,018; −0,002)** | 0,000 a +0,001 |
| **Llega a RCA ≥ 1,5** | 2005, 2010, 2015 | 1.242 a 1.522 | 1,2 a 1,7 % | 0,059→0,060 / 0,051→0,052 / 0,048→0,048 | +0,001 / 0,000 / 0,000 (todos con 0 dentro) | 0,000 |

- **El resultado no depende de la definición de la entrada.** En las 16 combinaciones de definición y ventana, el modelo con capas no supera a la densidad sola en ninguna: las diferencias van de −0,010 a +0,003 en precision@20 y el intervalo siempre incluye el cero salvo un caso, donde las capas empeoran (parte de RCA < 1, 2015→2020).
- **En AUC-PR las diferencias son 0,000 a +0,001.** La única con intervalo estrictamente positivo (h = 10: +0,001, IC +0,000 a +0,002) es de una milésima.
- Con el horizonte de 10 años solo hay una prueba posible (2010→2020), entrenada con una sola ventana (2000).
- **No se probó todavía la robustez de HS4 contra HS6 (D5):** requiere extraer el comercio a 6 dígitos de la base de Ever y asignar los requisitos por prefijo.

## Opciones para seguir (a decidir)
1. **Revisar la medición de las capas** (los requisitos con la tecnología de EE. UU., el precio de la electricidad de 2014-2019, el LPI de percepción, y todas ellas muy correlacionadas con el desarrollo).
2. **Aceptar que M1 es densidad + efectos fijos de país y producto**, y usar las dotaciones como **diagnóstico de brechas** (M3: comparar a Paraguay con los países que sí desarrollaron cada producto, capa por capa), sin que entren a la probabilidad. Habría que corregir la condición de paso del plan.
3. ~~Probar otras definiciones de la entrada~~ (hecho, ver arriba: no cambia el resultado). Queda la robustez HS4 contra HS6.

## Cómo repetirlo
```bash
uv run python -m src.modelos.backtest_nacional
```
Escribe `data/model/backtest_resultados.csv`, `backtest_resultados_diferencias.csv` y `backtest_resultados_calibracion.csv`. Los controles: `uv run python -m src.modelos.xgb_control` y `uv run python -m src.modelos.mundlak`.
