# Plan de trabajo — Fase 0 y Fase 1 (módulo nacional)

Fecha: 2026-10-08. Alcance: solo datos públicos descargables (los datos MIC, MEC, EPHC, BCP, maquila y 60/90 llegan después; sus carpetas en `data/raw/` ya están preparadas con README).

Cada tarea es acotada, tiene un criterio de terminado y cierra con resumen + tabla/gráfico de control + commit. Las tareas marcadas **[DECISIÓN]** esperan tu respuesta antes de implementarse.

## Estado

| Tarea | Estado |
|---|---|
| 0.1 Estructura, entorno, `CLAUDE.md`, `fuentes.csv`, README de `data/raw` | Hecha |

---

## Fase 0 — Fundamentos

### 0.2 Verificar las fuentes internacionales
- **Qué**: abrir cada fuente (BACI, Atlas, WDI, PWT, LPI, concordancias ONU/WITS, ILOSTAT) y confirmar URL de descarga, versión vigente, último año, revisión HS y licencia (incluido uso comercial: la propuesta comercial lo exige).
- **Produce**: `data/fuentes.csv` actualizado (versión, cobertura, licencia, URL final) y `docs/verificacion_fuentes.md` con lo que no coincide con el documento técnico (p. ej. el "1995–2024 (?)" de BACI).
- **Verificación**: ninguna celda "(verificar)" en las fuentes de Fase 1. Tú revisas la columna de licencias.
- **Decisiones**: D5 (revisión HS).

### 0.3 Descargas de Fase 1
- **Qué**: un script por fuente en `src/descargas/` (`baci.py`, `atlas.py`, `wdi.py`, `pwt.py`, `lpi.py`, `concordancias.py`) con un módulo común que baja, guarda en `data/raw/<fuente>/`, calcula hash y registra fecha/versión en `fuentes.csv`. Idempotentes: si el archivo está, no lo vuelven a bajar.
- **Cómo se baja cada una** (a confirmar en 0.2):

| Fuente | Qué necesitamos | Cómo |
|---|---|---|
| **BACI** (CEPII) | Flujos bilaterales HS6 con valor y toneladas; códigos de país y producto | Zip por revisión HS desde la página de CEPII, descarga directa. Se usa HS92 por serie larga. Peso: varios GB. |
| **Atlas** (Growth Lab) | PCI, COG, RCA y distancia por país-producto-año; clasificación | API de Harvard Dataverse: listar archivos del dataset y bajarlos por id. |
| **WDI** (Banco Mundial) | Dotaciones por país: matrícula terciaria y secundaria, crédito privado/PIB, consumo y acceso a electricidad, apertura, población, PIB per cápita PPP, valor agregado manufacturero, usuarios de internet, tierra arable por persona | API `api.worldbank.org/v2/country/all/indicator/{código}` con paginación. |
| **Penn World Table** | Capital humano (`hc`), stock de capital, PIB, población | Excel o Stata de la página del GGDC (Groningen), descarga directa. |
| **LPI** | Índice de desempeño logístico (ediciones bienales irregulares) | Indicador `LP.LPI.OVRL.XQ` por WDI; Excel del portal LPI como respaldo. |
| **Concordancias** | HS↔CPC↔CIIU Rev.4 y entre revisiones HS | Tablas de correspondencia de UNSD y de WITS (CSV), descarga directa. |
| **ILOSTAT** *(opcional)* | Empleo y fuerza laboral por rama (habilidades) | Archivos bulk `.csv.gz` del portal. |
| **Intensidades** y **costo de energía** | Ver D4 | Ver D4 |

- **Si algo no se puede bajar automáticamente** (CEPII o el portal LPI pueden bloquear descargas por script): te digo el nombre exacto del archivo y la carpeta de `data/raw/<fuente>/` donde copiarlo; el README de la carpeta ya lo explica.
- **Verificación**: `data/raw/<fuente>/` completo, `fuentes.csv` con fecha y versión, y una tabla de control con filas y rango de años por fuente.

