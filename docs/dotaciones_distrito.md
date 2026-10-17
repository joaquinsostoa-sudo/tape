# Dotaciones por distrito: energía, logística y recursos

Fecha: 2026-10-16 (actualizado el 2026-10-17 con D35 y D37: los requisitos por sector se ponderan por el comercio mundial). Código: `src/puentes/dotaciones_distrito.py` y `src/puentes/exigencia_capas.py` (8 pruebas en `tests/test_dotaciones_distrito.py`). Reglas declaradas antes de construir: D33 y D35 en `docs/supuestos.md`.
Salidas (en `data/clean/`): `dotaciones_distrito.csv` (una fila por distrito) y `exigencia_capas_sector.csv` (el requisito de cada sector por capa). Inventario previo: `docs/equivalencias_dotaciones.md`. Uso del suelo: `docs/` de MapBiomas en `data/raw/mapbiomas_paraguay/README.md`.

## En palabras simples
Tres capas nuevas por distrito, además del capital humano, medidas como en D30 (lo que hay cerca también cuenta, con un peso que baja con la distancia: escalas de 15, 30 —la principal— y 60 km):
- **Energía:** cuánta potencia eléctrica disponible hay en las subestaciones cercanas (promedio 2026-2028) y qué tan lejos está la subestación de 220 o 500 kV más cercana.
- **Logística:** qué tan cerca están las aduanas, puertos y pasos de frontera (y cuánto comercio pasa por ellos), cuántos km de ruta nacional hay en el entorno y qué tan lejos están los polos (Asunción, Ciudad del Este, Encarnación, Puerto Central).
- **Recursos (D35):** cuántas **hectáreas de la clase de tierra de su materia prima** hay cerca: **agricultura** para los cultivos y la agroindustria, **pastura** para la ganadería y los frigoríficos, **plantación forestal** para la madera. Sale del uso del suelo satelital de MapBiomas (2023).

Cada índice es el promedio de los percentiles entre los 263 distritos de sus medidas (0 es lo peor y 100 lo mejor; en las distancias, estar más cerca es mejor). **El capital físico no se construye por distrito** (lo reemplaza la densidad) y **el crédito es un indicador del sector** (D33).

## Qué cambió con D35
La medida inicial de recursos (hectáreas de fincas del Censo Agropecuario) medía **extensión y no productividad**: el 56 % de las hectáreas estaba en 18 distritos del Chaco y era inestable con la escala (0,37 entre 15 y 60 km). **Queda descartada** (las columnas antiguas siguen en el archivo como `*_fincas`, solo por trazabilidad). La reemplaza el uso del suelo de MapBiomas, que separa la tierra agrícola de la ganadera y de la forestal.

## Control
| Qué se mide | Resultado |
|---|---|
| Distritos | 263 (1 sin coordenadas: María Antonia) |
| Distritos sin dato de uso del suelo | 4 (Itacuá, San José de los Arroyos, Bella Vista, Nueva Asunción): sin índice de recursos |
| Distritos con ruta nacional | 199 (64 sin ruta) |
| Distancia a la subestación de 220 o 500 kV | mediana 28 km, percentil 90 en 79 km, máximo 217 km |
| Distancia a aduana, puerto o paso | mediana 58 km, percentil 90 en 122 km, máximo 197 km |
| Pool de potencia disponible a 30 km | mediana 35 MW, percentil 90 en 337 MW, máximo 681 MW |
| Hectáreas 2023 (millones) | agricultura 4,14 (13 % en el Chaco), pastura 8,14 (72 %), plantación forestal 0,09, bosque natural 20,87 (84 %) |

Los más altos (índice a 30 km) y su estabilidad con la escala (correlación de rangos entre 15 y 60 km; distritos que cambian más de 10 puntos):
| Índice | Más altos | Estabilidad |
|---|---|---|
| Energía | Asunción, Lambaré, San Lorenzo, Fernando de la Mora, Villa Elisa | 0,94 (82 distritos) |
| Logística | Asunción, Lambaré, Mariano Roque Alonso, Nueva Asunción, Fernando de la Mora | 0,84 (116) |
| Recursos, agricultura | San Alberto, Itakyry, Mbaracayú, Minga Porã, San Cristóbal | 0,83 (151) |
| Recursos, pastura | Mariscal Estigarribia, Boquerón, Filadelfia, Loma Plata, Fuerte Olimpo | 0,73 (132) |
| Recursos, plantación forestal | Maciel, Caazapá, Iturbe, Dr. Moisés Bertoni, San Juan Nepomuceno | 0,89 (119) |

