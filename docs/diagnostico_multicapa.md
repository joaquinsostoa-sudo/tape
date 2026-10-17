# Diagnóstico multi-capa por industria y distrito (D36)

Fecha: 2026-10-17. Código: `src/puentes/diagnostico_multicapa.py` (6 pruebas en `tests/test_diagnostico_multicapa.py`). Reglas declaradas **antes de implementar**: D36 en `docs/supuestos.md` (commit `389e576`).
Salidas (en `data/model/`): `diagnostico_multicapa.csv` (17.621 celdas: 67 sectores × 263 distritos), `diagnostico_multicapa_referencias.csv` (umbral por sector y capa), `diagnostico_multicapa_sensibilidad.csv`, `diagnostico_multicapa_control.csv` y fichas de ejemplo: `diagnostico_multicapa_ficha_S16.csv`, `..._S22.csv` y `..._ficha_distrito_CIUDAD_DEL_ESTE.csv`.

## Para qué sirve
Con la misma matriz se responden dos preguntas: **por distrito**, qué podría desarrollarse (tiene la capacidad o le faltan pocas); **por industria**, qué distritos son más compatibles. Y según el tipo de brecha, quién debe actuar. **No es una predicción ni una probabilidad:** dice «el distrito tiene (o no) lo que tienen quienes ya producen», no «va a producir» (D16, D34). Resultados como asociación, no causalidad.

## Cómo se lee una celda (sector × distrito)
- **Capas exigidas:** base de capital humano (siempre) y, según el sector, formación específica, energía, logística y recursos. Se evalúa solo lo que el sector exige.
- **Umbral:** el percentil 10 de los distritos que hoy producen ese sector (mapa MIC 2026) en cada capa. **Estado:** *sin brecha* (en el umbral o por encima), *cerca del umbral* (hasta 10 puntos de percentil por debajo) o *con brecha* (más de 10 por debajo).
- **Nivel de política:** 0 mercado (ninguna brecha); 1 ajuste puntual (una brecha de formación o base de hasta 20 puntos); 2 acción colectiva (dos o más, o una de más de 20); 3 Estado (cualquier brecha de energía o logística). Una brecha de **recursos** es un límite duro: «no apto por recursos» y fuera del ranking.
- **Orden:** apto por recursos, menos brechas (energía y logística juntas cuentan como una), mayor margen mínimo sobre el umbral. Sin puntaje único. Hay dos rangos: `rango_en_industria` (entre distritos) y `rango_en_distrito` (entre sectores).
- **Situación:** *ya se produce*, *oportunidad no realizada* (sin brechas y no se produce), *no se produce, con brechas*, *no apto por recursos*, *sin referencia* y *datos incompletos*.
- **Complejidad (informativa, no entra en el orden):** PCI y COG del sector como percentil entre sectores, y el **escalón** (PCI del sector menos la mediana del PCI de los sectores que el distrito produce): más complejo, similar o menos complejo.

## Control
| Qué se mide | Resultado |
|---|---|
| Celdas | 17.621 (67 sectores × 263 distritos) |
| Ya se produce | 2.919 |
| Oportunidad no realizada | 5.983 |
| No se produce, con brechas | 2.242 |
| No apto por recursos | 320 |
| Datos incompletos | 108 |
| Sin referencia | 6.049 (23 sectores) |
| Productores evaluados sin ninguna brecha | **95,0 %** (por construcción cerca del 90 %: no es evidencia de que el criterio funcione) |
| Sectores con referencia según el número de capas que exigen | 1 capa: 5; 2: 14; 3: 15; 4: 8; 5: 2 |

**Sectores sin referencia (menos de 5 productores en el mapa MIC):** 21 tienen **0 productores**, porque el mapa MIC de industrias solo cubre manufactura y alguna extracción: los cultivos (S01, S02), la pesca (S07), agua y saneamiento (S46), el comercio mayorista (S49) y los servicios (S51 a S66). Otros dos tienen 4 productores: otro equipo de transporte (S42) y construcción (S48). **El diagnóstico hoy no cubre agro ni servicios.** Con 5 a 9 productores (confianza baja) hay un solo sector: siderurgia y fundición (S36, 9 productores).

## Sensibilidad (celdas que cambian de nivel frente al caso principal)
| Variante | Celdas que cambian | Oportunidades no realizadas |
|---|---|---|
| Principal (30 km, productores, sede principal, banda 10, corte 20) | 0 | 5.983 |
| Umbral en la mediana de todos los distritos | 5.221 | 3.240 |
| Escala de 15 km | 1.374 | 5.631 |
| Escala de 60 km | 1.143 | 6.283 |
| Reparto parejo entre sedes | 502 | 5.907 |
| Banda de 5 puntos | 1.032 | 5.357 |
| Banda de 15 puntos | 917 | 6.637 |
| Corte de nivel 1 en 10 puntos | 587 | 5.983 |
| Corte de nivel 1 en 30 puntos | 180 | 5.983 |

**El resultado depende mucho del estándar:** con la mediana de todos los distritos en vez del percentil 10 de los productores, cambian 5.221 celdas (casi la mitad de las evaluadas). Las tolerancias (banda de 10, corte de 20) mueven entre 1 y 6 % de las celdas.

## Ejemplos
- **S16 (cinco capas exigidas: base, formación, energía, logística y recursos de agricultura; 34 productores):** 34 ya producen, 124 oportunidades no realizadas, 88 con brechas, 12 no aptos por recursos y 5 con datos incompletos. Los primeros son distritos agrícolas de Cordillera, Caaguazú y Guairá, donde la capa limitante es recursos.
- **S22 (solo la base; 96 productores):** 96 ya producen, 130 oportunidades no realizadas y 37 con brechas. Un sector que exige una sola capa aparece «viable» casi en todos lados: es una afirmación débil.
- **Ciudad del Este (vista por distrito):** la ficha ordena los sectores por compatibilidad y marca cuáles ya produce.

## Hallazgos que cambian cómo se leen
1. **La base de capital humano, la energía y la logística siguen el mismo patrón** (correlación de rangos entre 0,83 y 0,85): las tres se concentran en el Gran Asunción. Un distrito con brechas en las tres tiene, en la práctica, una sola carencia: estar lejos de ese polo. Los recursos casi no se parecen a ellas (entre −0,37 y 0,33).
2. **Los productores casi nunca tienen brechas (95 %) por construcción**, y 5.983 celdas salen como oportunidad no realizada. No son recomendaciones: son distritos que no están por debajo de los productores más rezagados. Hay que cruzarlas con las capas exigidas y con la confianza de la referencia.
3. **Una celda con una capa evaluada sin dato en el distrito no se ordena ni se marca como oportunidad** (108 celdas: los 4 distritos sin MapBiomas y María Antonia, sin coordenadas). Esta regla no estaba escrita en D36 y se agregó al implementar, porque la primera corrida ponía en primer lugar a distritos a los que solo les faltaba un dato.

## Limitaciones
- El mapa MIC es un stock de 2026 y solo cubre industrias: **sin agro ni servicios**.
- Percentiles dentro del país: dicen posición relativa, no un nivel absoluto. Distancias en línea recta. Recursos mide clase de tierra y no cultivo.
- La asignación de capas a sectores (exigencia por mediana de productos, rubros de recursos) y la de carreras a sectores es un juicio que el equipo debe validar.
- La complejidad del sector es la de los productos exportables del Atlas; no existe una complejidad propia del distrito.
