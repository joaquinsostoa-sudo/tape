# Revisión del baseline de Ever (2026-10-13)

Revisado: PR #1 (`fase1/baseline-ever`): `depurar.py`, `presencia.py`, `panel.py`, `backtest.py`, `docs/RESULTADO_baseline.md`. No se modificó ningún archivo de `src/modelos/`. Las cifras de `RESULTADO_baseline.md` no se reprodujeron (la base DuckDB es local de Ever).

## Qué está bien
- `MIN_EXPORT = 1_000_000` (miles de USD) equivale a USD 1.000 millones; BACI trae `v` en miles.
- `depurar.py` recalcula el RCA sobre el comercio sin Itaipú y sin reexportaciones.
- `panel.py`: entrada de un solo año (D7) y variante «2 de 3 años» (`panel_robusto_*`).
- `backtest.py` usa `LogitEfectosFijos` y recibe `--db`; ya no hay rutas fijas.

## Cambios que le tocan a Ever (en sus archivos)
1. **Filtro de población (D8) en `panel.py`.** Hoy lee `country, year` de `dotaciones.parquet`, pero las columnas son `iso3, anio`, y `country` de BACI es numérico (Paraguay = 600). Usar los dos archivos nuevos, ya versionados (`git pull`):
   - `data/clean/puente_paises_baci.csv` (`codigo_baci`, `iso3`, `nombre`, `historico`): unir desde el comercio, por `codigo_baci`.
   - `data/clean/poblacion_pais.csv` (`iso3`, `anio`, `poblacion`): no hace falta el parquet ni reconstruir nada.
   Con eso: `comercio.country -> puente.iso3 -> poblacion(iso3, t0)`.
2. **Países sin dato de población:** `p.poblacion IS NULL OR >= 1M` los deja pasar. D8 pide población ≥ 1 millón; sin dato debe quedar fuera (o listarse aparte para revisarlos a mano).
3. **Presencia «2 de 3 años» (`presencia.py`).** `ROWS BETWEEN 2 PRECEDING` cuenta 3 *filas*, no 3 años: `rca_depurado` solo trae años con exportación positiva, así que la ventana puede abarcar más años. Usar años de calendario (`RANGE BETWEEN 2 PRECEDING` sobre `year`, o completar los años faltantes con RCA = 0). Además `anios_disponibles` no se usa.
4. **Fuera de muestra (D2).** El logit se ajusta y se mide con las mismas filas (con efectos fijos de país y producto). Para la comparación con la literatura hay que entrenar hasta t−h y predecir la ventana siguiente. Hasta entonces, las cifras de `RESULTADO_baseline.md` son *dentro de la muestra* y no se comparan con Bahar et al.
5. **Verificar el panel (urgente).** La entrada se define con RCA_t < 0,5, que incluye RCA = 0. Si `rca_depurado` solo trae pares con exportación positiva, el panel excluye los productos que el país no exportaba. Contar cuántos pares con RCA = 0 hay en `panel_*` y cuántos pares país-producto pierde el filtro `densidad IS NOT NULL` (≈ 15 %), y si esa pérdida depende de E.
6. **Reexportaciones:** hoy se *borran* del RCA y solo se marcan para Paraguay. La regla 3 pide una columna explícita; conservar `es_reexportacion` en `baci_depurado`.
7. **Estilo:** `uv run ruff check --fix src/modelos` corrige 13 de las 15 faltas (imports, f-strings sin variables).

## Nota
La ventana de densidad termina en t−1 (para t0 = 2015 usa 2010-2014). No hay fuga; es más conservador que D3 (termina en t). Anotado en `docs/supuestos.md`.
