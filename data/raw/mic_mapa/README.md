# Mapa Logístico MIC (capas)

Registro: fila `mic_mapa` de `data/fuentes.csv`. El visor es un panel de Zoho Analytics (https://mapaprodpy.mic.gov.py/) sin botón de descarga.

## Qué hay aquí
- `industrias_sector_subsector_2026-10-08.csv`: resumen sector > subsector de la pestaña **F- INDUSTRIAS** (tabla F4), leído del visor el 2026-10-08: 73 pares, 17.080 industrias en total (coincide con los totales por zona). Incluye el número de "sectores específicos" distintos por subsector.
- Los **1.744 sectores específicos** (texto libre del tercer nivel) se pueden volver a leer del visor; no están guardados todavía.

## Qué falta
Las demás pestañas (A zonas y ciudades, B rutas, C red eléctrica, D combustibles, E salud, G polos, H aduanas, I comercio global) y las **coordenadas de las industrias**, necesarias para el geoprocesamiento de la Fase 2. Si el MIC las entrega por solicitud de acceso a la información, guardarlas en subcarpetas por capa.

## Hallazgos sobre la extracción (2026-10-08)
- El visor entrega **coordenadas** en las respuestas de sus gráficos de mapa (campos `Latitud_1` y `Longitud_1`). En la pestaña **C- RED ELECTRICA** se vieron: subestaciones con tensión (kV), tablas de demanda proyectada por subestación y año (MW) y las líneas (≈ 776 KB de vértices).
- **Prueba hecha (2026-10-08): el mapa de F- INDUSTRIAS devuelve las 17.080 industrias, una por una, con coordenadas.** La respuesta del gráfico (`ZAChartView`, tipo `MAPSCATTER`, ≈ 2,9 MB) trae 19 series (una por sector) y cada punto es `[latitud, 1, SECTOR, SUB-SECTOR, SECTOR ESPECÍFICO, longitud, índice]`. El conteo por sector coincide con el visor (p. ej. madera y muebles 3.976). **No trae ciudad ni departamento por punto**: la ciudad se obtiene cruzando las coordenadas con los límites administrativos (carpeta `limites_admin`). No trae nombre ni identificador de la empresa.
- Falta guardar esos puntos a disco: el navegador integrado bloquea el envío directo a un receptor local, así que hay que generar un archivo descargable desde la página (con permiso del usuario).
- Las otras capas (rutas, red eléctrica, combustibles, salud, polos, aduanas) usan el mismo tipo de gráfico y también devuelven coordenadas.
- Los filtros Zona / Departamento / Ciudad permitirían leer la tabla F4 por ciudad (263), pero con las coordenadas ya no hace falta.
- El visor no declara licencia ni ofrece descarga. La extracción es provisoria: **pedir los datos al MIC por acceso a la información** sigue siendo la vía formal, igual que la copia anual del mapa para construir un panel propio.

## Capa A: zonas y ciudades (extraída 2026-10-09)
- `capaA_ciudades_censo2022_2026-10-09.csv`: tabla A3 del visor, 263 ciudades con zona (4), departamento, **población del Censo 2022** y distancias por carretera en km a Asunción, Ciudad del Este, Encarnación y al puerto de Central. Totales verificados contra el visor: 6.109.903 habitantes y los 18 totales departamentales del gráfico A2.
- `capaA_ciudades_mapa_2026-10-09.csv`: mapa A1, mismas ciudades con **latitud y longitud** (un punto por ciudad), hombres, mujeres, **PEA** (3.331.360 en total) y **edad mediana**.
- Cómo se leyó: la tabla A3 carga solo 200 de las 263 filas, así que se recorrió el filtro de zona (Centro 58, Este 78, Norte y Chaco 60, Sur 67) interceptando la respuesta de cada consulta. El mapa se leyó de la respuesta del gráfico `MAPBUBBLE`.
- Las 263 ciudades coinciden con los 263 distritos del Censo 2022. Ojo: los límites administrativos que usamos para asignar industrias (DGEEC 2012) tienen 247 distritos; al unir ambas fuentes hay distritos nuevos que reconciliar.
- Limpieza y unión: `src/limpieza/mic_ciudades.py` -> `data/clean/ciudades_mic.csv`. Dos nombres difieren entre tabla y mapa (BELLA VISTA NORTE / BELLA VISTA en Amambay, ÑUMI / NUMI). **María Antonia (Paraguarí) viene con coordenadas 0,0 en el visor**: queda sin ubicación.
- Las otras pestañas (B rutas, C red eléctrica, D combustibles, E salud, G polos, H aduanas, I comercio global) siguen pendientes.

## Capa C: red eléctrica (extraída 2026-10-09)
- `red_electrica_mic_2026-10-09.json` (0,9 MB): generado por la página con el navegador (descarga autorizada por el usuario para las capas del MIC). Contiene:
  - **104 subestaciones y generadoras** (mapa C3): coordenadas, tensión (23, 66, 220 y 500 kV), estado (todas OPERATIVA), potencia disponible 2026.
  - **Potencia disponible proyectada por subestación** (tablas C4 y C5): 23 kV en 2026-2029 y 2031-2033; 220/66 kV en 2025-2028 y 2030-2033. Los años no son consecutivos (23 kV omite 2030 y 220/66 kV omite 2029). Los cuatro primeros años de cada tabla coinciden con los gráficos C7 y C8; los siguientes se deducen del orden de los encabezados (por confirmar).
  - **Trazado de las líneas**: 3.823 vértices en cuatro tipos (línea de transmisión, troncal de 500 kV, corredor de 220 kV, central hidroeléctrica) con tensión, nombre del corredor, zona y departamento.
- La subestación `SE023kV_LUQUE` no tiene valores en la tabla 220/66 kV (se guarda como dato faltante). `Yacyretá` cae sobre el río, entre Misiones e Itapúa.
- Alto Paraguay no tiene subestaciones de 23 kV en el visor.
- Limpieza: `src/limpieza/mic_red_electrica.py` -> `data/clean/mic_subestaciones.csv`, `mic_potencia_disponible.csv` (formato largo) y `mic_lineas_vertices.parquet`; asignación a distrito en `src/puentes/subestaciones_distrito.py` -> `mic_subestaciones_localizadas.csv` (las 104 caen dentro de un distrito de los límites de 2012).
