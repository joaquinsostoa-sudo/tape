# Limpieza de BACI (tarea 1.1)

Código: `src/limpieza/baci.py` (`uv run python -m src.limpieza.baci`, unos 5 minutos). Entrada: `data/raw/baci/BACI_HS92_V202601.zip` (CEPII, descargado el 2026-10-08, sha256 en `MANIFEST.json`). Salidas en `data/clean/` (no versionadas): `comercio_exportaciones_hs6.parquet` (14,9 millones de filas) y `comercio_importaciones_hs6.parquet` (23,4 millones), por país, producto HS6 y año 1995-2024; y la tabla de los modelos `data/model/exportaciones_hs4.parquet` (año, ISO3, HS4, miles de USD).

## Qué hace
Cada CSV anual (≈ 360 MB, una fila por exportador-importador-producto) se extrae a una carpeta temporal, se agrega con DuckDB y se borra, de modo que nunca hay más de uno en disco. Repone el cero inicial del código HS6 (BACI lo pierde) y suma las toneladas tratando «NA» como vacío. **No excluye nada**: la energía (HS 2716) y las reexportaciones se tratan en la depuración (tarea 1.2). Las importaciones por país y producto quedan guardadas para marcar reexportaciones (D6).

## Verificación
- Sin valores negativos; sin claves duplicadas; todo HS6 de 6 dígitos; todo país exportador e importador en el catálogo de BACI.
- Los totales exportados e importados de cada año coinciden (BACI está conciliado): 0 años con diferencias.
- **Control contra el panel anterior:** la tabla HS4 reconstruida desde el zip coincide con la que se venía usando (que venía de la base de Ever): las mismas 4.976.887 filas, ninguna clave solo en una de las dos y una diferencia relativa máxima de 1,5 × 10⁻¹⁵. Los resultados anteriores se pueden reproducir desde el archivo de CEPII, sin depender de la base de Ever.
- Mundo: de USD 5,1 billones (1995) a 22,8 billones (2024). Paraguay (millones de USD, de ellos energía HS 2716): 2000: 2.420 (1.300); 2010: 6.700 (1.930); 2019: 8.370 (1.840); 2024: 11.460 (1.180).

## Pendiente de verificación
La tarea pide comparar las exportaciones de Paraguay con cifras oficiales. **Falta una referencia oficial anual**: conviene el total de exportaciones registradas del BCP (balanza de pagos) o de la DNA, por año, en `data/raw/` (por ejemplo `bcp_balanza/`), con su fila en `data/fuentes.csv`. La diferencia esperada con BACI es de método (BACI usa valor CIF de las importaciones del socio conciliado, reasigna y limpia).

## Cambios en el código
- `logit_nacional.py` ya no extrae las exportaciones de la base de Ever (`--db` y `extraer_exportaciones` se eliminaron): si falta `data/model/exportaciones_hs4.parquet` indica correr `src.limpieza.baci`.
- `src/reconstruir_todo.py` incluye el paso de BACI y los pasos nuevos del censo, los distritos y las actividades específicas del MIC.
