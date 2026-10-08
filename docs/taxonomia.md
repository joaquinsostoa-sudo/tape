# Taxonomía de sectores TAPE (tarea 0.4)

Archivo: `data/clean/taxonomia_sectores_tape.csv`. Código y validaciones: `src/puentes/taxonomia_tape.py`, `tests/test_taxonomia_tape.py`. Este documento se genera con `src/puentes/doc_taxonomia.py`.

**67 sectores** (41 de bienes con código HS y 26 de servicios, construcción y energía), sobre CIIU Rev.4 (decisión D9). Los ids se asignan por orden y cambian si se inserta un sector.

## Criterios de corte
1. **Base CIIU Rev.4.** Cada sector es una lista de prefijos (división, grupo o clase). Se desagrega más donde Paraguay tiene espacio producto (alimentos, textil y cuero, metales, químicos). Los servicios quedan agrupados porque no entran al espacio producto.
2. **Partición exacta.** Cada clase CIIU de las secciones A-S cae en un solo sector (prueba automática contra la tabla oficial de la ONU). Se excluye la división 99.
3. **Herencia de grupos.** Ningún sector cruza los grupos de EPHC, crédito BCP, cuentas regionales, MIP ni las 33 actividades del BCP, así cada sector hereda un solo grupo de cada clasificación. Esto obligó a separar comercio mayorista de minorista, agencias de viaje de alojamiento, ganadería de cultivos y panificados de confitería y pastas (el BCP los pone en actividades distintas). Única excepción: educación y salud, que las 33 actividades reparten entre servicios a los hogares (privado) y gubernamentales (público); la CIIU no distingue la titularidad.
4. **Detalle según los datos disponibles.** Dentro de un grupo se puede dividir; nunca juntar grupos distintos.

## Tabla
Columna "grupos": EPHC / crédito / cuentas regionales / MIP / 33 actividades BCP. Las 33 actividades y las 6 ramas regionales siguen las definiciones **oficiales** del BCP (SCN año base 2014 y Metodología de Cuentas Regionales); EPHC, crédito y MIP son supuestos por nombre (ver `clasificaciones_locales.py`).

