# Estado del proyecto TAPE

Actualizado: 2026-10-13. Para ponerse al día: leer este archivo, luego `CLAUDE.md` (resumen técnico y reglas), `docs/PLAN_fase0_fase1.md` (plan, decisiones y estado por tarea) y `docs/COLABORACION.md` (cómo trabajar de a dos). Un resumen para repartir el trabajo está en `docs/TAPE_pasos_siguientes.pdf` (y `.docx`).

## Hasta dónde llegamos
**Fase 0 (fundamentos) cerrada. La Fase 1 (módulo nacional) está en marcha.** Hay 129 pruebas automáticas que pasan (`uv run pytest`).

**Decisiones tomadas el 2026-10-12** (detalle en `docs/supuestos.md`): D3 (proximidad con ventana de 5 años que termina en t; la distancia del Atlas solo como control), D4 (intensidades con NBER-CES, puente NAICS → HS de Pierce y Schott, energía con el **precio de la electricidad** de Doing Business) D6 (reexportaciones marcadas por regla automática, a revisar después con la aduana), **D7** (entrada de un solo año como principal y «2 de 3 años» como robustez; el promedio móvil de 3 años se descartó) y **D8** (población ≥ 1 millón y exportaciones ≥ USD 1.000 millones: 112 a 144 países, ≈ 97 % del comercio). Siguen abiertas D1, D2 y D10.

**Tareas de la Fase 1:**
| Tarea | Estado |
|---|---|
| 1.5 Dotaciones por país | **Hecha** (`docs/dotaciones.md`): capital humano, crédito, energía (precio) y logística, 235 países × 1990-2024 |
| 1.6 Requisitos por producto | **Hecha** (`docs/puente_requisitos.md`): energía, capital, habilidades y valor/peso para 1.242 productos HS4 |
| 1.2, 1.3, 1.4, 1.7, 1.8 | **Borradores de Ever en `src/modelos/`**; baseline de densidad sola subido el 2026-10-12 (dentro de la muestra, sin D2). Revisión y cambios pedidos: `docs/NOTA_revision_modelos_Ever.md`. Van a pasar a las versiones livianas `densidad_np.py` y `logit_disperso.py` (ver `docs/optimizacion_modelos.md`) |
| 1.1, 1.9, 1.10, 1.11 | Pendientes (1.9 espera D2; 1.11 espera D1) |

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
**Decisiones abiertas:** D2 (efectos fijos) para el logit; D1 (producto → sector) para el informe; D10 (umbral ε) para la Fase 3. **Pendiente de confirmar:** la presencia que se usa para la proximidad y la densidad (hoy, promedio móvil de 3 años ≥ 1 en algún año de la ventana) y qué hacer con la capa de logística en las ventanas de 2000 y 2005 (el LPI empieza en 2007).

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
| Ever | Modelos de `src/modelos/`: pasar a `densidad_np.py` y `logit_disperso.py`, recalcular el RCA después de depurar, aplicar la depuración a la presencia y la densidad, aplicar D7 y D8 en el panel (entrada de un solo año y variante «2 de 3 años»; filtro de países) y sacar las rutas fijas | — |
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
