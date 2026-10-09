# Estado del proyecto TAPE

Actualizado: 2026-10-09. Para ponerse al día: leer este archivo, luego `CLAUDE.md` (resumen técnico y reglas), `docs/PLAN_fase0_fase1.md` (plan y decisiones abiertas) y `docs/COLABORACION.md` (cómo trabajar de a dos). Un resumen para repartir el trabajo está en `docs/TAPE_pasos_siguientes.pdf` (y `.docx`).

## Hasta dónde llegamos
**Fase 0 (fundamentos) cerrada. La Fase 1 (módulo nacional) no empezó.** Hay 95 pruebas automáticas que pasan (`uv run pytest`).

**Fuentes internacionales descargadas** (`uv run python -m src.descargas.todas`): BACI (HS92, 1995-2024), Atlas de Complejidad, WDI (13 indicadores), Penn World Table 10.01 (a mano), LPI, correspondencias de la ONU y WITS, límites administrativos de geoBoundaries y 10 tablas de SIMEL. Ver `docs/verificacion_fuentes.md`.

**Taxonomía y puentes:** 67 sectores TAPE sobre CIIU Rev.4 (`docs/taxonomia.md`); puente HS92 → CPC → CIIU → sector con confianza por fila (`docs/puente_hs_sector.md`: 86 % del valor exportado mundial con confianza alta, 99,4 % de coincidencia con WITS); tabla CNAEP → sector y subsectores MIC → sector.

**Datos nacionales ya incorporados** (a mano, en `TAPE_datos_manuales.zip`; detalle en `docs/COLABORACION.md` y en el README de cada carpeta `data/raw/<fuente>/`):
- **BCP:** PIB por 33 actividades (1991-2024) y regional por 6 ramas y 18 departamentos (2021-2024); crédito por 13 sectores y banco (mensual 2020-2026/08); cuentas nacionales base 2014.
- **MIP:** simulador con la matriz de 21 sectores (autoría y año por confirmar).
- **INE:** EPHC anual 2022-2025 (rama de actividad en 8 categorías, sin CIIU más fino).
- **MAG:** Censo Agropecuario 2022: Volumen I (78 cuadros por departamento) y fincas y superficie por distrito (259 distritos; los totales cuadran con el Volumen I).
- **MTESS (SIMEL):** establecimientos y puestos inscritos (por actividad y por departamento, pero no el cruce), formación SINAFOCAL/SNPP e informalidad por departamento.
- **Educación:** carreras y programas de la ANEAES con la marca acreditada o no (792); establecimientos 2012 e instituciones 2018 del MEC (incompletos).
- **Mapa logístico del MIC** (visor sin licencia declarada; provisorio): 263 distritos con población del Censo 2022, PEA y distancias; 17.080 industrias por distrito y sector; red eléctrica (104 subestaciones, potencia disponible y líneas); 22 rutas nacionales y fronteras; 6.987 puntos de AFI y 53 centros del SNPP; comercio por aduana (sin año declarado); 212 establecimientos de salud. La capa de combustibles no se extrajo.
- **Maquila:** informe agregado de agosto 2026.

## Qué falta
**Fase 1 (módulo nacional):** decidir D1 a D4 y D6 a D8 (`docs/PLAN_fase0_fase1.md`) y hacer las tareas 1.1 a 1.11: limpieza de BACI, depuración (energía de Itaipú y Yacyretá, reexportaciones), RCA, proximidad y densidad sin fuga de información, dotaciones y requisitos por producto (intensidades y costo de energía: D4), panel de entradas, logit con efectos fijos, XGBoost de control y backtest. Los países y productos de todo el mundo son necesarios: Paraguay es solo el caso al que se aplica.

**Datos nacionales por conseguir:**
- Registro de títulos y Registro Nacional de Carreras del MEC (descarga manual; el sitio rechaza scripts).
- Pedidos formales: Censo Económico 2011 por distrito (INE), régimen de materia prima (MIC) y cuadros de oferta y utilización detallados (BCP).
- Comercio exterior de Paraguay por NCM (aduana o BCP): opcional, BACI ya trae a Paraguay.
- Cultivos y ganadería del censo agropecuario por distrito, si existe otro tomo.
- Informes de maquila y de la Ley de Inversiones: última capa, complementos.
- Leyes y normas (BACN y Gaceta), ILOSTAT, licencias de SIMEL y del visor del MIC.

**Trabajo de datos pendiente:** reconciliar los 247 distritos de los límites de 2012 con los 263 del Censo 2022 (industrias, subestaciones y rutas usan los viejos; población y censo agropecuario, los nuevos); definir carrera → CINE-F → sector cuando lleguen los títulos.

## Quién hace qué
| Persona | Tarea en curso | Rama |
|---|---|---|
| Joaquín | Datos nacionales pendientes; decisiones D4, D6 y D3 con Claude Code | — |
| (socio) | Por acordar. Propuesta: 1.1 limpieza de BACI, 1.3 RCA y 1.8 métricas de evaluación | — |

Las tareas 1.1, 1.3 y 1.8 son código sin decisiones abiertas. Una tarea por rama (`fase1/1-1-limpieza-baci`), con pruebas y lint en verde antes de cada commit.

## Cómo reproducir todo
```bash
uv sync
uv run python -m src.descargas.todas     # fuentes automáticas (≈ 4 GB)
# descomprimir TAPE_datos_manuales.zip (Drive) en la raíz del repositorio
uv run python -m src.reconstruir_todo    # tablas limpias, puentes y taxonomía
uv run pytest
```
Para regenerar el zip: `uv run python -m src.empaquetar_datos_manuales`.
