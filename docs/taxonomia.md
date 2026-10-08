# Taxonomía de sectores TAPE: borrador para aprobación (tarea 0.4)

Fecha: 2026-10-08. Archivo: `data/clean/taxonomia_sectores_tape.csv`. Código y validaciones: `src/puentes/taxonomia_tape.py`, `tests/test_taxonomia_tape.py`.

**66 sectores** (40 de bienes con código HS y 26 de servicios, construcción y energía), sobre CIIU Rev.4 (decisión D9).

## Criterios de corte
1. **Base CIIU Rev.4.** Cada sector es una lista de prefijos (división, grupo o clase). Se desagrega más donde Paraguay tiene espacio producto: alimentos (11 sectores), textil y cuero, metales, químicos. Los servicios quedan agrupados porque no entran al espacio producto.
2. **Partición exacta.** Cada clase CIIU de las secciones A-S cae en un solo sector (prueba automática contra la tabla oficial de la ONU). Se excluye la división 99 (organizaciones extraterritoriales).
3. **Herencia de grupos.** Ningún sector cruza los grupos de EPHC, crédito BCP, cuentas regionales ni MIP: así cada sector hereda un solo grupo de cada clasificación (regla del documento técnico). Esto obligó a separar, por ejemplo, el comercio mayorista (S48) del minorista (S49), las agencias de viaje (S54) de alojamiento (S53) y la ganadería (S03-S04) de los cultivos (S01-S02).
4. **Granularidad por detalle disponible.** Dentro de un grupo se puede dividir (p. ej. la MIP "Química, farmacia y caucho" son S27 a S31), pero nunca juntar grupos distintos.

## Tabla
Columna "grupos": EPHC / crédito / cuentas regionales / MIP, según el mapeo supuesto de `clasificaciones_locales.py`. Falta el grupo de las 33 actividades CNAEP del BCP (columna vacía).

