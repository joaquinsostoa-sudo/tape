# CLAUDE.md — TAPE (Territorio, Actividades y Potencial Económico)

Proyecto del Laboratorio de Desarrollo Económico (LabDE). Responder siempre en español. Fuentes originales en `docs/` (PDF y `.txt` extraído). Plan vigente: `docs/PLAN_fase0_fase1.md`.

## Objetivo y preguntas
Predecir a qué actividades puede diversificarse Paraguay (o un territorio), dónde, con qué probabilidad, qué falta y quién debe actuar. Seis preguntas: (1) factibilidad, (2) valor, (3) dónde (departamento/ciudad), (4) qué brechas (capital humano, logística, energía, insumos, crédito, regulación), (5) quién actúa y con qué instrumento (mercado / acción colectiva / Estado), (6) validación histórica. Lógica: el espacio producto define candidatos → las capas de capacidades ajustan la probabilidad → el tipo de brecha define quién actúa. Los "saltos largos" (IED, maquila: arneses) son una categoría propia de política.
Prioridad de uso: herramienta interna para producir servicios (diagnósticos territoriales, estudios sectoriales, localización de inversiones) y después la web pública. Las salidas deben servir para fichas y estudios.

## Taxonomías pivote
- **Sectores TAPE**: ~40–60 sectores, intermedios entre CIIU 2 dígitos y subsectores MIC. Jerárquicos: cada uno pertenece a un grupo de las 33 actividades CNAEP, 21 de la MIP, 7–8 de crédito, 8 ramas EPHC y 6 actividades regionales.
- **Territorio**: ciudad/distrito anidado en departamento (17). Puntos y líneas del mapa MIC se asignan a ciudad por geoprocesamiento.
- **Regla central**: cada dato entra en su **nivel nativo de agregación**; nada se desagrega artificialmente. Un sector hereda el valor de su grupo y el modelo sabe que es dato grueso.
- Tablas puente: HS6/NCM8 → CPC → CIIU Rev.4 → sector TAPE (correspondencias ONU, pesos por valor exportado); MIC → CIIU → sector (manual, una vez); carreras → CINE-F → sector; leyes → sector.

## Módulos y ecuaciones
Notación: c país, p producto, s sector TAPE, j ciudad, t año, k capa.

**Bloques**: `RCA_cpt = (X_cpt/Σ_p X_cpt)/(Σ_c X_cpt/Σ_cΣ_p X_cpt)`, `M_cpt = 1[RCA≥1]`; `φ_pp' = min{P(M_p=1|M_p'=1), P(M_p'=1|M_p=1)}`; `d_cpt = Σ_p' φ_pp' M_cp't / Σ_p' φ_pp'`. PCI y COG vienen del Atlas.

**M1 (nacional)**: resultado `E_cp,t→t+h = 1[RCA_cpt<0.5 ∧ RCA_cp,t+h≥1]`, h=5 o 10. Logit: `Pr(E=1)=Λ(α_ct + γ_pt + β d_cpt + Σ_k θ_k r_pk a_ckt + Σ_k λ_k d_cpt r_pk a_ckt)`. r_pk = requisito del producto (energía, capital, habilidades, valor/peso), a_ckt = dotación del país (costo energía, capital humano, crédito/PIB, logística), ambos estandarizados. Panel ~180 países, ventanas 2000→2005→2010→2015→2020, HS4, errores agrupados por país. Control: XGBoost + SHAP.

**M2 (territorial)**: unidad sector×ciudad (foto MIC 2026). `φ^dom_ss'` y `D_sj` análogos a M1 con presencia `P_sj`. Binomial negativa jerárquica: `log μ_sj = α_s + u_dep(j) + β1 D_sj + β2 Σ_j' w_jj' D_sj' + Σ_k θ_k r_sk z_jk + log(PEA_j)`, `u_dep~N(0,σ²)`. Potencial no realizado: y_sj=0 con probabilidad predicha alta. Estimación bayesiana.

**M3 (brechas y valor)**: `ΔP_sk = Pr(E_s=1|a_k=ā_k) − Pr(E_s=1|a_k=a^PY_k)`, `k*_s = argmax_k ΔP_sk` (ā = mediana de países/ciudades donde sí se desarrolló). Brechas no estimables (regulación, MIP, crédito sectorial) = indicadores diagnósticos separados. Valor: `V_s = Σ_m ω_m ṽ_sm`, m∈{PCI, COG, salario, formalidad, productividad, BL, FL}; `L=(I−A)^-1`, `BL_j = (1/n Σ_i l_ij)/(1/n² Σ_iΣ_j l_ij)`.

**M4 (política)**: nivel 0 mercado (prob. alta, ningún ΔP>ε); 1 ajuste puntual (una brecha >ε, privada); 2 acción colectiva (≥2 brechas o una de coordinación/bien público); 3 Estado/apuesta (regulatoria, infraestructura pesada, o prob. baja con valor alto). ε = umbral, por definir.

**Validación**: métrica principal **precision@k** (listas cortas), **AUC-PR** (entradas raras, 1–2%), **calibración**. **Siempre contra el modelo de densidad sola**, no contra umbrales absolutos. Pruebas: backtest nacional (entrenar hasta 2005, predecir 2005–2015), países excluidos, aporte de capas, casos Paraguay (arneses, frigoríficos, biocombustibles), territorial hacia adelante (maquila, 60/90) y hacia atrás (Censo 2011). Robustez: HS4 vs HS6, h=5 vs 10, umbrales RCA alternativos.

