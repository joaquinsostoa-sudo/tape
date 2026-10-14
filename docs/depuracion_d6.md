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

## Decisión del equipo (2026-10-14): alcance (a)
La marca se calcula para todos los países (columnas informativas) pero **solo se aplica** (`reexportacion_aplicada`, la que usa el «RCA depurado») a **Paraguay y a una lista explícita de centros de reexportación: Hong Kong, Singapur, Países Bajos y Bélgica** (`PAISES_DEPURADOS` en `depuracion.py`). El resto de los países usa exportaciones brutas, porque en ellos la razón M/X marca comercio intraindustrial genuino.
Efecto sobre `exportaciones_hs4_depurado.parquet`: solo cambian esos cinco países; se excluye el 93 % de las exportaciones de Hong Kong, el 69 % de Singapur y de Países Bajos, el 68 % de Bélgica y el 4,6 % de Paraguay (con la energía, que los modelos ya excluían); los demás quedan idénticos.

## Robustez del modelo (criterio declarado)
Backtest nacional repetido con `exportaciones_hs4_depurado.parquet` (`data/model/backtest_resultados_d6.csv`). Criterio declarado: la conclusión «las capas no mejoran a la densidad» se mantiene si los intervalos de la diferencia capas − densidad sola en precision@20 por país incluyen el cero en las tres ventanas y la precision@20 de la densidad sola cambia menos de 0,01.

| Prueba | Densidad sola p@20 (antes → alcance a) | Capas − densidad, p@20 por país (IC 95 %) |
|---|---|---|
| 2005→2010 | 0,088 → 0,092 (+0,004) | −0,002 (−0,007; +0,003) |
| 2010→2015 | 0,085 → 0,087 (+0,002) | −0,006 (−0,014; +0,000) |
| 2015→2020 | 0,075 → 0,073 (−0,002) | +0,001 (−0,004; +0,007) |

**Criterio cumplido:** los intervalos incluyen el cero (en 2010 el límite superior es 0,000: el modelo con capas queda, si algo, apenas peor) y la densidad cambia menos de 0,01 en las tres ventanas. La conclusión central (D16) no depende de la depuración elegida.

**Para contraste, la depuración aplicada a todos los países** (descartada): la conclusión sobre las capas también se mantiene, pero la precision@20 de la densidad sube 0,013, 0,030 y 0,019 (no cumple el criterio de 0,01) con otra muestra (tasa base de 3,4 % en lugar de 2,8 %): es el efecto de sacar de golpe el 38 % del comercio mundial, por eso se acotó el alcance.

## Pendiente
- Revisar con la aduana la lista de productos marcados para Paraguay (sobre todo los que Paraguay también produce).
- Los modelos siguen usando por defecto `exportaciones_hs4.parquet` (brutas); para el «RCA depurado» de D13 se pasa `--expo data/model/exportaciones_hs4_depurado.parquet`. La definición final de qué tabla es la principal en el informe de la Fase 1 queda para esa tarea.
