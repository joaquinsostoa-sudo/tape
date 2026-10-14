# Pruebas del punto 3 de la tarea 1.11: HS6, países excluidos y casos de Paraguay (2026-10-14)

Declaradas antes de correr en `docs/supuestos.md` (commit `7bf0b12`); código: `src/modelos/robustez_hs6.py`, `paises_excluidos.py` y `casos_paraguay.py`. Todas con la tabla de exportaciones depurada con el alcance (a) de D6, esquema del backtest nacional (D2 a), pruebas 2005, 2010 y 2015. Resultados como asociación, no causalidad.

## A. HS4 contra HS6 (D5)
Mismo modelo con 4.000 productos HS6 en lugar de 1.000 HS4 (393.000 a 450.000 filas por ventana de prueba, 10.900 a 12.900 entradas). Datos: `data/model/backtest_resultados_hs6*.csv`.

| Ventana | Nivel | p@20 por país, densidad sola | Tasa base | «Lift» (p@20 / base) | AUC-PR |
|---|---|---|---|---|---|
| 2005 | HS6 | 0,114 | 0,033 | 3,5 | 0,078 |
| | HS4 | 0,092 | 0,029 | 3,2 | 0,066 |
| 2010 | HS6 | 0,097 | 0,026 | 3,7 | 0,066 |
| | HS4 | 0,087 | 0,024 | 3,6 | 0,059 |
| 2015 | HS6 | 0,100 | 0,024 | 4,1 | 0,067 |
| | HS4 | 0,073 | 0,021 | 3,4 | 0,056 |

Capas − densidad sola en HS6 (IC 95 % por remuestreo de países):

| Ventana | p@20 por país | AUC-PR |
|---|---|---|
| 2005 | −0,000 (−0,007; +0,007) | **+0,0006 (+0,0002; +0,0010)** |
| 2010 | −0,005 (−0,012; +0,002) | **+0,0006 (+0,0002; +0,0010)** |
| 2015 | −0,005 (−0,011; +0,003) | +0,0003 (−0,0001; +0,0008) |

- **A2 se cumple con holgura:** la densidad ordena de 3,5 a 4,1 veces mejor que el azar en la lista corta de cada país (el criterio pedía 2,0); a HS6 es igual o mejor que a HS4. El resultado de la densidad **no depende del nivel de agregación**.
- **A1 no se cumple tal como se declaró:** en p@20 los intervalos incluyen el cero en las tres ventanas, pero en AUC-PR el intervalo excluye el cero en 2005 y 2010 (a favor de las capas). Regla declarada para este caso: **hallazgo a replicar; no cambia D16 por sí solo.**
- **Cómo leerlo:** la diferencia es de 0,0006 sobre un AUC-PR de 0,066 a 0,078 (un 0,8 %), es decir estadísticamente detectable con 400.000 filas pero sin consecuencia práctica; en la métrica principal de listas cortas (p@20) las capas no ayudan y, en 2010 y 2015, quedan algo por debajo (−0,005). Con HS4 la diferencia de AUC-PR incluía el cero. No se redefine el criterio.

## B. Países excluidos comparables a Paraguay
En cada ventana, los 10 países más cercanos a Paraguay en PIB per cápita (Jamaica, Irak, Túnez, Ecuador, Jordania, Egipto, Namibia, Guatemala, Siria y Perú en 2005; Túnez, Egipto, Perú, Jordania, Albania, Irak, Ecuador, Colombia, Sudáfrica y Argelia en 2010; Perú, Sudáfrica, Irán, China, Mongolia, Ecuador, Albania, Argelia, Irak y Ucrania en 2015) se retiran del entrenamiento y se predicen con el modelo tipo Mundlak (sin efecto de país). 29 países-ventana tienen alguna entrada.

| | Tasa base | p@20 densidad | «Lift» densidad | p@20 capas | «Lift» capas |
|---|---|---|---|---|---|
| Comparables retenidos | 0,025 | 0,052 | **2,10** | 0,053 | 2,17 |
| 10 países al azar retenidos (20 sorteos) | 0,026 | 0,054 | 2,06 | 0,059 | 2,24 |

- **B1 se cumple, justo:** la densidad ordena 2,1 veces mejor que el azar en países que el modelo no vio (el criterio era 2,0). Es menos que los 3 a 4 de los modelos con efecto de país (esos sí usan información de cada país en el entrenamiento).
- **B2 se cumple:** capas − densidad = +0,0017 (IC 95 % −0,012; +0,016), incluye el cero. Con 29 países-ventana la prueba tiene poca potencia: significa «no se detecta mejora».
- Los comparables **no son más difíciles** que 10 países cualesquiera (2,10 contra 2,06).
- **Paraguay retenido** (sin ningún dato de sus entradas): 1 acierto en su lista de 20 en 2005 (0903, yerba mate) y ninguno en 2010 ni en 2015.

## C. Casos de Paraguay
Casos definidos por tablas existentes: arneses = HS4 8544; frigoríficos = los 19 HS4 del sector S09 del puente HS; biocombustibles = 1518, 2207 y 3823. Eventos = entradas de Paraguay en esos productos (D7) en las ventanas de prueba.

| Caso | Producto | Ventana | Candidatos | Puesto (densidad sola) | Percentil | Puesto (capas) |
|---|---|---|---|---|---|---|
| Biocombustibles | 2207 etanol | 2010→2015 | 1.019 | **8** | **0,007** | 7 |
| Frigoríficos | 0210 carne salada o seca | 2005→2010 | 1.011 | 331 | 0,327 | 304 |
| Arneses | 8544 | 2010→2015 | 1.019 | 465 | 0,456 | 490 |
| Frigoríficos | 0209 grasa de cerdo y aves | 2010→2015 | 1.019 | 683 | 0,670 | 664 |

- **Criterio principal no cumplido:** 1 de 4 eventos queda marcado (percentil ≤ 10 %); el criterio pedía la mitad o más.
- **Biocombustibles:** el etanol estaba 8.º entre 1.019 candidatos antes de despegar: el único caso en que el modelo lo anticipa con claridad. **Arneses:** en el medio de la lista (percentil 0,46), como se esperaba: la entrada vino por maquila e inversión extranjera, no por capacidades locales. **Frigoríficos:** pocos eventos medibles; la carne bovina (0201 y 0202) ya tenía ventaja antes de 2000 y no es entrada con estas ventanas.
- Las capas casi no mueven los puestos. 2015→2020 no tiene eventos en estos casos. Son 4 eventos: descriptivo, sin inferencia.

## Qué sale de las tres pruebas
- La conclusión de D16 resiste: las capas no mejoran la lista corta a HS6 ni en países excluidos; la única señal en contra es una diferencia de AUC-PR de 0,0006 en HS6, a replicar.
- La densidad predice mejor que el azar de forma estable (3 a 4 veces a HS4 y HS6; 2 veces en países no vistos), pero los casos emblemáticos de Paraguay no se anticipan salvo el etanol.
- **Pendiente para cerrar la tarea 1.11:** decidir D1 (producto → sector) y armar el informe de la Fase 1.
