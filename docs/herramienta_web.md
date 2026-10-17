# Herramienta web del diagnóstico multi-capa (D38)

Fecha: 2026-10-17. Código: `src/herramienta/exportar_diagnostico.py` (datos) y `web/tapeapp/` (app React + Vite, que parte de la de Ever). Decisiones: D38 en `docs/supuestos.md`.

## Cómo se usa
Primero se generan los datos, después se abre la app:
```bash
uv run python -m src.herramienta.exportar_diagnostico
npm --prefix web/tapeapp install
npm --prefix web/tapeapp run dev
```
Hace falta Node.js (se instaló la versión LTS con `winget install OpenJS.NodeJS.LTS`). El exportador escribe `web/tapeapp/src/data/diagnostico.json` (0,9 MB) y `distritos_geo.json` (0,6 MB); ambos se versionan, como los datos de Ever.

## Qué muestra
- **Por actividad:** lista de actividades con filtros (complejidad del producto en tercios, complejidad frente a lo que Paraguay ya produce, y cuántos distritos la producen). Al elegir una, el mapa pinta los 263 distritos en cinco clases ordenadas: cumple todo, cerca del umbral, una brecha, dos o más brechas y límite duro de recursos; además datos incompletos y sin referencia. Un borde naranja marca los distritos que ya la producen. A la derecha: las capas que exige, el estándar y los distritos más compatibles.
- **Por territorio:** selector de indicador (cada capa, actividades compatibles o actividades que ya produce), mapa de departamentos (mediana de sus distritos) y, al elegir uno, sus distritos.
- **Ficha de distrito:** capas, actividades que ya produce, actividades que podría desarrollar (con filtro de complejidad) y las que le faltan, con la capa limitante y quién actúa. Con una actividad elegida, la ficha muestra primero cómo está el distrito frente a esa actividad.
- **Ficha de departamento:** agregado de sus distritos (capas, actividades más producidas y más compatibles, lista de distritos). Los datos entran a nivel distrito; no se inventan datos departamentales.

## Reglas de lectura (en la propia herramienta)
Es una descripción de distancias frente a quienes ya producen, no una predicción ni una probabilidad (D16, D34). Se muestran la confianza de la referencia, el aviso de que una actividad con una sola capa exigida aparece viable casi en todos lados, y que el mapa MIC solo cubre industrias.

## Límites y pendientes
- **Sin agro ni servicios:** 23 sectores quedan «sin referencia» (menos de 5 productores en el MIC) y se listan atenuados.
- **17 distritos sin polígono propio** (creados después de 2012) se dibujan como puntos; María Antonia no tiene coordenadas y solo aparece en las listas.
- **Nombres:** los 67 sectores están en español. Los nombres de productos HS4 del Atlas están en inglés y la herramienta todavía no los muestra; si se muestran hay que traducirlos (pendiente: tabla HS4 en español). Los nombres de distritos salen sin tildes (así vienen de las fuentes).
- **La formación específica no se guarda por distrito**: la ficha solo muestra su estado.
- La app anterior de Ever (`departamentos.json`, `ParaguayMap.jsx`) queda en el repositorio sin uso; sus datos eran de ejemplo (con probabilidades inventadas).
- El orden de las clases y los umbrales dependen mucho del estándar (con la mediana de todos los distritos cambia cerca de la mitad de las celdas evaluadas; `docs/diagnostico_multicapa.md`).