| ID | Sector | CIIU Rev.4 | Comercio | Grupos | Confianza | Notas |
|---|---|---|---|---|---|---|
| S01 | Cultivos anuales (soja, maíz, trigo, arroz, caña, algodón, hortalizas) | 011 | sí | E1 / K03 / R1 / M01 / N01 | alta | núcleo exportador de Paraguay |
| S02 | Cultivos perennes y viveros | 012,013 | sí | E1 / K03 / R1 / M01 / N01 | alta |  |
| S03 | Ganadería bovina y otras especies, servicios pecuarios y caza | 0141,0142,0143,0144,0149,0162,017 | sí | E1 / K08 / R2 / M01 / N02 | alta | 0149 incluye apicultura; el BCP pone el apoyo pecuario (0162) y la caza (017) con ganadería |
| S04 | Avicultura y porcicultura | 0145,0146 | sí | E1 / K08 / R2 / M01 / N02 | alta |  |
| S05 | Servicios agrícolas, poscosecha (silos, acopio) y agricultura mixta | 015,0161,0163,0164 | no | E1 / K03 / R1 / M01 / N01 | media | 015 (mixta) se agrupa aquí porque el BCP la cuenta como agricultura |
| S06 | Silvicultura y extracción de madera | 02 | sí | E1 / K03 / R2 / M01 / N03 | alta |  |
| S07 | Pesca y acuicultura | 03 | sí | E1 / K10 / R2 / M01 / N04 | alta |  |
| S08 | Minería y canteras | 05,06,07,08,09 | sí | SIN_GRUPO / K10 / R2 / M02 / N05 | media | en Paraguay es sobre todo canteras y áridos (08) |
| S09 | Frigoríficos y productos cárnicos | 101 | sí | E2 / K09 / R3 / M03 / N06 | alta | carne bovina |
| S10 | Lácteos | 105 | sí | E2 / K09 / R3 / M03 / N08 | alta |  |
| S11 | Aceites y oleaginosas | 104 | sí | E2 / K09 / R3 / M03 / N07 | alta | molienda de soja |
| S12 | Molinería (trigo, maíz y otros) | 1061 | sí | E2 / K09 / R3 / M03 / N09 | alta | los almidones (1062) van con otros alimentos porque el BCP los cuenta en otra actividad |
| S13 | Panificados | 1071 | sí | E2 / K09 / R3 / M03 / N09 | alta |  |
| S14 | Confitería y pastas | 1073,1074 | sí | E2 / K09 / R3 / M03 / N11 | alta | separado de panificados porque el BCP los pone en actividades distintas |
| S15 | Frutas, hortalizas y pescado procesados | 102,103 | sí | E2 / K09 / R3 / M03 / N11 | alta |  |
| S16 | Azúcar | 1072 | sí | E2 / K09 / R3 / M03 / N10 | alta |  |
| S17 | Almidones, yerba mate, hierbas y otros alimentos | 1062,1075,1079 | sí | E2 / K09 / R3 / M03 / N11 | media |  |
| S18 | Alimentos balanceados y para mascotas | 108 | sí | E2 / K09 / R3 / M03 / N11 | alta |  |
| S19 | Bebidas, alcohol y agua envasada | 1101,1102,1103,1104 | sí | E2 / K09 / R3 / M03 / N12 | alta | 1101 incluye alcohol etílico; los biocombustibles se identifican por producto HS |
| S20 | Tabaco | 12 | sí | E2 / K09 / R3 / M03 / N12 | alta |  |
| S21 | Textiles e hilandería | 13 | sí | E2 / K09 / R3 / M04 / N13 | alta |  |
| S22 | Confecciones | 14 | sí | E2 / K09 / R3 / M04 / N13 | alta | maquila |
| S23 | Cuero y calzado | 15 | sí | E2 / K09 / R3 / M04 / N14 | alta |  |
| S24 | Aserrado y productos de madera | 16 | sí | E2 / K09 / R3 / M05 / N15 | alta |  |
| S25 | Muebles | 31 | sí | E2 / K09 / R3 / M11 / N22 | alta |  |
| S26 | Papel y cartón | 17 | sí | E2 / K09 / R3 / M05 / N16 | alta |  |
| S27 | Impresión y reproducción | 18 | no | E2 / K09 / R3 / M05 / N16 | alta | mayormente servicios; poco comercio |
| S28 | Petróleo refinado y combustibles | 19 | sí | E2 / K09 / R3 / M06 / N17 | media | los biocombustibles no tienen clase CIIU propia: se identifican por producto HS (ver docs/taxonomia.md) |
| S29 | Químicos básicos, fertilizantes y agroquímicos | 201,2021,203 | sí | E2 / K09 / R3 / M06 / N17 | alta |  |
| S30 | Pinturas, limpieza y cosmética | 2022,2023,2029 | sí | E2 / K09 / R3 / M06 / N17 | alta |  |
| S31 | Farmacéutica | 21 | sí | E2 / K09 / R3 / M06 / N17 | alta |  |
| S32 | Caucho y plásticos | 22 | sí | E2 / K09 / R3 / M06 / N17 | alta | maquila de plásticos |
| S33 | Cemento, hormigón y prefabricados | 2394,2395 | sí | E2 / K09 / R3 / M07 / N18 | alta |  |
| S34 | Cerámica y ladrillos | 2391,2392,2393 | sí | E2 / K09 / R3 / M07 / N18 | alta | olerías |
| S35 | Vidrio, piedra y otros minerales no metálicos | 231,2396,2399 | sí | E2 / K09 / R3 / M07 / N18 | alta |  |
| S36 | Siderurgia y fundición | 241,243 | sí | E2 / K09 / R3 / M08 / N19 | alta |  |
| S37 | Metales no ferrosos y aluminio | 242 | sí | E2 / K09 / R3 / M08 / N19 | alta | maquila de aluminio |
| S38 | Productos de metal y estructuras (herrería, mecanizado) | 25 | sí | E2 / K09 / R3 / M09 / N20 | alta |  |
| S39 | Maquinaria y equipo | 28 | sí | E2 / K09 / R3 / M10 / N21 | alta |  |
| S40 | Electrónica y equipo eléctrico (incluye cables) | 26,27 | sí | E2 / K09 / R3 / M10 / N21 | media | los arneses de maquila se asignan a Autopartes y vehículos por producto HS |
| S41 | Autopartes y vehículos | 29 | sí | E2 / K09 / R3 / M10 / N21 | alta | maquila de autopartes; incluye los arneses |
| S42 | Otro equipo de transporte y astilleros | 30 | sí | E2 / K09 / R3 / M10 / N21 | alta |  |
| S43 | Joyería, deportes y manufacturas diversas | 32 | sí | E2 / K09 / R3 / M11 / N22 | alta |  |
| S44 | Reparación e instalación de maquinaria | 33 | no | E2 / K09 / R3 / M11 / N22 | alta |  |
| S45 | Electricidad, gas y vapor | 35 | no | E3 / K10 / R4 / M12 / N23 | alta | la exportación de energía eléctrica (HS 271600) se excluye del comercio |
| S46 | Agua, saneamiento y remediación | 36,37,39 | no | E3 / K10 / R4 / M12 / N23 | alta |  |
| S47 | Gestión de residuos y reciclaje | 38 | no | E3 / K10 / R4 / M12 / N23 | alta |  |
| S48 | Construcción | 41,42,43 | no | E4 / K06 / R5 / M13 / N24 | alta |  |
| S49 | Comercio mayorista | 46 | no | E5 / K04 / R6 / M14 / N25 | alta |  |
| S50 | Comercio minorista y de vehículos | 45,47 | no | E5 / K05 / R6 / M14 / N25 | alta |  |
| S51 | Transporte terrestre y por tuberías | 49 | no | E6 / K12 / R6 / M15 / N26 | alta |  |
| S52 | Transporte acuático y aéreo | 50,51 | no | E6 / K12 / R6 / M15 / N26 | alta | hidrovía |
| S53 | Almacenamiento, logística y correos | 52,53 | no | E6 / K12 / R6 / M15 / N26 | alta |  |
| S54 | Alojamiento y gastronomía | 55,56 | no | E5 / K12 / R6 / M16 / N31 | alta |  |
| S55 | Agencias de viaje y turismo | 79 | no | E6 / K12 / R6 / M16 / N30 | alta | separado de alojamiento porque EPHC lo agrupa en otra rama |
| S56 | Telecomunicaciones | 61 | no | E6 / K12 / R6 / M17 / N27 | alta |  |
| S57 | Software, informática y servicios de información | 62,63 | no | E7 / K12 / R6 / M17 / N27 | alta |  |
| S58 | Edición, audiovisual y medios | 58,59,60 | no | E8 / K12 / R6 / M17 / N27 | media |  |
| S59 | Finanzas y seguros | 64,65,66 | no | E7 / K11 / R6 / M18 / N28 | alta |  |
| S60 | Servicios inmobiliarios | 68 | no | E7 / K01 / R6 / M19 / N29 | alta |  |
| S61 | Servicios profesionales, científicos y técnicos | 69,70,71,72,73,74,75 | no | E7 / K12 / R6 / M20 / N30 | alta |  |
| S62 | Servicios administrativos y de apoyo a empresas | 77,78,80,81,82 | no | E7 / K12 / R6 / M20 / N30 | alta |  |
| S63 | Administración pública y defensa | 84 | no | E8 / K02 / R6 / M21 / N33 | alta |  |
| S64 | Educación | 85 | no | E8 / K12 / R6 / M21 / N32+N33 | alta | público y privado: reparte entre N32 y N33 del BCP |
| S65 | Salud y asistencia social | 86,87,88 | no | E8 / K12 / R6 / M21 / N32+N33 | alta | público y privado: reparte entre N32 y N33 del BCP |
| S66 | Arte, recreación y deportes | 90,91,92,93 | no | E8 / K12 / R6 / M16 / N32 | alta |  |
| S67 | Otros servicios personales y de reparación | 94,95,96,97,98 | no | E8 / K12 / R6 / M21 / N32 | media |  |

