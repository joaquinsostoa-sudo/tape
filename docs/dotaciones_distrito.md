# Dotaciones por distrito: energía, logística y recursos

Fecha: 2026-10-16. Código: `src/puentes/dotaciones_distrito.py` y `src/puentes/exigencia_capas.py` (6 pruebas en `tests/test_dotaciones_distrito.py`). Reglas declaradas antes de construir: D33 en `docs/supuestos.md`.
Salidas (en `data/clean/`): `dotaciones_distrito.csv` (una fila por distrito) y `exigencia_capas_sector.csv` (el requisito de cada sector por capa). Inventario previo: `docs/equivalencias_dotaciones.md`.

> **Estado (2026-10-16): el índice de recursos es PRELIMINAR y no se usa para diagnosticar** hasta conseguir el rendimiento y el uso del suelo (decisión de Joaquín). Energía y logística no tienen esa marca.

## En palabras simples
Tres capas nuevas por distrito, además del capital humano, medidas como en D30 (lo que hay cerca también cuenta, con un peso que baja con la distancia: escalas de 15, 30 —la principal— y 60 km):
- **Energía:** cuánta potencia eléctrica disponible hay en las subestaciones cercanas (promedio 2026-2028) y qué tan lejos está la subestación de 220 o 500 kV más cercana.
- **Logística:** qué tan cerca están las aduanas, puertos y pasos de frontera (y cuánto comercio pasa por ellos), cuántos km de ruta nacional hay en el entorno y qué tan lejos están los polos (Asunción, Ciudad del Este, Encarnación, Puerto Central).
- **Recursos:** la superficie agropecuaria de las fincas del entorno.

Cada índice es el promedio de los percentiles entre los 263 distritos de sus medidas (0 es lo peor y 100 lo mejor; en las distancias, estar más cerca es mejor). **El capital físico no se construye por distrito** (lo reemplaza la densidad) y **el crédito es un indicador del sector** (D33).

## Control
| Qué se mide | Resultado |
|---|---|
| Distritos | 263 (1 sin coordenadas: María Antonia) |
| Distritos sin dato de superficie agropecuaria | 4 |
| Distritos con ruta nacional | 199 (64 sin ruta) |
| Distancia a la subestación de 220 o 500 kV | mediana 28 km, percentil 90 en 79 km, máximo 217 km |
| Distancia a aduana, puerto o paso | mediana 58 km, percentil 90 en 122 km, máximo 197 km |
| Pool de potencia disponible a 30 km | mediana 35 MW, percentil 90 en 337 MW, máximo 681 MW |

Los más altos y los más bajos (índice a 30 km):
| Índice | Más altos | Más bajos |
|---|---|---|
| Energía | Asunción, Lambaré, San Lorenzo, Fernando de la Mora, Villa Elisa | Bahía Negra, Tte. Esteban Martínez, Fuerte Olimpo, Puerto Pinasco |
| Logística | Asunción, Lambaré, Mariano Roque Alonso, Nueva Asunción, Fernando de la Mora | Campo Aceval, Puerto Pinasco, Fuerte Olimpo, Bella Vista |
| Recursos | Mariscal Estigarribia, Villa Hayes, Benjamín Aceval, Puerto Pinasco, Limpio | Paso de Patria, Humaitá, Gral. José E. Díaz, Alberdi |

Correlación de rangos entre los índices (30 km): energía–logística **0,85**, energía–recursos 0,41, logística–recursos 0,37; con la población 0,30, 0,29 y 0,24.

Sensibilidad a la escala (correlación de rangos entre 15 y 60 km, y distritos que cambian más de 10 puntos): energía 0,94 (82 distritos), logística 0,84 (116) y **recursos 0,37 (179)**.

