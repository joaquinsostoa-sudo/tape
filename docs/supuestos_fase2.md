# Supuestos de la Fase 2: módulo territorial de TAPE

Fecha: 2026-10-16. **Estado: declaración previa.** Este documento se escribe ANTES de correr cualquier modelo territorial. Fija las decisiones D19 a D26 (renumeradas el 2026-10-16: antes D17 a D24, que chocaban con D17 y D18 de `docs/supuestos.md`; el contenido no cambió). Cambiar cualquier criterio después de ver los resultados invalida el test.

## 1. Objetivo

Determinar si las capas de capacidades, medidas con **varianza territorial**, mejoran la predicción de la densidad territorial a nivel de distrito.

- **Si mejoran:** las capas se promueven a motor de predicción (se reabre D16).
- **Si no mejoran:** D16 se confirma. Las capas siguen siendo diagnóstico de brechas.

## 2. Decisión D19: unidad de análisis

- **Principal:** Distrito × Grupo de sectores TAPE (5-8 grupos).
- **Robustez:** Distrito × Sector TAPE (50-67 sectores).
- **Razón:** con ~238 distritos y ~50 sectores hay ~12.000 celdas. Muchas quedan vacías. Con grupos hay suficientes entradas para tener potencia estadística.

## 3. Decisión D20: definición de presencia

- **Principal:** LQ de establecimientos > 1.5.
- **Robustez:** LQ de ocupados > 1.5.
- **Definición de LQ:**
  LQ(d, s) = (establecimientos del sector s en distrito d / total establecimientos en d) / (establecimientos de s en el país / total país)
- **Razón:** LQ > 1.5 es más exigente que 1 y evita que distritos chicos aparezcan con "presencia" por ruido. Establecimientos para el principal porque el Censo 2011 lo tiene completo; ocupados como robustez.

## 4. Decisión D21: definición de entrada

- **Entrada = 1** si `presencia_2010 = 0` y `presencia_2026 = 1`.
- **Salida = 1** si `presencia_2010 = 1` y `presencia_2026 = 0`.
- **Persistencia = 1** si `presencia = 1` en ambos.
- **Ventana única:** 2010 → 2026.
- **Razón:** solo hay dos cortes disponibles. No hay forma de tener más ventanas.

## 5. Decisión D22: validación

- **KFold por distritos**, 5 folds, semilla 42.
- **Repetir 10 veces** con semillas distintas.
- **Bootstrap por distrito**, 1000 repeticiones, para IC 95%.
- **Razón:** con un solo período temporal, la validación cruzada por distritos es la única opción honesta. Reportar media y desviación entre folds.

## 6. Decisión D23: modelo

- **Principal:** Logit con efectos fijos de grupo de sectores.
- **Robustez:** XGBoost con 100 árboles.
- **Razón:** logit interpretable y comparable con Fase 1. XGBoost captura no linealidades. Si ambos coinciden, el resultado es robusto.

## 7. Decisión D24: capas a incluir

Solo 4 capas con varianza territorial real y fuente disponible:

| Capa | Fuente | Variable | Estado |
|---|---|---|---|
| Aglomeración | Censo 2011 + Censo 2022 | Establecimientos por km² | Lista |
| Logística | MIC mapa logístico | Distancia al puerto más cercano | Lista |
| Recursos naturales | Censo Agropecuario 2022 | Superficie agropecuaria por km² | Lista |
| Capital humano específico | MEC títulos + MEC escuelas | Técnicos por sector y distrito | En proceso |

**Excluidas explícitamente:**
- **Electricidad:** no hay consumo por distrito (solo infraestructura de transmisión, casi constante).
- **Crédito:** solo departamental, no distrital.
- **Cualquier capa sin varianza territorial.** No se sustituye por promedios nacionales ni departamentales.

## 8. Decisión D25: criterio de promoción de capas

Las capas se promueven a motor de predicción si y solo si, en el backtest territorial:

1. La diferencia en `precision@20` (con capas − sin capas) es **≥ 0.005**.
2. El IC 95% (bootstrap por distrito) **excluye el cero**.
3. Se cumple en **al menos 2 de 3 grupos** (manufactura liviana, manufactura pesada, agro/servicios).

**Si no se cumple, D16 se confirma:** capas siguen siendo diagnóstico.

## 9. Decisión D26: densidad territorial

- **Proximidad:** la misma que en Fase 1 (espacio de productos nacional, calculada con exportaciones de países).
- **Presencia:** la del distrito (LQ > 1.5).
- **Densidad territorial:**
  densidad(d, s) = Σ_{s'} φ(s, s') · presencia(d, s') / Σ_{s'} φ(s, s')
- **Razón:** extensión natural de Hidalgo/Neffke (2011) a nivel subnacional. No inventamos nada.

## 10. Lo que este test NO prueba

- No prueba que las capacidades no importen.
- No prueba que la densidad sea causal.
- No prueba que las capas estén bien medidas.
- Solo prueba: **dado el proxy de densidad territorial, ¿agregar capas territoriales mejora la predicción de entradas?**

## 11. Reglas no negociables

1. No correr el backtest antes de commitear este documento.
2. No incluir capas sin varianza territorial.
3. No cambiar el criterio D25 después de ver los resultados.
4. Reportar el resultado negativo si es negativo.
5. Si < 5 entradas por distrito, avisar antes de seguir.

## 12. Reproducibilidad

- Script de presencia: `src/fase2/presencia.py`
- Script de densidad: `src/fase2/densidad_territorial.py`
- Script de capas: `src/fase2/capas_territoriales.py`
- Script de backtest: `src/fase2/backtest_territorial.py`
- Resultado: `data/model/resultado_backtest_territorial.json`
- Decisión final: `docs/DECISION_fase2_capas.md`