Correlación de rangos entre los índices (30 km): energía–logística **0,85**. Los recursos casi no se parecen a la infraestructura: agricultura con energía −0,15 y con logística −0,06; pastura −0,21 y −0,37; plantación forestal 0,24 y 0,23. Entre clases: agricultura–pastura 0,33, agricultura–plantación 0,51, pastura–plantación −0,01. Con la población: energía 0,30, logística 0,29, agricultura 0,08, pastura 0,13, plantación −0,04.

## Hallazgos que cambian cómo se leen
1. **Los recursos ahora apuntan donde debe:** la agricultura, al cinturón sojero del este; la pastura, al Chaco ganadero (donde sí hay frigoríficos y lácteos); la plantación forestal, a Caazapá y Guairá. Y son más estables que la medida anterior.
2. **Energía y logística se parecen mucho (0,85)**: las dos siguen la cercanía a la infraestructura del Gran Asunción. Para un diagnóstico por capa eso significa que, en la práctica, a un distrito le falta o no le falta infraestructura en conjunto.
3. **La energía es la más estable con la escala** (0,94 a 0,98 entre escalas vecinas). Pero mide **disponibilidad** y no precio, y la potencia disponible oscila por año (1.705 MW en 2026, 1.963 en 2028, 1.424 en 2033).
4. **Nueva Asunción** aparece entre los 5 primeros en logística: está a 3,8 km de Asunción en línea recta pero **al otro lado del río**.

## Qué sectores exigen cada capa (`exigencia_capas_sector.csv`)
Con la mediana de los productos como corte (energía 0,0146; valor por kilo 5,04 USD):
- **Energía** (solo manufactura; 17 de 35 sectores con dato exigen, con D37): molinería, azúcar, papel, imprenta, petróleo refinado, siderurgia, cemento, cerámica, vidrio, química, plásticos, textiles y madera, entre otros. Sin dato: agro, minería, servicios y S44.
- **Logística** (valor por kilo por debajo de la mediana; 30 de 50 sectores con dato, con D37): los bienes pesados y de bajo valor, como cemento (0,20 USD/kg), azúcar (0,21), petróleo refinado (0,38), y molinería (0,75). No exigen farmacéutica (142 USD/kg), electrónica (97) ni confecciones (24).
- **Recursos** (lista de 22 sectores: S01 a S07, S09 a S21, S23 y S24), **con medida en 18**: agricultura para S01, S02, S04, S05, S11, S12, S15, S16, S17, S18, S20 y S21; pastura para S03, S09, S10 y S23; plantación forestal para S06 y S24. **Sin medida** (siguen en la lista pero sin brecha: sin dato, por decisión de Joaquín): S07 pesca, S13 panificados, S14 confitería y pastas y S19 bebidas.
- **Capital:** solo informativo, como «inversión inicial exigida». Los más intensivos, con D37: petróleo refinado (2.611 mil USD por trabajador), azúcar (950) y metales no ferrosos (731).

## Límites que hay que tener presentes
- **MapBiomas dice cuánta tierra es agrícola, ganadera o forestal, pero no el cultivo, el rendimiento ni la calidad.** La clase «agricultura» no separa soja de otros cultivos; «pastura» incluye pasturas cultivadas y manejadas y no separa carne de leche. La plantación forestal es muy escasa (0,09 millones de hectáreas).
- **La asignación de rubros a clases de tierra es un juicio de Claude** que debe validar el equipo.
- **Distancia en línea recta**, no tiempo de viaje; el punto del distrito es el centro de la ciudad.
- **Energía mide disponibilidad y no precio**, y solo 2026-2028 traen las dos redes (23 kV y 220/66 kV). Sumarlas puede solaparse; se publican también por separado.
- **El mapa MIC es una foto de 2026**, la potencia disponible es una proyección y el uso del suelo es de 2023.
- Los pesos iguales de cada índice son un supuesto. Resultados como asociación, no causalidad.

## Qué falta
1. **El diagnóstico multi-capa por industria**: aplicar D31 a cada capa que el bien exige y mostrar qué le falta a cada distrito (base, formación, energía, logística, recursos) y, con eso, quién debe actuar (D16). No está declarado ni construido.
2. **Rendimiento:** ponderar las hectáreas por el rendimiento departamental (Censo Agropecuario Volumen I) y, cuando llegue el pedido al MAG (`docs/solicitud_MAG_DCEA.md`), reemplazar la clase de tierra por los cultivos reales.
3. **El crédito como indicador del sector** (crédito del BCP sobre valor agregado), para la fase de política (D15).