## Decisiones tomadas (2026-10-08)
- Se mantiene la taxonomía de 66 sectores propuesta, más uno forzado por el BCP: **confitería y pastas** se separa de panificados.
- **Biocombustibles:** no tienen clase CIIU propia; se identifican **por producto HS** en el puente (tarea 0.5), no por sector.
- **Arneses de maquila:** se asignan a **Autopartes y vehículos** por producto HS.
- **Las 33 actividades del BCP se mapean con la definición oficial** (SCN año base 2014). Frente a mi primer supuesto cambió: el almidón (CIIU 1062) va con otros alimentos y no con la molinería; ganadería incluye el apoyo pecuario (0162) y la caza (017); "telecomunicaciones" incluye edición, audiovisual, informática y servicios de información (58 a 63); y las agencias de viaje (79) van en servicios a las empresas. Por eso molinería se separa de almidones, y los servicios pecuarios y la caza pasan al sector de ganadería.
- Excepción conocida: el hielo (CNAEP 10991) lo cuenta el BCP en otros alimentos, pero su clase CIIU (3530) cae en electricidad, gas y vapor. Solo afecta a datos codificados en CNAEP.

## Puntos pendientes de revisión
1. **Mapeos supuestos de EPHC, crédito y MIP.** Se hicieron por el nombre de cada categoría. Con los clasificadores oficiales (INE, BCP, CEPAL-OIT) se pueden confirmar; si alguno cambia, la prueba indica qué sector pasa a cruzar grupos.
2. **"Productos metálicos" vale cero de 1991 a 2007** en la serie del BCP: corte de serie, hay que saber dentro de qué actividad estaba antes.
3. **Educación y salud** (público y privado) se reparten entre dos actividades del BCP; el dato público/privado no se puede asignar por CIIU.
4. **Minería.** La EPHC no muestra una rama de minería: queda `SIN_GRUPO` hasta tener el clasificador del INE.
5. **Cantidad.** Son 67, por encima del rango 40-60 del documento técnico. Si querés reducir, se pueden juntar los tres sectores de transporte y logística, educación con salud, o lácteos con molinería. Juntar pierde detalle.
6. **Servicios y construcción** quedan fuera del espacio producto; se usan en el módulo territorial y en las cuentas nacionales.
