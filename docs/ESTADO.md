# Estado del proyecto TAPE

Actualizado: 2026-10-08. Para ponerse al día: leer este archivo, luego `CLAUDE.md` (resumen técnico y reglas), `docs/PLAN_fase0_fase1.md` (plan y decisiones abiertas) y `docs/COLABORACION.md` (cómo trabajar de a dos).

## Hasta dónde llegamos
**Fase 0 (fundamentos) cerrada.** Está hecho:
- Estructura del repositorio, entorno `uv`, registro de fuentes (`data/fuentes.csv`), 48 pruebas automáticas.
- **Fuentes internacionales de la Fase 1 descargadas:** BACI (HS92, 1995-2024), Atlas de Complejidad, WDI (13 indicadores), Penn World Table 10.01, LPI, correspondencias de la ONU y WITS (`docs/verificacion_fuentes.md`).
- **Taxonomía de 67 sectores TAPE** sobre CIIU Rev.4 (`docs/taxonomia.md`). Cada sector hereda un solo grupo de las clasificaciones locales (EPHC, crédito, cuentas regionales, MIP, 33 actividades del BCP).
- **Puente HS92 → CPC → CIIU → sector** con confianza por fila (`docs/puente_hs_sector.md`): 86 % del valor exportado mundial con confianza alta; 99,4 % de coincidencia con WITS.
- **Datos del BCP:** PIB por 33 actividades (1991-2024) y PIB regional por 6 ramas y 18 departamentos (2021-2024), más la tabla CNAEP ↔ CIIU con puente a sectores.
- **Mapa logístico MIC, capa de industrias:** 17.080 industrias con coordenadas, asignadas a distrito y departamento (los totales por zona del visor se reproducen exactamente) y repartidas por sector TAPE. Es una extracción provisoria de un visor sin licencia declarada.

## Qué falta
**Para la Fase 1 (módulo nacional):** decidir D1 a D4 y D6 a D8 (`docs/PLAN_fase0_fase1.md`), conseguir las intensidades por producto y el costo de energía (D4) y luego tareas 1.1 a 1.11: limpieza de BACI, depuración (energía de Itaipú/Yacyretá, reexportaciones), RCA, proximidad y densidad sin fuga de información, dotaciones, panel de entradas, logit con efectos fijos, XGBoost de control y backtest.

**Bases nacionales aún sin conseguir** (en verificación; ver `docs/verificacion_fuentes_nacionales.md` cuando exista): comercio exterior DNIT/BCP, maquila y 60/90 a nivel de proyecto, régimen de materia prima, EPHC, crédito por actividad, matriz insumo-producto, Censo Económico 2011, SIMEL, escuelas y títulos del MEC, las otras capas del mapa MIC (rutas, red eléctrica, combustibles, salud, polos, aduanas), leyes.

## Quién hace qué
| Persona | Tarea en curso | Rama |
|---|---|---|
| Joaquín | Conseguir las bases nacionales (ver \docs/verificacion_fuentes_nacionales.md\) | — |
| (socio) | por asignar | — |

Tareas sugeridas para repartir sin pisarse: (a) 1.1 limpieza de BACI y 1.2 depuración (código puro, sin decisiones abiertas); (b) conseguir los archivos nacionales de la lista de arriba; (c) revisar los mapeos de confianza media y baja (`docs/taxonomia.md`, `data/clean/puente_*.csv`).

## Cómo reproducir todo
```bash
uv sync
uv run python -m src.descargas.todas     # fuentes automáticas
uv run python -m src.reconstruir_todo    # tablas limpias, puentes y taxonomía
uv run pytest
```