## Reglas de trabajo
1. **No tocar `data/raw/`**: solo lectura. Limpieza va a `data/clean/`, derivados a `data/model/`.
2. **Toda fuente se registra en `data/fuentes.csv`** (URL, fecha, versión, licencia) al descargarla.
3. **Excluir energía de Itaipú/Yacyretá (HS 271600)** del comercio y **marcar reexportaciones** (columna explícita, no borrar en silencio).
4. **Partición temporal sin fuga**: entrenamiento termina en t−h; φ, densidad y RCA de referencia se calculan solo con datos ≤ t (nunca con toda la muestra). Exigir **entradas sostenidas** (RCA se mantiene) como variante/robustez.
5. **Toda tabla puente lleva nivel de confianza por fila** (alta/media/baja) y fuente. Los mapeos dudosos los valida el equipo.
6. **Documentar supuestos** en `docs/supuestos.md` (decisión, fecha, alternativa descartada).
7. Resultados como asociación, no causalidad. Mostrar incertidumbre siempre.
8. Si un dato no se puede bajar automáticamente: decir exactamente qué archivo conseguir y en qué carpeta de `data/raw/<fuente>/` ponerlo (cada una tiene README).
9. Inconsistencias en los documentos: señalarlas al usuario, no corregirlas en silencio.

## Forma de trabajo
Una tarea acotada por vez con criterio de terminado. Si implica una decisión metodológica, proponer opciones y esperar respuesta. Al terminar: resumen, tabla o gráfico de control y commit con mensaje claro (autor: Joaquín Sostoa).

## Decisiones tomadas (detalle en `docs/supuestos.md`)
- Sectores TAPE parten de CIIU Rev.4 (D9). Unidad común: división CIIU de 2 dígitos, bajando a 3-4 donde haga falta, con el sector TAPE encima (D12). Las carreras del MEC se vinculan a CIIU/sector, no a HS (D11).
- HS92 a 4 dígitos para estimar; 6 dígitos para el puente a CIIU y la robustez (D5).
- Se excluyen CONSUMO, VIVIENDA e Impuestos: no son actividades económicas.

## Decisiones abiertas (ver el plan)
Agregación producto→sector (D1); predicción fuera de muestra con efectos fijos país-año (D2); cómo calcular φ sin fuga (D3); fuente de intensidades r_pk y de costo de energía (D4); marcar reexportaciones (D6); entrada sostenida (D7); muestra de países (D8); anidamiento de las clasificaciones agregadas (comprobado: no anidan del todo, ver `docs/`); fórmula de ε (D10).

## Datos y herramientas locales
- Clasificaciones locales ya mapeadas a CIIU (borrador): `src/puentes/clasificaciones_locales.py` → `data/clean/clasificaciones_locales_ciiu.csv` y `ciiu4_atomos_clasificaciones.csv`.
- Mapa MIC: el visor Zoho (https://mapaprodpy.mic.gov.py/) se puede leer con el navegador integrado; no ofrece descarga. Resumen en `data/raw/mic_mapa/`.
- Descargas: `uv run python -m src.descargas.todas` (idempotente; manifiesto en `data/raw/<fuente>/MANIFEST.json`).
- Registro de títulos del MEC: contiene nombre y documento de personas; usar solo agregados (carrera, institución, mes) y no guardar datos personales.

## Hoja de ruta (estado)
- **Fase 0 Fundamentos** ← *estamos aquí*: hechos estructura, CLAUDE.md, fuentes de Fase 1 descargadas y taxonomía de 67 sectores TAPE (`docs/taxonomia.md`, `data/clean/taxonomia_sectores_tape.csv`). Falta la tarea 0.5: puente HS → CPC → CIIU → sector (biocombustibles y arneses se fijan por producto HS).
- Fase 1 Módulo nacional: descargas, depuración, RCA/φ/densidad, logit + XGBoost + backtest. Paso si el modelo con capas supera a la densidad sola en precision@k.
- Fase 2 Territorial (capas MIC, tabla MIC→CIIU, MEC, modelo jerárquico). Fase 3 Brechas, valor, política (EPHC, cuentas, MIP, crédito, SIMEL, leyes). Fase 4 Interfaz (FastAPI + MapLibre sobre la app Vercel). Fase 5 Monitoreo y difusión.
- Datos locales (MIC, MEC, EPHC, BCP, maquila, 60/90) aún no disponibles: se trabaja primero con datos públicos descargables.

## Convenciones de código
Python 3.12, `uv`. Funciones pequeñas y puras, con tipos (`mypy`), docstring corto. Una prueba en `tests/` por cada cálculo clave (RCA, φ, densidad, definición de entrada, partición temporal) con ejemplos mínimos hechos a mano. Scripts reproducibles en `src/` (no lógica en notebooks). Datos tabulares en parquet; consultas con DuckDB/polars. Nombres de columnas en español sin tildes y snake_case (`pais`, `producto`, `anio`, `rca`); códigos ISO3 para países, HS como texto de 6 dígitos. Formato y lint: `ruff`.
