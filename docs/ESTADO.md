# Estado del proyecto TAPE

Actualizado: 2026-10-13. Para ponerse al día: leer este archivo, luego `CLAUDE.md` (resumen técnico y reglas), `docs/PLAN_fase0_fase1.md` (plan, decisiones y estado por tarea) y `docs/COLABORACION.md` (cómo trabajar de a dos). Un resumen para repartir el trabajo está en `docs/TAPE_pasos_siguientes.pdf` (y `.docx`).

## Hasta dónde llegamos
**Fase 0 (fundamentos) cerrada. La Fase 1 (módulo nacional) está en marcha.** Hay 132 pruebas automáticas que pasan (`uv run pytest`).

**Decisión D2 (2026-10-13):** coeficientes con la especificación del documento (efectos país-año y producto-año, errores agrupados por país); backtest con efectos de país y producto constantes más indicador de ventana, prediciendo la ventana siguiente; Mundlak solo para países excluidos y Paraguay. Los errores estándar agrupados ya están en `logit_disperso.py` (`errores_agrupados`); falta repetir el baseline fuera de muestra.

**Decisión D14 (2026-10-13):** la primera edición del LPI (2007) se arrastra hacia atrás para tener logística en 2000 y 2005 (marca `lpi_hacia_atras`); robustez con las ventanas de datos reales.

**Decisión D13 (2026-10-13):** presencia para φ y densidad = RCA ≥ 1 en 2 de los 3 años de calendario que terminan en t.

**Decisiones tomadas el 2026-10-12** (detalle en `docs/supuestos.md`): D3 (proximidad con ventana de 5 años que termina en t; la distancia del Atlas solo como control), D4 (intensidades con NBER-CES, puente NAICS → HS de Pierce y Schott, energía con el **precio de la electricidad** de Doing Business) D6 (reexportaciones marcadas por regla automática, a revisar después con la aduana), **D7** (entrada de un solo año como principal y «2 de 3 años» como robustez; el promedio móvil de 3 años se descartó) y **D8** (población ≥ 1 millón y exportaciones ≥ USD 1.000 millones: 112 a 144 países, ≈ 97 % del comercio). Siguen abiertas D1, D2 y D10.

**Tareas de la Fase 1:**
| Tarea | Estado |
|---|---|
| 1.5 Dotaciones por país | **Hecha** (`docs/dotaciones.md`): capital humano, crédito, energía (precio) y logística, 235 países × 1990-2024 |
| 1.6 Requisitos por producto | **Hecha** (`docs/puente_requisitos.md`): energía, capital, habilidades y valor/peso para 1.242 productos HS4 |
| 1.2, 1.3, 1.4, 1.7, 1.8 | **Borradores de Ever en `src/modelos/`**; baseline de densidad sola subido el 2026-10-12 (dentro de la muestra, sin D2). Revisión y cambios pedidos: `docs/NOTA_revision_modelos_Ever.md`. Van a pasar a las versiones livianas `densidad_np.py` y `logit_disperso.py` (ver `docs/optimizacion_modelos.md`) |
| 1.9 Logit con capas | **Primera versión provisoria** (`src/modelos/logit_nacional.py`, `docs/resultado_logit_provisorio.md`): la densidad predice las entradas; capital humano es significativo pero pierde fuerza al controlar por PIB per cápita (no se separa del desarrollo general); energía y crédito no se distinguen de cero; logística sale con signo contrario al esperado, no se explica por desarrollo y no es robusta (depende de D14); se decide con el backtest. Capa nueva `capital_fisico` (PWT): no aporta señal propia pero amplía la muestra (97 países en 2000 contra 59); D15 decidida (capital físico en lugar del crédito; el crédito queda como robustez) |
| 1.11 Backtest | **Primera versión** (`src/modelos/backtest_nacional.py`, `docs/resultado_backtest.md`): fuera de muestra, **el modelo con capas no supera a la densidad sola** (diferencias de ±0,004 en precision@20 por país, intervalos que incluyen el cero); la condición de paso a la Fase 2 no se cumple todavía. Controles hechos (`docs/resultado_backtest.md`): **XGBoost con SHAP (1.10) y la variante sin efectos fijos tipo Mundlak no cambian la conclusión**: las capas no mejoran la predicción; las interacciones r·a no aportan. **Paso 3 del plan (entrada por sector TAPE, `backtest_sector.py`, declarado antes de correrlo): criterio no cumplido; dirección positiva en 2 de 3 ventanas (+0,011 y +0,009 en precision@5) con el intervalo tocando el cero y solo 67 a 96 entradas por ventana: indicio débil.** **Requisito revelado probado (paso 2 del plan, `backtest_revelado.py`): tampoco supera a la densidad sola** (criterio declarado no cumplido en 6 de 6 combinaciones), ni con efectos fijos ni sin ellos (`backtest_revelado_mundlak.py`, declarado antes de correrlo). **Robustez de la definición de la entrada hecha** (h = 10, 2 de 3 años y tres umbrales de RCA): el resultado no cambia. Falta: casos de Paraguay, países excluidos, HS6 y D1 para el informe |
| 1.1, 1.10 | Pendientes |

**Fuentes internacionales descargadas** (`uv run python -m src.descargas.todas`): BACI (HS92, 1995-2024), Atlas de Complejidad, WDI (15 indicadores, incluidos el precio de la electricidad y la proporción hidroeléctrica), Penn World Table 10.01 (a mano), LPI, correspondencias de la ONU y WITS, límites administrativos, 10 tablas de SIMEL, **NBER-CES** (intensidades por industria de EE. UU.) y la **concordancia HS → NAICS** de Pierce y Schott. Ver `docs/verificacion_fuentes.md`.

