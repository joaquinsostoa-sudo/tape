# ¿Qué tan bien predice la densidad territorial por sí sola?

Fecha: 2026-10-16. Código: `src/fase2/presencia.py`, `densidad_territorial.py` y `prueba_densidad.py` (8 pruebas en `tests/test_fase2_densidad.py`). Diseño y criterio declarados **antes de correr**: D34 en `docs/supuestos.md` (commit `371e191`; el código se commiteó antes de correrlo, `ec07a7a`).
Salidas (en `data/model/`): `prueba_densidad_territorial.csv` y `prueba_densidad_territorial_descriptivos.csv`.

## Veredicto
**La densidad NO cumple el criterio declarado.** Según la regla de Joaquín («si no lo hace bien, vamos directo al diagnóstico»), se pasa al diagnóstico multi-capa. Las capas no se pueden probar como predictoras: no hay valores de 2010 de energía, logística ni capital humano.

## En palabras simples
Se probó si saber **qué sectores manufactureros ya hay en un distrito** (y qué tan emparentados están con los demás, según el comercio de otros países) permite adivinar **qué otros sectores hay** en ese mismo distrito. Se hizo por separado con el Censo Económico 2011 (datos de 2010) y con el mapa MIC 2026, en 159 distritos y 35 sectores. Se comparó contra dos reglas simples: «el sector es común en el resto de los distritos» y «el distrito es grande».

## Resultado principal (presencia = concentración relativa mayor a 1,5)
AUC: 0,5 es azar y 1 es perfecto. Entre paréntesis, el intervalo del 95 %.

| | Censo 2010 | MIC 2026 |
|---|---|---|
| **Densidad** | 0,640 (0,613 a 0,662) | 0,585 (0,550 a 0,614) |
| Base 1: el sector es común en otros distritos | 0,780 (0,746 a 0,812) | 0,614 (0,586 a 0,646) |
| Base 2: el distrito es grande | 0,464 (0,434 a 0,495) | 0,549 (0,516 a 0,577) |
| **Densidad menos base 1** | **−0,140** (−0,183 a −0,102) | **−0,029** (−0,092 a +0,026) |
| **Densidad menos base 2** | **+0,176** (+0,140 a +0,215) | **+0,037** (+0,007 a +0,069) |

**Criterio (mejora de al menos 0,03 sobre cada base, con el intervalo por encima de cero, en las dos fuentes): no se cumple.** La densidad supera a la base del tamaño (en las dos fuentes), pero **no supera a la base «el sector es común en otros distritos»**: en el censo la pierde por mucho y en el MIC queda igual.

Con la presencia alternativa (al menos una unidad): censo 0,806 contra 0,794 y 0,781 (diferencias +0,012 y +0,025: no llega a 0,03); MIC 0,687 contra 0,826 y 0,664 (−0,139 y +0,023). Tampoco cumple.

## Descriptivos (no son el criterio)
| | Censo 2010 | MIC 2026 |
|---|---|---|
| Tasa base (celdas con presencia) | 18,8 % | 16,0 % |
| AUC-PR de la densidad | 0,270 | 0,236 |
| Precisión entre los 3 sectores de mayor densidad de cada distrito | **0,8 %** | **1,5 %** |
| … contra la tasa base del distrito | 18,9 % | 16,0 % |
| AUC dentro de cada distrito | **0,29** | **0,16** |

**Dentro de un mismo distrito, la densidad ordena los sectores peor que el azar** (AUC por debajo de 0,5; los 3 sectores de mayor densidad casi nunca son los presentes).

## Secundario: entradas 2010 → 2026 (con la advertencia declarada)
Entre las 4.520 celdas ausentes en 2010, 621 (13,7 %) aparecen en 2026. AUC de la densidad de 2010: **0,537** (0,504 a 0,568), contra 0,559 la prevalencia del sector y 0,568 el tamaño del distrito (diferencias −0,022 y −0,031, con intervalos que incluyen el cero). **La densidad no predice las entradas mejor que las bases.** Recordar que las dos fuentes no son comparables (21.131 contra 14.857 establecimientos manufactureros).

## Por qué pasa (diagnóstico de la prueba ya corrida, no una nueva especificación)
1. **La densidad calculada con el comercio mundial no se parece a lo que es común en los distritos de Paraguay.** Los sectores con mayor densidad media son tabaco, metales no ferrosos, confecciones, bebidas y cuero, que son **raros** (presentes en 1 a 12 % de los distritos); los sectores más comunes (alimentos balanceados, aceites, frutas y hortalizas procesadas, molinería, frigoríficos) tienen densidad media más baja. La correlación entre la densidad media de un sector y su presencia es de apenas 0,14. Por eso, al ordenar sectores dentro de un distrito, la densidad cruda empuja hacia arriba a sectores que casi no existen.
2. **La presencia por concentración relativa (LQ) es composicional**: si un distrito se especializa en algunos sectores, los demás quedan por debajo; 60 % de los pares de sectores tienen presencias con correlación negativa. Con una definición no composicional (al menos una unidad) el AUC dentro del distrito también queda por debajo de 0,5 (0,25 y 0,24).
3. **La proximidad internacional es un buen mapa de qué sectores se parecen, pero no de qué es frecuente en la manufactura paraguaya** (industrias de alimentos y madera).

**Qué no se hizo:** una versión de la densidad que reste el nivel medio de cada sector (para que ordene dentro del distrito) podría contener señal que esta versión no ve. Probarla sería una especificación nueva: debe declararse antes de correrla y no cambia el veredicto de la prueba declarada.

## Qué implica
- **Se pasa al diagnóstico multi-capa** (D31 aplicado a cada capa que el bien exige), como se decidió.
- **La densidad que usamos en el matcheo de un bien nuevo (D32) y en el documento de Ever (D26) debe leerse como descripción de «qué bienes relacionados ya produce el distrito», no como una predicción.**
- D16 (las capas son diagnóstico) queda reforzada, aunque la prueba de capas como predictoras no se pudo hacer.

## Limitaciones
- Censo 2011 y MIC 2026 no miden lo mismo. La asignación de actividades a sectores TAPE tiene confianza por fila. Los distritos nuevos se agregan a su unidad de 2011.
- El AUC agrupado mezcla diferencias entre sectores y entre distritos (por eso las dos bases). Las bases se calcularon con la muestra completa y el remuestreo fue de distritos.
- Resultados como asociación, no causalidad.