### 0.4 Borrador de la taxonomía de sectores TAPE **[DECISIÓN D9]**
- **Qué**: proponer ~50 sectores partiendo de CIIU Rev.4 (secciones y divisiones), desagregando más la manufactura y la agroindustria, que es donde está el espacio producto de Paraguay (carne, soja, lácteos, textil, plásticos, autopartes/arneses, biocombustibles, etc.). Los servicios quedan agrupados porque no entran al espacio producto.
- **Produce**: `data/clean/taxonomia_sectores_tape.csv` (`sector_id`, `nombre`, `ciiu_divisiones`, `ciiu_grupos`, `descripcion`, `entra_en_comercio`) y `docs/taxonomia.md` con el criterio de cada corte. Las columnas de grupos agregados (CNAEP 33, MIP 21, crédito 8, EPHC 8, regionales 6) quedan **vacías** hasta que lleguen los clasificadores del BCP, CEPAL-OIT e INE.
- **Verificación**: toda división CIIU de bienes comerciables pertenece exactamente a un sector. Tú apruebas que tenga sentido para Paraguay (condición de paso de la Fase 0).

### 0.5 Tabla puente HS → CIIU Rev.4 → sector TAPE
- **Qué**: construir el puente con las correspondencias oficiales (HS→CPC→CIIU Rev.4). Donde un producto HS cae en varios CIIU, repartir con **pesos por valor exportado mundial** de BACI. Cada fila lleva `nivel_confianza`: alta (correspondencia 1 a 1), media (1 a n con pesos), baja (se resolvió a nivel de 4 dígitos o por asignación manual).
- **Produce**: `src/puentes/hs_ciiu.py`, `data/clean/puente_hs6_ciiu4.parquet`, `data/clean/puente_hs6_sector.parquet`, pruebas en `tests/`.
- **Verificación**: 100% de los HS6 de BACI asignados; tabla con el porcentaje de valor exportado mundial por nivel de confianza; los 30 principales productos de exportación de Paraguay revisados a mano por ti; muestra aleatoria de 30 filas de confianza media/baja.
- **Condición de paso de Fase 0**: taxonomía aprobada + fuentes de Fase 1 descargadas.

---

## Fase 1 — Módulo nacional

### 1.1 Limpieza de BACI
- **Produce**: `src/limpieza/baci.py` → `data/clean/comercio_hs92.parquet` (`pais`, `socio`, `producto`, `anio`, `valor_usd`, `toneladas`); y la vista exportaciones por país-producto-año.
- **Verificación**: totales mundiales por año plausibles, sin valores negativos, códigos ISO3 consistentes con el catálogo; gráfico de exportaciones mundiales 1995–último año; exportaciones de Paraguay por año comparadas con cifras oficiales de referencia.

### 1.2 Depuración del comercio **[DECISIÓN D6]**
- **Qué**: excluir HS 271600 (energía eléctrica; Itaipú/Yacyretá) y **marcar** reexportaciones de Paraguay (y de otros países reexportadores). La columna `reexportacion` queda explícita; nada se borra en silencio.
- **Produce**: `src/limpieza/depuracion.py` → `data/clean/comercio_depurado.parquet`; `docs/supuestos.md` con la regla elegida.
- **Verificación**: tabla antes/después de Paraguay (valor total, top 20 productos) y lista de productos marcados.

### 1.3 RCA y matriz de presencia
- **Produce**: `src/modelos/rca.py` (funciones puras) → `data/model/rca.parquet` (`pais`, `producto`, `anio`, `rca`, `presente`); prueba con ejemplo hecho a mano.
- **Verificación**: correlación con el RCA del Atlas por país-producto-año (esperada >0.99 con la misma clasificación); top 15 de RCA de Paraguay (soja, carne, energía excluida, etc.).

### 1.4 Proximidad y densidad sin fuga **[DECISIÓN D3]**
- **Produce**: `src/modelos/proximidad.py` → `data/model/proximidad_corte{año}.parquet` y `data/model/densidad.parquet`. Para cada año de corte t, φ se estima **solo con datos ≤ t**.
- **Verificación**: prueba automática de que ningún dato posterior a t entra en φ; comparación con la distancia del Atlas; lista de los 10 productos más próximos a "carne bovina" y "soja" para sanidad.

