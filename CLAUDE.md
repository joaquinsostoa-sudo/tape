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
Agregación producto→sector (D1); anidamiento de las clasificaciones agregadas (comprobado: no anidan del todo, ver `docs/`); fórmula de ε (D10).

## Decididas el 2026-10-12 (detalle en `docs/supuestos.md`)
- **D3**: φ con ventana de 5 años que termina en t, solo con datos ≤ t.
- **D4**: intensidades r_pk con NBER-CES y el puente NAICS→HS de Pierce y Schott (`docs/puente_requisitos.md`); energía = **precio de la electricidad** (Doing Business 2014-2019, promedio, barato = mejor; `docs/dotaciones.md`). Agro, minería y servicios quedan sin requisitos.
- **D7**: entrada = definición del documento (un solo año: RCA_t < 0,5 y RCA_t+h ≥ 1); robustez: RCA ≥ 1 en 2 de los 3 años que terminan en t+h. El promedio móvil de 3 años se descartó como definición de la entrada (más rachas de un año).
- **D8**: muestra = población ≥ 1 millón y exportaciones ≥ USD 1.000 millones en el año inicial (112 a 144 países, ≈ 97 % del comercio mundial); reportar el filtro.
- **D13** (2026-10-13): presencia para φ y densidad = RCA ≥ 1 en al menos 2 de los 3 **años de calendario** que terminan en t (RCA depurado); la entrada principal (D7) sigue siendo de un solo año. Variante de robustez: presencia de un solo año.
- **D2** (2026-10-13): efectos fijos y fuera de muestra, por propósito. (c) Coeficientes θ_k y λ_k (tarea 1.9): la especificación del documento (país-año y producto-año), dentro de la muestra, con errores agrupados por país; las interacciones r·a se identifican aunque los efectos absorban las dotaciones y los requisitos solos. (a) Backtest (1.11): efectos de país y de producto constantes más un indicador por ventana, entrenando solo con ventanas cuyo resultado se conocía en t y prediciendo la siguiente. (b) Efectos de Mundlak solo para países excluidos y Paraguay.
- **D15** (2026-10-13): el requisito de capital se empareja con el stock de capital real por trabajador de PWT (`capital_fisico`), no con el crédito/PIB; el crédito queda como robustez y como indicador separado de brechas (Fase 3). Razón: muestra mayor (97 contra 59 países en 2000) y sin pérdida medible; no es que prediga mejor.
- **D14** (2026-10-13): la primera edición del LPI se arrastra hacia atrás para tener logística en las ventanas de 2000 y 2005 (marca `lpi_hacia_atras`); robustez: modelo solo con datos reales (ventanas 2010 y 2015).
- **D6**: reexportaciones marcadas automáticamente (importaciones y exportaciones del mismo orden en BACI), con revisión posterior producto por producto y confirmación con la aduana.

## Datos y herramientas locales
- Clasificaciones locales ya mapeadas a CIIU (borrador): `src/puentes/clasificaciones_locales.py` → `data/clean/clasificaciones_locales_ciiu.csv` y `ciiu4_atomos_clasificaciones.csv`.
- Mapa MIC: el visor Zoho (https://mapaprodpy.mic.gov.py/) se puede leer con el navegador integrado; no ofrece descarga. Se interceptan las respuestas de sus gráficos (técnica y capas extraídas en `data/raw/mic_mapa/README.md`; limpieza en `src/limpieza/mic_*.py`).
- Datos manuales: `TAPE_datos_manuales.zip` (Drive); se arma con `uv run python -m src.empaquetar_datos_manuales`. Los tests que dependen de datos faltantes se saltan.
- Descargas: `uv run python -m src.descargas.todas` (idempotente; manifiesto en `data/raw/<fuente>/MANIFEST.json`).
- Registro de títulos del MEC: contiene nombre y documento de personas; usar solo agregados (carrera, institución, mes) y no guardar datos personales.

## Hoja de ruta (estado)
- **Fase 0 Fundamentos: CERRADA (2026-10-08).** Estructura, CLAUDE.md, fuentes de Fase 1 descargadas, taxonomía de 67 sectores TAPE (`docs/taxonomia.md`) y puente HS92 → CPC → CIIU → sector (`docs/puente_hs_sector.md`, `data/clean/puente_hs92_sector.csv`; biocombustibles y arneses por producto HS). También hay: PIB por 33 actividades y regional del BCP, equivalencias de las clasificaciones locales a CIIU, tabla CNAEP → sector, e industrias del mapa MIC por distrito y sector.
- **Fase 1 Módulo nacional** ← *estamos aquí*: hechas la 1.5 (dotaciones, `docs/dotaciones.md`) y la 1.6 (requisitos, `docs/puente_requisitos.md`). Ever subió borradores de 1.2, 1.3, 1.4, 1.7 y 1.8 en `src/modelos/`, sin revisar contra D3, D5 y D6; van a pasar a `densidad_np.py` y `logit_disperso.py`. Decididas D2, D3, D4, D6, D7, D8, D13 y D14; pendiente D1 (ver `docs/PLAN_fase0_fase1.md` y `docs/ESTADO.md`).
- Fase 1 Módulo nacional: descargas, depuración, RCA/φ/densidad, logit + XGBoost + backtest. Paso si el modelo con capas supera a la densidad sola en precision@k.
- Fase 2 Territorial (capas MIC, tabla MIC→CIIU, MEC, modelo jerárquico). Fase 3 Brechas, valor, política (EPHC, cuentas, MIP, crédito, SIMEL, leyes). Fase 4 Interfaz (FastAPI + MapLibre sobre la app Vercel). Fase 5 Monitoreo y difusión.
- Datos locales ya incorporados (2026-10-09; ver `docs/ESTADO.md` y `docs/COLABORACION.md`): BCP (PIB, regional, crédito), MIP, EPHC 2022-2025, censo agropecuario 2022, SIMEL, ANEAES, MEC (parcial) y siete capas del mapa MIC. Faltan títulos y carreras del MEC, Censo Económico 2011, materia prima, oferta-utilización del BCP, y maquila y 60/90 a nivel de proyecto (decidido no pedirlos). La Fase 1 usa solo datos internacionales.

## Rendimiento (aprendido el 2026-10-12)
Una consulta SQL que une cada par país-producto con todos los vecinos de la tabla de proximidad genera ≈ 1.600 millones de filas por ventana y llenó el disco de un integrante del equipo. Reglas: la densidad se calcula con matrices (`src/modelos/densidad_np.py`); los logit con efectos fijos de país y producto, con matrices dispersas (`src/modelos/logit_disperso.py`), no con `C(country) + C(product)` de statsmodels (matriz densa de 14 a 16 GB); no materializar uniones de más de unos 100 millones de filas; fijar `temp_directory` y limpiarlo. Detalle en `docs/optimizacion_modelos.md`.

## Convenciones de código
Python 3.12, `uv`. Funciones pequeñas y puras, con tipos (`mypy`), docstring corto. Una prueba en `tests/` por cada cálculo clave (RCA, φ, densidad, definición de entrada, partición temporal) con ejemplos mínimos hechos a mano. Scripts reproducibles en `src/` (no lógica en notebooks). Datos tabulares en parquet; consultas con DuckDB/polars. Nombres de columnas en español sin tildes y snake_case (`pais`, `producto`, `anio`, `rca`); códigos ISO3 para países, HS como texto de 6 dígitos. Formato y lint: `ruff`.
