# Optimización de `src/modelos/` (2026-10-12)

Motivo: al correr el modelo, el disco de la PC de Ever perdió unos 60 GB. Este documento dice dónde se genera ese volumen, qué versiones livianas hay y cómo pasarse a ellas. **No se modificó ningún archivo de `src/modelos/` que ya existía**: las versiones nuevas son archivos aparte y cada cambio lo decide quien trabaja ese módulo.

## Dónde estaba el problema (medido con datos reales, ventana 2015-2019)
| Paso | Qué hace | Tamaño |
|---|---|---|
| `densidad.py`, `calcular_densidad` | une cada par país-producto (530.810) con todos sus vecinos de la tabla de proximidad (≈ 3.000 por producto) y **recién después suma** | **1.614 millones de filas intermedias** (≈ 39 GB si se materializan), por ventana; son 6 ventanas |
| `densidad.py`, `calcular_phi` | autounión de la presencia por país | 73 millones de filas por ventana (agrupa a 6,7 millones de pares): pesado pero manejable |
| `backtest.py`, `smf.logit("E ~ densidad_z + C(country) + C(product)")` | statsmodels arma una matriz **densa** de filas × ~5.000 dummies | **14 a 16 GB por ventana** (float64), más las copias que hace al ajustar: puede obligar a Windows a crecer el archivo de paginación decenas de GB |

Con `memory_limit='4GB'`, DuckDB manda lo que no entra a `duckdb_temp`: ahí se van decenas de GB, y si el proceso se interrumpe esos archivos temporales pueden quedar en el disco.

## Versiones livianas
| Archivo | Reemplaza | Tiempo y memoria (ventana real) |
|---|---|---|
| `src/modelos/densidad_np.py` | `densidad.py` (proximidad y densidad) | **3,7 s y ≈ 490 MB**, sin disco |
| `src/modelos/logit_disperso.py` | el logit de `backtest.py` | **37 s y ≈ 400 MB** (panel 2015→2020: 403.400 filas, 5.040 efectos fijos) |

- **La densidad es idéntica a la de la versión SQL**: se verificó con tres casos aleatorios contra `calcular_phi` y `calcular_densidad` (diferencia máxima menor a 1e-5) y con un ejemplo calculado a mano. Se usa una multiplicación de matrices en vez de unir y sumar.
- **El logit** coincide con statsmodels cuando no hay separación perfecta (probabilidades a menos de 0,002). Cuando algún país o producto no tiene ninguna entrada, el máximo está en el infinito: se usa una penalización suave (`C=10`). **Errores estándar agrupados (2026-10-13):** `LogitEfectosFijos.errores_agrupados(df, 'E', 'country')` devuelve coef, error estándar, z y p con el estimador sandwich agrupado por país (D2, tarea 1.9). Usa el complemento de Schur sobre los efectos fijos, sin armar la matriz de información completa: en un panel de 168.000 filas, 140 países, 1.200 productos y 3 pendientes tarda 0,2 s además del ajuste y usa unos 0,2 GB. Coincide con statsmodels (`cov_type='cluster'`, sin corrección de muestra) hasta el quinto decimal. Se calcula como máxima verosimilitud sin penalización; con `C=10` la diferencia en las pendientes es despreciable. Por defecto aplica la corrección G/(G-1).

### Cómo usarlas
```bash
uv run python -m src.modelos.densidad_np --db RUTA_A_LA_BASE.duckdb --phi-dir CARPETA_OPCIONAL
```
Lee `presencia_{ini}_{fin}` y `rca_matrix` de la base y escribe `densidad_{ini}_{fin}` con las mismas columnas que lee `backtest.py`. No crea las tablas `phi_*`.

En `backtest.py`, cambiar el ajuste por:
```python
from src.modelos.logit_disperso import LogitEfectosFijos

df["prob"] = LogitEfectosFijos(["densidad_z"], ["country", "product"], C=10).ajustar(df, "E").predecir(df)
```

## Recuperar espacio en el disco de Ever
1. **Revisar el tamaño de las carpetas** `duckdb_temp` (hay dos: `C:\ever\tape\db\duckdb_temp` y `C:\ever\complejidad\duckdb_temp`) y los archivos `.wal`. Con los procesos cerrados se pueden borrar: son temporales.
2. **Hay dos copias de la base**: `densidad.py` usa `C:\ever\tape\db\econofold.duckdb` y los demás módulos `C:\ever\complejidad\econofold.duckdb`. Conviene dejar una sola.
3. **DuckDB no achica el archivo al borrar tablas.** Para compactarlo: crear una base nueva y copiar (`ATTACH 'nueva.duckdb' AS n; COPY FROM DATABASE actual TO n;`) o usar `EXPORT DATABASE` / `IMPORT DATABASE`.
4. **El archivo de paginación de Windows (`pagefile.sys`)** puede quedar grande después de un cálculo así; se reduce al reiniciar la PC.

```powershell
Get-ChildItem C:\ever -Recurse -File | Group-Object { $_.DirectoryName } | ForEach-Object { [pscustomobject]@{ Carpeta = $_.Name; GB = [math]::Round(($_.Group | Measure-Object Length -Sum).Sum / 1GB, 2) } } | Sort-Object GB -Descending | Select-Object -First 10
```

## Otras observaciones sobre `src/modelos/` (no se tocaron)
1. **`depurar.py` borra filas pero no recalcula el RCA.** `rca_depurado` quita la energía (HS 271600) y las reexportaciones, pero el RCA de los productos que quedan sigue calculado con la energía en el denominador: en 2015 la energía es el 23 % de las exportaciones de Paraguay, así que el RCA de todo lo demás queda subestimado. Hay que recalcular el RCA después de depurar.
2. **La depuración no llega a la densidad.** `presencia.py` y `densidad.py` leen `rca_matrix` (sin depurar); solo `panel.py` usa `rca_depurado`.
3. **Constantes sin usar en `panel.py`:** `MIN_POBLACION` y `MIN_EXPORT` (D8) están definidas pero no se aplican. D7 y D8 se decidieron el 2026-10-12 (ver `docs/supuestos.md`): la entrada principal es la de un solo año, con la variante «2 de 3 años» como robustez, y el filtro de D8 es población ≥ 1 millón y exportaciones ≥ USD 1.000 millones; hay que aplicarlos en `panel.py`.
4. **Rutas fijas de Windows** (`C:\ever\...`): hay que pasarlas a un parámetro o a una variable de entorno para que corra en otra máquina o en un servidor.
5. **Para subir a un servidor (Railway, Cloudflare):** no subir la base de 3 GB. La aplicación necesita solo los resultados (tablas chicas en parquet: densidades, probabilidades, requisitos y dotaciones), que pesan megabytes.