## Hallazgos que cambian cómo se leen
1. **El índice de recursos mide extensión y no productividad, y está dominado por el Chaco.** El **56 % de todas las hectáreas agropecuarias (30,4 millones) está en 18 distritos** de Boquerón, Alto Paraguay y Presidente Hayes (ganadería extensiva). Mariscal Estigarribia (4,1 millones de hectáreas) y Villa Hayes sacan 100; Santa Rita y Naranjal, el corazón sojero, sacan 20 y 15, y Encarnación 8. **No distingue cultivos de ganadería ni la calidad de la tierra**, y es muy inestable con la escala (0,37 entre 15 y 60 km). La medida declarada (hectáreas) se aplicó como estaba; **no se cambió**. Queda para decisión de Joaquín (ver abajo).
2. **Energía y logística se parecen mucho (0,85)**: las dos siguen la cercanía a la infraestructura del Gran Asunción. Para un diagnóstico por capa eso significa que, en la práctica, a un distrito le falta o no le falta infraestructura en conjunto.
3. **La energía es estable con la escala** (0,94 a 0,98) y la más confiable de las tres. Pero mide **disponibilidad** y no precio, y la potencia disponible oscila por año (1.705 MW en 2026, 1.963 en 2028, 1.424 en 2033).
4. **Nueva Asunción** aparece entre los 5 primeros en logística: está a 3,8 km de Asunción en línea recta pero **al otro lado del río**.

## Qué sectores exigen cada capa (`exigencia_capas_sector.csv`)
Con la mediana de los productos como corte (energía 0,0146; valor por kilo 5,04 USD):
- **Energía** (solo manufactura; 18 de 35 sectores con dato exigen): aceites, molinería, azúcar, papel, siderurgia, cemento, cerámica, vidrio, química, plásticos, textiles y madera, entre otros. Sin dato: agro, minería, servicios y S44.
- **Logística** (valor por kilo por debajo de la mediana; 31 de 50 sectores con dato): los bienes pesados y de bajo valor, como cemento (0,20 USD/kg), azúcar (0,21), petróleo refinado (0,38), molinería (0,75) y aceites (0,96). No exigen farmacéutica (44 USD/kg), electrónica (42), joyería (25) ni confecciones (21).
- **Recursos** (lista): S01 a S07 y S09 a S21, S23 y S24 (22 sectores).
- **Capital:** solo informativo, como «inversión inicial exigida». Los más intensivos: petróleo refinado (1.875 mil USD por trabajador), azúcar (950) y química básica (625).

## Límites que hay que tener presentes
- **Distancia en línea recta**, no tiempo de viaje; el punto del distrito es el centro de la ciudad.
- **Energía mide disponibilidad y no precio**, y solo 2026-2028 traen las dos redes (23 kV y 220/66 kV). Sumarlas puede solaparse; se publican también por separado.
- **El mapa MIC es una foto de 2026** y la potencia disponible es una proyección.
- Los pesos iguales de cada índice son un supuesto. Resultados como asociación, no causalidad.

## Qué falta
1. **Decidir la medida de recursos** (ver abajo).
2. **El diagnóstico multi-capa por industria**: aplicar D31 a cada capa que el bien exige y mostrar qué le falta a cada distrito (base, formación, energía, logística, recursos) y, con eso, quién debe actuar (D16). No está declarado ni construido.
3. **El crédito como indicador del sector** (crédito del BCP sobre valor agregado), para la fase de política (D15).

## Opciones para la medida de recursos
- **Hectáreas por superficie del distrito** (qué parte del distrito está bajo fincas): corrige el tamaño, pero hace falta el área de cada distrito (los polígonos de 2012 cubren 247 de 263).
- **Fincas por 1.000 habitantes** o **superficie media por finca**: otras formas de la misma fuente, sin separar cultivo de ganadería.
- **Conseguir cultivos y ganadería por distrito** (otro tomo del Censo Agropecuario 2022) y medir el recurso por sector agropecuario: es la que realmente responde a la pregunta, pero requiere el dato.
- **Dejarlo como está** y leerlo como «extensión de tierra con fincas», sin usarlo para diagnosticar.