### 1.5 Dotaciones por país (`a_ckt`)
- **Produce**: `src/limpieza/dotaciones.py` → `data/clean/dotaciones.parquet` con las capas capital humano, crédito, energía, logística, estandarizadas por año.
- **Verificación**: cobertura país × año × capa (qué falta y cómo se imputa); posición de Paraguay en cada capa (percentil) con gráfico.
- **Depende de D4** (energía).

### 1.6 Requisitos por producto (`r_pk`) **[DECISIÓN D4]**
- **Produce**: `src/puentes/requisitos.py` → `data/clean/requisitos_producto.parquet` (intensidad energética, de capital, de habilidades y valor/peso, con nivel de confianza del mapeo a HS).
- **Verificación**: ranking de productos más intensivos en cada capa revisado por ti (sentido económico: aluminio intensivo en energía, maquinaria en capital humano, etc.).

### 1.7 Panel de entradas
- **Produce**: `src/modelos/panel.py` → `data/model/panel_entradas.parquet` (país × producto × ventana: `entrada`, `densidad`, `requisitos`, `dotaciones`, interacciones); ventanas 2000→2005→2010→2015→2020, h=5 y h=10 **[DECISIONES D5, D7, D8]**.
- **Verificación**: tasa de entrada por ventana (esperada baja, de pocos puntos porcentuales); prueba de no fuga: ninguna variable usa información posterior a t.

### 1.8 Modelo de referencia: densidad sola
- **Produce**: `src/modelos/evaluacion.py` (precision@k, AUC-PR, calibración) y el logit con solo la densidad. Es el piso contra el que se compara todo.
- **Verificación**: pruebas de cada métrica con casos hechos a mano; curva de calibración y precision@k para k = 10, 20, 50.

### 1.9 Logit con capas y efectos fijos **[DECISIÓN D2]**
- **Produce**: `src/modelos/logit_nacional.py`, `data/model/logit_coeficientes.csv`, `outputs/` con tabla de θ_k y λ_k con errores agrupados por país.
- **Verificación**: signos y magnitudes con sentido económico; tú interpretas los coeficientes (es lo que revisa el equipo en esta fase).

### 1.10 XGBoost de control con SHAP
- **Produce**: `src/modelos/xgb_control.py`, gráficos SHAP. Si supera claramente al logit, hay poder predictivo no capturado.

### 1.11 Backtest y validación
- **Qué**: entrenar hasta 2005 y predecir 2005–2015; países excluidos (comparables a Paraguay); aporte de las capas contra la densidad sola; casos de Paraguay (¿marcaba el modelo arneses de maquila, frigoríficos, biocombustibles antes de su despegue?); robustez (HS4 vs HS6, h=5 vs 10, umbrales de RCA, entrada sostenida).
- **Produce**: `docs/informe_fase1.md` con tablas y gráficos, y la lista de sectores candidatos para Paraguay (producto→sector, **D1**).
- **Condición de paso a Fase 2**: el modelo con capas supera a la densidad sola en precision@k.

---

## Decisiones que necesito que tomes

Mi recomendación va primero en cada una.

