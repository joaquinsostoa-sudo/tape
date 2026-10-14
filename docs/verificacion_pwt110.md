# Verificación de los resultados con PWT 11.0 (2026-10-14)

**Pregunta:** los modelos y cuadros anteriores se hicieron con Penn World Table 10.01; ¿cambia algo con la versión 11.0 (`data/raw/pwt/pwt110.xlsx`, 1950-2023)?
**Respuesta: no.** Se repitieron cinco análisis con el mismo código y los mismos datos de comercio, cambiando solo el capital humano y el capital por trabajador (la tabla de dotaciones). Los resultados con 10.01 quedaron guardados en `data/model/pwt1001/`.

## Qué cambió en los datos de entrada
- **Capital humano (`hc`):** casi igual (correlación 0,9985 entre versiones; cociente mediano 1,000).
- **Stock de capital real (`rnna`):** se reestimó (correlación 0,98; cociente mediano 1,21). Estandarizado por año, el capital por trabajador de Paraguay pasa del percentil 35 al 43.
- **Empleo y población:** iguales. Cobertura: 185 países; 145 con capital humano.

## Resultados, lado a lado
| Análisis | PWT 10.01 | PWT 11.0 |
|---|---|---|
| **Logit de entrada, capital humano (r·a)** | 0,088 (p < 0,001) | 0,087 (p < 0,001) |
| Logit de entrada, capital físico (r·a) | 0,004 (p = 0,83) | 0,002 (p = 0,91) |
| Logit de entrada, logística (r·a) | −0,063 (p = 0,013) | −0,062 (p = 0,015) |
| **Backtest: con capas − densidad sola, precision@20 por país** | +0,003 / −0,003 / −0,001 | +0,003 / −0,003 / −0,001 (mismos intervalos) |
| Backtest: diferencia en AUC-PR | 0,000 a +0,001 | 0,000 a +0,001 |
| **Corte transversal, capital humano (r·a)** | 0,193 (p < 0,001) | 0,190 (p < 0,001) |
| Corte transversal, capital físico | 0,072 (p = 0,021) | 0,076 (p = 0,017) |
| Corte transversal, logística | −0,093 (p = 0,016) | −0,093 (p = 0,016) |
| Corte transversal, tierra × tierra cultivable (no usa PWT) | 0,218 (p = 0,0015) | 0,218 (p = 0,0015) |
| **Cuadro de bloques (2015):** correlación de las 77 diferencias alto − bajo | | 0,9985; diferencia mediana 0 puntos, máxima 6,5; **0 celdas cambian de signo** y 1 de 77 cambia de significancia |
| **Requisito revelado − densidad sola (p@20 por país)** | −0,003 / −0,003 / −0,006 | −0,004 / −0,003 / −0,007 |

## Matices
- **Con el control de ingreso**, el capital humano en el corte transversal baja de 0,114 (p = 0,057) a 0,108 (p = 0,087), y el capital físico sigue cerca de cero con cualquiera de las dos versiones (de −0,03 a +0,02, no significativo). La lectura no cambia: el capital humano es muy estable sin el control y se debilita con él.
- **Requisito revelado, 2015→2020:** con 11.0 el intervalo de la diferencia con la densidad sola es (−0,014; −0,001) y ya no incluye el cero: las capas reveladas quedan **significativamente peores**, no solo sin mejora. Es una diferencia menor y no cambia la conclusión.
- Las dos fichas de brechas (arneses y etanol) ya se habían recalculado con 11.0 antes de esta verificación.

## Conclusión
Las conclusiones de `docs/resultado_backtest.md`, `docs/resultado_presente.md` y `docs/resultado_bloques.md` **se mantienen con PWT 11.0**; los números de esos documentos son los de PWT 10.01 y no se reescriben. De acuerdo con esto, la versión 11.0 queda como la oficial para las dotaciones.
