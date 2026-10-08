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