| # | Decisión | Opciones | Recomendación |
|---|---|---|---|
| **D1** | Pasar de producto a sector TAPE | (a) estimar por producto y agregar la probabilidad del sector como media ponderada por exportación mundial, con máximo y conteo como respaldo; (b) agregar a sector antes de estimar; (c) usar 1−Π(1−p) | (a) conserva el detalle; (b) pierde resolución |
| **D2** | Efectos fijos y predicción fuera de muestra: los efectos fijos país-año y producto-año no existen para una ventana futura ni para un país excluido | (a) FE de país y de producto constantes más dummies de ventana, y la especificación del documento solo como robustez dentro de muestra; (b) efectos aleatorios correlacionados (Mundlak), que permiten predecir países excluidos; (c) la especificación del documento tal cual, sin predecir fuera de muestra | (a) para el backtest; (b) para países excluidos |
| **D3** | Cómo calcular φ sin fuga | (a) ventana de 5 años que termina en t; (b) todo el período ≤ t acumulado | (a) |
| **D4** | Fuente de intensidades `r_pk` y de costo de energía: ninguna de las fuentes de tu lista las trae | Intensidades: (a) NBER-CES (EE. UU., manufactura, energía/capital/trabajadores calificados) con el puente NAICS→HS del Census; (b) OCDE/EU KLEMS; (c) UNIDO INDSTAT. Energía: precio de electricidad industrial (IEA, de pago) o proxies WDI (consumo y acceso) | Intensidades (a); energía con proxy WDI al inicio, dejando el precio real como mejora. Aviso: el costo de energía es la capa más débil con datos públicos |
| **D5** | Revisión HS y nivel | (a) HS92 a HS4 para estimar y HS6 para robustez y puente a CIIU; (b) HS6 en todo | (a), como en el documento técnico |
| **D6** | Marcar reexportaciones | (a) marcar productos cuyas importaciones y exportaciones de Paraguay son del mismo orden (usando importaciones de BACI) y confirmar luego con la aduana DNIT; (b) lista manual de productos | (a) |
| **D7** | Entradas sostenidas | (a) RCA con promedio móvil de 3 años en t y t+h, y variante exigiendo RCA≥1 en dos de tres años; (b) solo la definición del documento | (a) |
| **D8** | Muestra de países | (a) excluir países con menos de 1 millón de habitantes o exportaciones muy bajas; (b) los ~180 sin filtro | (a), con el filtro reportado en el informe |
| **D9** | Taxonomía de sectores | (a) base CIIU Rev.4 con la manufactura y la agroindustria desagregadas; (b) base subsectores MIC | (a) porque el MIC aún no llegó. Pregunta aparte: tu lista de 5 clasificaciones agregadas puede no anidar; lo verificamos cuando lleguen los clasificadores |
| **D10** | Umbral ε de las reglas de política (se necesita en Fase 3, no ahora) | Fijo (p. ej., 5 puntos de probabilidad) o relativo | Dejar abierto hasta tener ΔP |

## Riesgos de la Fase 1
- **Licencias** de BACI y Atlas para uso comercial: se revisan en 0.2 antes de construir sobre ellas.
- **Costo de energía**: capa débil, ver D4.
- **Tamaño de BACI**: varios GB; trabajamos con parquet y DuckDB para no cargarlo entero en memoria.
- **Historia corta de entradas** de Paraguay para la prueba de casos: se muestra la incertidumbre.

---

## Anexo (2026-10-08): extracciones de fuentes locales previstas para la Fase 2
Hallazgos de la exploración de los sitios; ninguna de estas tareas está hecha todavía.

| # | Tarea | Qué produce | Estado de la fuente |
|---|---|---|---|
| L1 | **Registro de títulos del MEC** | `data/raw/mec_titulos/`; luego conteos por carrera × campo CINE-P × departamento/distrito × año | Hay enlaces de descarga al pie del portal (CSV/XLS/JSON en zip), pero el servidor rechaza a los scripts (403): hay que bajarlo a mano desde el navegador. El diccionario trae 44 campos: incluye `CLASIFICACION_CAMPO_AMPLIO/ESPECIFICO/DETALLADO` (CINE-P 2013) y `DEPARTAMENTO`/`DISTRITO` donde se dicta la carrera, lo que adelanta la equivalencia carrera → sector y la ubicación |
| L2 | **Industrias por ciudad** (mapa MIC, pestaña F) | tabla industria × sector × subsector × ciudad | Se puede leer filtrando por ciudad (263) |
| L3 | **Coordenadas de industrias** (pestaña F) | puntos con sector, para geoprocesar a distrito | A comprobar: el mapa podría devolver solo puntos agrupados |
| L4 | **Capas logísticas** (pestañas B rutas, C red eléctrica, D combustibles, E salud, G polos/IFCLs, H aduanas) | puntos y líneas con coordenadas; demanda proyectada por subestación (MW) | Las coordenadas aparecen en las respuestas del visor; hay que extraer y limpiar cada capa |
| L5 | **Escuelas del MEC** | establecimientos con ubicación | Hay un mapa en `datos.mec.gov.py/app/mapa_establecimientos` (por revisar) |

Pedido formal recomendado en paralelo: acceso a la información al MIC (capas y coordenadas) y al MEC (si el CSV no se puede bajar).