| ID | Sector | CIIU Rev.4 | Comercio | Grupos | Confianza | Notas |
|---|---|---|---|---|---|---|
| S01 | Cultivos anuales (soja, maíz, trigo, arroz, caña, algodón, hortalizas) | 011 | sí | E1 / K03 / R1 / M01 | alta | núcleo exportador de Paraguay |
| S02 | Cultivos perennes y viveros | 012,013 | sí | E1 / K03 / R1 / M01 | alta |  |
| S03 | Ganadería bovina y otras especies | 0141,0142,0143,0144,0149 | sí | E1 / K08 / R2 / M01 | alta | 0149 incluye apicultura |
| S04 | Avicultura y porcicultura | 0145,0146 | sí | E1 / K08 / R2 / M01 | alta |  |
| S05 | Servicios agropecuarios y poscosecha (silos, acopio) | 015,016,017 | no | E1 / K03 / R1 / M01 | media | 015 (mixta) se agrupa aquí porque no se puede separar de la agricultura |
| S06 | Silvicultura y extracción de madera | 02 | sí | E1 / K03 / R2 / M01 | alta |  |
| S07 | Pesca y acuicultura | 03 | sí | E1 / K10 / R2 / M01 | alta |  |
| S08 | Minería y canteras | 05,06,07,08,09 | sí | SIN_GRUPO / K10 / R2 / M02 | media | en Paraguay es sobre todo canteras y áridos (08) |
| S09 | Frigoríficos y productos cárnicos | 101 | sí | E2 / K09 / R3 / M03 | alta | carne bovina |
| S10 | Lácteos | 105 | sí | E2 / K09 / R3 / M03 | alta |  |
| S11 | Aceites y oleaginosas | 104 | sí | E2 / K09 / R3 / M03 | alta | molienda de soja |
| S12 | Molinería y almidones | 106 | sí | E2 / K09 / R3 / M03 | alta |  |
| S13 | Panificados, confitería y pastas | 1071,1073,1074 | sí | E2 / K09 / R3 / M03 | alta |  |
| S14 | Frutas, hortalizas y pescado procesados | 102,103 | sí | E2 / K09 / R3 / M03 | alta |  |
| S15 | Azúcar y alcohol | 1072,1101 | sí | E2 / K09 / R3 / M03 | media | 1101 incluye alcohol; ver nota de biocombustibles |
| S16 | Yerba mate, hierbas y otros alimentos | 1075,1079 | sí | E2 / K09 / R3 / M03 | media |  |
| S17 | Alimentos balanceados y para mascotas | 108 | sí | E2 / K09 / R3 / M03 | alta |  |
| S18 | Bebidas y agua envasada | 1102,1103,1104 | sí | E2 / K09 / R3 / M03 | alta |  |
| S19 | Tabaco | 12 | sí | E2 / K09 / R3 / M03 | alta |  |
| S20 | Textiles e hilandería | 13 | sí | E2 / K09 / R3 / M04 | alta |  |
| S21 | Confecciones | 14 | sí | E2 / K09 / R3 / M04 | alta | maquila |
| S22 | Cuero y calzado | 15 | sí | E2 / K09 / R3 / M04 | alta |  |
| S23 | Aserrado y productos de madera | 16 | sí | E2 / K09 / R3 / M05 | alta |  |
| S24 | Muebles | 31 | sí | E2 / K09 / R3 / M11 | alta |  |
| S25 | Papel y cartón | 17 | sí | E2 / K09 / R3 / M05 | alta |  |
| S26 | Impresión y reproducción | 18 | no | E2 / K09 / R3 / M05 | alta | mayormente servicios; poco comercio |
| S27 | Petróleo refinado y combustibles | 19 | sí | E2 / K09 / R3 / M06 | media | los biocombustibles (biodiésel, bioetanol) no tienen clase CIIU propia: ver docs/taxonomia.md |
| S28 | Químicos básicos, fertilizantes y agroquímicos | 201,2021,203 | sí | E2 / K09 / R3 / M06 | alta |  |
| S29 | Pinturas, limpieza y cosmética | 2022,2023,2029 | sí | E2 / K09 / R3 / M06 | alta |  |
| S30 | Farmacéutica | 21 | sí | E2 / K09 / R3 / M06 | alta |  |
| S31 | Caucho y plásticos | 22 | sí | E2 / K09 / R3 / M06 | alta | maquila de plásticos |
| S32 | Cemento, hormigón y prefabricados | 2394,2395 | sí | E2 / K09 / R3 / M07 | alta |  |
| S33 | Cerámica y ladrillos | 2391,2392,2393 | sí | E2 / K09 / R3 / M07 | alta | olerías |
| S34 | Vidrio, piedra y otros minerales no metálicos | 231,2396,2399 | sí | E2 / K09 / R3 / M07 | alta |  |
| S35 | Siderurgia y fundición | 241,243 | sí | E2 / K09 / R3 / M08 | alta |  |
| S36 | Metales no ferrosos y aluminio | 242 | sí | E2 / K09 / R3 / M08 | alta | maquila de aluminio |
| S37 | Productos de metal y estructuras (herrería, mecanizado) | 25 | sí | E2 / K09 / R3 / M09 | alta |  |
| S38 | Maquinaria y equipo | 28 | sí | E2 / K09 / R3 / M10 | alta |  |
| S39 | Electrónica y equipo eléctrico (incluye cables) | 26,27 | sí | E2 / K09 / R3 / M10 | media | los arneses pueden clasificarse en 27 o en 29: ver docs/taxonomia.md |
| S40 | Autopartes y vehículos | 29 | sí | E2 / K09 / R3 / M10 | alta | maquila de autopartes |
| S41 | Otro equipo de transporte y astilleros | 30 | sí | E2 / K09 / R3 / M10 | alta |  |
| S42 | Joyería, deportes y manufacturas diversas | 32 | sí | E2 / K09 / R3 / M11 | alta |  |
| S43 | Reparación e instalación de maquinaria | 33 | no | E2 / K09 / R3 / M11 | alta |  |
| S44 | Electricidad, gas y vapor | 35 | no | E3 / K10 / R4 / M12 | alta | la exportación de energía eléctrica (HS 271600) se excluye del comercio |
| S45 | Agua, saneamiento y remediación | 36,37,39 | no | E3 / K10 / R4 / M12 | alta |  |
| S46 | Gestión de residuos y reciclaje | 38 | no | E3 / K10 / R4 / M12 | alta |  |
| S47 | Construcción | 41,42,43 | no | E4 / K06 / R5 / M13 | alta |  |
| S48 | Comercio mayorista | 46 | no | E5 / K04 / R6 / M14 | alta |  |
| S49 | Comercio minorista y de vehículos | 45,47 | no | E5 / K05 / R6 / M14 | alta |  |
| S50 | Transporte terrestre y por tuberías | 49 | no | E6 / K12 / R6 / M15 | alta |  |
| S51 | Transporte acuático y aéreo | 50,51 | no | E6 / K12 / R6 / M15 | alta | hidrovía |
| S52 | Almacenamiento, logística y correos | 52,53 | no | E6 / K12 / R6 / M15 | alta |  |
| S53 | Alojamiento y gastronomía | 55,56 | no | E5 / K12 / R6 / M16 | alta |  |
| S54 | Agencias de viaje y turismo | 79 | no | E6 / K12 / R6 / M16 | alta | separado de S53 porque EPHC lo agrupa en otra rama |
| S55 | Telecomunicaciones | 61 | no | E6 / K12 / R6 / M17 | alta |  |
| S56 | Software, informática y servicios de información | 62,63 | no | E7 / K12 / R6 / M17 | alta |  |
| S57 | Edición, audiovisual y medios | 58,59,60 | no | E8 / K12 / R6 / M17 | media |  |
| S58 | Finanzas y seguros | 64,65,66 | no | E7 / K11 / R6 / M18 | alta |  |
| S59 | Servicios inmobiliarios | 68 | no | E7 / K01 / R6 / M19 | alta |  |
| S60 | Servicios profesionales, científicos y técnicos | 69,70,71,72,73,74,75 | no | E7 / K12 / R6 / M20 | alta |  |
| S61 | Servicios administrativos y de apoyo a empresas | 77,78,80,81,82 | no | E7 / K12 / R6 / M20 | alta |  |
| S62 | Administración pública y defensa | 84 | no | E8 / K02 / R6 / M21 | alta |  |
| S63 | Educación | 85 | no | E8 / K12 / R6 / M21 | alta |  |
| S64 | Salud y asistencia social | 86,87,88 | no | E8 / K12 / R6 / M21 | alta |  |
| S65 | Arte, recreación y deportes | 90,91,92,93 | no | E8 / K12 / R6 / M16 | alta |  |
| S66 | Otros servicios personales y de reparación | 94,95,96,97,98 | no | E8 / K12 / R6 / M21 | media |  |

