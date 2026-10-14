# Depuración del comercio (tarea 1.2, decisión D6)

Código: `src/limpieza/depuracion.py` (`uv run python -m src.limpieza.depuracion`, 10 segundos). Entradas: las tablas HS6 de BACI (`docs/baci_limpieza.md`). Salidas en `data/clean/` y `data/model/` (no versionadas): `comercio_depurado.parquet` (una fila por país-producto-año con exportación, con las marcas) y `exportaciones_hs4_depurado.parquet` (suma por HS4 de lo no marcado).

## Regla (declarada en `docs/supuestos.md` antes de correr)
Reexportación = X ≥ USD 100 mil **y** M ≥ 0,5 · X, con X y M las exportaciones e importaciones del mismo país, producto HS6 y año. Sensibilidad con 0,25 y 1,0. Se aplica a todos los países. La energía HS 271600 se marca `excluido_energia`. **No se borra nada**: son columnas.

## Resultado global (2019)
La regla marca el **38,4 % de las exportaciones mundiales** (55,0 % con 0,25; 21,1 % con 1,0): 199.079 de 530.810 pares país-producto. Los países con mayor proporción marcada (sin energía):

| País | Marcado (θ=0,5) | θ=0,25 | θ=1,0 |
|---|---|---|---|
| Hong Kong | 95,6 % | 97,8 % | 86,6 % |
| Reino Unido | 75,1 % | 86,1 % | 51,9 % |
| Países Bajos | 72,8 % | 84,2 % | 43,7 % |
| **Estados Unidos** | **72,3 %** | 83,8 % | 42,5 % |
| Bélgica | 68,4 % | 85,4 % | 31,2 % |
| Singapur | 67,7 % | 81,6 % | 58,0 % |
| **Alemania** | **62,4 %** | 90,8 % | 19,5 % |
| Francia | 61,0 % | 74,7 % | 35,5 % |

**El problema:** los centros de reexportación conocidos (Hong Kong, Países Bajos, Bélgica, Singapur) salen arriba, como se esperaba, pero también las economías grandes que producen lo que exportan (Estados Unidos, Alemania, Francia, Reino Unido). A nivel HS6 el comercio de ida y vuelta de un mismo producto (autos, maquinaria, medicamentos) es enorme y no es reexportación. **La razón M/X marca comercio intraindustrial genuino.** Aplicada a todos los países, la regla saca más de la mitad de las exportaciones de Alemania o Estados Unidos del RCA, que no es lo que D6 pretendía. El límite estaba declarado; la magnitud no se esperaba.

## Paraguay (la razón de ser de D6)
| Año | Total | Energía | Sin energía | Marcado (θ=0,5) | θ=0,25 | θ=1,0 |
|---|---|---|---|---|---|---|
| 2005 | 3,70 | 1,47 | 2,23 | 3,0 % | 4,5 % | 2,6 % |
| 2010 | 6,70 | 1,93 | 4,77 | 5,4 % | 7,1 % | 4,9 % |
| 2015 | 8,64 | 1,99 | 6,65 | 5,8 % | 7,8 % | 5,0 % |
| 2019 | 8,37 | 1,84 | 6,53 | 6,7 % | 7,5 % | 5,5 % |
| 2024 | 11,46 | 1,18 | 10,29 | 7,1 % | 9,3 % | 5,9 % |

(miles de millones de USD). La expectativa registrada se cumple: **la proporción marcada de las exportaciones sin energía es menor al 15 %** (3 a 7 %).

Productos HS6 marcados con más valor en 2015-2024 (en 9 a 10 de los 10 años, salvo los de menos años):
medicamentos 3004 (518 M USD exportados y 1.249 importados), derivados del petróleo 2710 (348 y 16.276), herbicidas 3808.30 (339), insecticidas 3808.10 (256), cigarrillos 2402.20 (201; 9 años), alimento para perros y gatos 2309 (260), vidrio 7010.90 (102), tereftalato de polietileno 3907.60 (70), fungicidas 3808.20 (61), tejidos de punto 6002 (107), panificados 1905.90 (54), jabón 3401.11 (51), cierres plásticos 3923.50 (41).

**Para revisar producto por producto y confirmar con la aduana:** al menos cigarrillos, alimento para mascotas, vidrio, PET y panificados, donde Paraguay también produce (la marca puede ser un falso positivo), y los agroquímicos y medicamentos, donde las importaciones son varias veces las exportaciones (reexportación probable a los vecinos). **Los arneses (HS 8544.30) no se marcan** (importaciones del 1 % de las exportaciones): la maquila transforma componentes de otros códigos HS, no los reexporta; esta regla no la captura.

## Robustez del modelo (criterio declarado)
Backtest nacional repetido con `exportaciones_hs4_depurado.parquet` (`data/model/backtest_resultados_d6.csv`):

| Prueba | Densidad sola p@20 (antes → ahora) | Capas − densidad, p@20 por país (IC 95 %) |
|---|---|---|
| 2005→2010 | 0,088 → 0,101 | −0,001 (−0,008; +0,005) |
| 2010→2015 | 0,085 → 0,115 | −0,002 (−0,009; +0,004) |
| 2015→2020 | 0,075 → 0,094 | −0,000 (−0,006; +0,005) |

- **Se mantiene la conclusión central:** los intervalos de la diferencia capas − densidad siguen incluyendo el cero en las tres ventanas y el AUC-PR de las capas es igual al de la densidad (0,082 contra 0,081, 0,090 contra 0,088, 0,080 contra 0,080).
- **La segunda condición declarada no se cumple en valor absoluto:** la precision@20 de la densidad sola sube 0,013, 0,030 y 0,019 (el criterio pedía menos de 0,01). Hay que leerlo con cuidado: la muestra cambia (más entradas: 3.395 contra 2.581 en 2005 y tasa base de 3,4 % contra 2,8 %, porque quitar flujos marcados baja el RCA y genera más entradas posteriores). **El «lift» sobre la tasa base es el mismo** (3,0 contra 3,1 veces en 2005), así que la capacidad de ordenar no cambia, pero no se redefine el criterio: se informa el cambio.

## Decisión pendiente (alcance de la marca)
La regla debe seguir siendo una marca (no borra), pero **para qué datos se usa como «RCA depurado»** cambia mucho el resultado en las economías grandes. Opciones:
- **(a)** Usar la marca solo para Paraguay (y, si se quiere, una lista explícita de centros de reexportación como Hong Kong, Singapur, Países Bajos y Bélgica); el resto con exportaciones brutas. Es lo que D6 buscaba: corregir la visión de Paraguay.
- **(b)** Aplicarla a todos con un umbral mucho más estricto (por ejemplo M ≥ 1,0 · X sigue marcando 21 % del mundo: no alcanza solo).
- **(c)** Usar exportaciones netas (X − M, mínimo cero) para todos los países.
- **(d)** Mantenerla como marca informativa y no depurar el RCA del modelo nacional (los resultados con y sin depuración llevan a la misma conclusión).

Recomiendo (a): resuelve el caso de Paraguay sin distorsionar a las economías que producen lo que exportan. Falta decidirlo y revisar la lista de productos marcados con la aduana.
