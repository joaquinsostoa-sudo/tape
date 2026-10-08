# Mapa Logístico MIC (capas)

Registro: fila `mic_mapa` de `data/fuentes.csv`. El visor es un panel de Zoho Analytics (https://mapaprodpy.mic.gov.py/) sin botón de descarga.

## Qué hay aquí
- `industrias_sector_subsector_2026-10-08.csv`: resumen sector > subsector de la pestaña **F- INDUSTRIAS** (tabla F4), leído del visor el 2026-10-08: 73 pares, 17.080 industrias en total (coincide con los totales por zona). Incluye el número de "sectores específicos" distintos por subsector.
- Los **1.744 sectores específicos** (texto libre del tercer nivel) se pueden volver a leer del visor; no están guardados todavía.

## Qué falta
Las demás pestañas (A zonas y ciudades, B rutas, C red eléctrica, D combustibles, E salud, G polos, H aduanas, I comercio global) y las **coordenadas de las industrias**, necesarias para el geoprocesamiento de la Fase 2. El visor muestra el mapa pero no se pudo comprobar si expone coordenadas. Si el MIC las entrega por solicitud de acceso a la información, guardarlas en subcarpetas por capa (ver `data/raw/mic_mapa` en el plan).