## Puntos que necesitan tu criterio
1. **Cantidad.** Son 66, por encima del rango 40-60 del documento técnico. Si querés reducir: juntar S50-S52 (transporte y logística), S63-S64 (educación y salud) y S59/S60, o S10-S13 (lácteos y molinería). Aumentar es fácil; juntar pierde detalle.
2. **Biocombustibles.** La CIIU no tiene una clase propia para biodiésel o bioetanol (caen en 1101, 1920 o 2029 según el caso). Como el documento los usa como caso de validación, conviene definir cómo identificarlos (¿por producto HS, p. ej. 3826 y 2207?). Hoy quedan repartidos entre S15, S27 y S29.
3. **Arneses de maquila.** Pueden clasificarse en CIIU 27 (cables, S39) o en 29 (partes de vehículos, S40). Como son el ejemplo central del documento, hay que decidir en qué sector se miden; propongo S40 y que el puente HS lo fije por producto.
4. **Servicios y construcción.** Quedan fuera del espacio producto. Se usarán en el módulo territorial y en las cuentas nacionales, no en el modelo de comercio.
5. **Minería (S08).** La EPHC no la muestra como rama: queda `SIN_GRUPO` hasta tener el clasificador del INE. El mapa MIC la trae como "Canteras y áridos".
6. **Agricultura.** La separación S01-S05 sigue lo que permiten crédito y cuentas regionales (ganadería aparte). La agricultura mixta (015) se agrupa con los servicios agropecuarios (S05).
7. **Supuestos de mapeo.** Los grupos de cada sector dependen de los supuestos marcados con confianza media en `clasificaciones_locales.py` (por ejemplo, dónde cae edición y audiovisual en la EPHC). Si algún supuesto está mal, el sector puede quedar cruzando grupos; la prueba lo detecta.

## Qué sigue
Con tu aprobación (o tus cambios), esta taxonomía es la base del puente HS → CPC → CIIU → sector (tarea 0.5). Se completa la columna CNAEP cuando llegue el clasificador del BCP.