**Taxonomía y puentes:** 67 sectores TAPE sobre CIIU Rev.4 (`docs/taxonomia.md`); puente HS92 → CPC → CIIU → sector con confianza por fila (`docs/puente_hs_sector.md`); tabla CNAEP → sector y subsectores MIC → sector; puente de requisitos por producto.

**Datos nacionales ya incorporados** (a mano, en `TAPE_datos_manuales.zip`; detalle en `docs/COLABORACION.md` y en el README de cada carpeta `data/raw/<fuente>/`):
- **BCP:** PIB por 33 actividades (1991-2024) y regional por 6 ramas y 18 departamentos (2021-2024); crédito por 13 sectores y banco (mensual 2020-2026/08); cuentas nacionales base 2014.
- **MIP:** simulador con la matriz de 21 sectores (autoría y año por confirmar).
- **INE:** EPHC anual 2022-2025 (rama de actividad en 8 categorías, sin CIIU más fino).
- **MAG:** Censo Agropecuario 2022: Volumen I (78 cuadros por departamento) y fincas y superficie por distrito (259 distritos; los totales cuadran con el Volumen I).
- **MTESS (SIMEL):** establecimientos y puestos inscritos (por actividad y por departamento, pero no el cruce), formación SINAFOCAL/SNPP e informalidad por departamento.
- **Educación:** carreras y programas de la ANEAES con la marca acreditada o no (792); establecimientos 2012 e instituciones 2018 del MEC (incompletos).
- **Mapa logístico del MIC** (visor sin licencia declarada; provisorio): 263 distritos con población del Censo 2022, PEA y distancias; 17.080 industrias por distrito y sector; red eléctrica; 22 rutas nacionales y fronteras; AFI y centros del SNPP; comercio por aduana (sin año declarado); 212 establecimientos de salud. La capa de combustibles no se extrajo.
- **Maquila:** informe agregado de agosto 2026.

## Qué falta
**Decisiones abiertas:** D1 (producto → sector) para el informe; D10 (umbral ε) para la Fase 3.

**Hallazgos a resolver en la Fase 1:**
- **Las capas de dotaciones están correlacionadas:** capital humano, crédito y logística entre sí (0,65 a 0,76); la energía (precio) es independiente. Decidir en la tarea 1.9 cómo tratarlo (capa por capa, control por PIB per cápita o componentes).
- **Agricultura, minería y servicios no tienen requisitos** (NBER-CES es solo manufactura; 13 % del valor mundial, incluida la soja): decidir cómo tratarlos en el modelo (tarea 1.7) y en el módulo territorial (Fase 2).
- **Código de `src/modelos/`** (ver `docs/optimizacion_modelos.md`): `depurar.py` quita la energía y las reexportaciones pero no recalcula el RCA, y la depuración no llega a la densidad; las constantes de D8 de `panel.py` no se aplican (y D7 fija la entrada de un solo año como definición principal); hay rutas fijas de Windows (`C:\ever\...`) y dos copias de la base DuckDB.
- **Precio de la electricidad:** solo existe para 2014-2019 y se aplica a todos los años; en la robustez, repetir el modelo con las ventanas desde 2015.

**Datos nacionales por conseguir:**
- Registro de títulos del MEC: **solicitud formal enviada el 2026-10-12** (títulos expedidos agregados por año, carrera, institución, nivel, campo CINE, departamento y distrito, sin datos personales). **El MEC tiene plazo hasta el 2026-11-02 para responder.** Al llegar: guardar en `data/raw/mec_titulos/`, anotar en `data/fuentes.csv` y regenerar el zip.
- Registro Nacional de Carreras del MEC (descarga manual; el sitio rechaza scripts; no se incluyó en la solicitud).
- Pedidos formales: Censo Económico 2011 por distrito (INE), régimen de materia prima (MIC) y cuadros de oferta y utilización detallados (BCP).
- Comercio exterior de Paraguay por NCM (aduana o BCP): opcional, BACI ya trae a Paraguay.
- Cultivos y ganadería del censo agropecuario por distrito, si existe otro tomo.
- Informes de maquila y de la Ley de Inversiones: última capa, complementos.
- Leyes y normas (BACN y Gaceta), ILOSTAT, licencias de SIMEL, del visor del MIC y de BACI/Atlas.

**Trabajo de datos pendiente:** reconciliar los 247 distritos de los límites de 2012 con los 263 del Censo 2022; definir carrera → CINE-F → sector cuando lleguen los títulos.

## Quién hace qué
| Persona | Tarea en curso | Rama |
|---|---|---|
| Joaquín | Datos nacionales pendientes | — |
| Ever | Modelos de `src/modelos/`: pasar a `densidad_np.py` y `logit_disperso.py`, recalcular el RCA después de depurar, aplicar la depuración a la presencia y la densidad, aplicar D7 y D8 en el panel (entrada de un solo año y variante «2 de 3 años»; filtro de países), contar la presencia D13 en años de calendario y sacar las rutas fijas | — |
| Claude Code | Hechas: 1.5, 1.6 y las versiones livianas. Siguiente: revisar los borradores de Ever contra D3, D5 y D6 cuando él los suba | — |

Una tarea por rama (`fase1/1-1-limpieza-baci`), con pruebas y lint en verde antes de cada commit. Los archivos de `src/modelos/` existentes los modifica solo quien trabaja ese módulo.

## Cómo reproducir todo
```bash
uv sync
uv run python -m src.descargas.todas     # fuentes automáticas (≈ 4 GB)
# descomprimir TAPE_datos_manuales.zip (Drive) en la raíz del repositorio
uv run python -m src.reconstruir_todo    # tablas limpias, puentes, requisitos y dotaciones
uv run pytest
```
Para regenerar el zip: `uv run python -m src.empaquetar_datos_manuales`.
