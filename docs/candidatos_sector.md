# Sectores candidatos de Paraguay (D1, opción a), año de corte 2024

Código: `src/modelos/candidatos_sector.py` (`uv run python -m src.modelos.candidatos_sector`). Salidas en `data/model/` (no versionadas): `candidatos_sector_PRY_2024.csv` y `candidatos_producto_PRY_2024.csv`.

## Cómo se calcula
1. **Modelo por producto** (el de la tarea 1.11): logit con la densidad y efectos fijos de país, de producto y de ventana, entrenado con las ventanas de resultado conocido (2000, 2005, 2010 y 2015) y la tabla de exportaciones depurada (alcance a de D6).
2. **Candidatos de Paraguay en 2024:** 1.132 productos HS4 con RCA < 0,5 y sin presencia sostenida. La densidad usa los 5 años que terminan en 2024 (D3). 109 productos no son candidatos (Paraguay ya los exporta con ventaja o con RCA ≥ 0,5).
3. **Del producto al sector (D1 a):** la puntuación del sector es la **media de las puntuaciones de sus productos candidatos, ponderada por el comercio mundial del producto**; el peso de un HS4 en un sector es la fracción de su valor mundial que el puente HS → sector asigna a ese sector. Respaldo: el **máximo** (producto líder) y el **conteo** de productos del sector entre los 100 mejores candidatos de Paraguay. Se excluyen los sectores sin comercio de bienes según la taxonomía (finanzas, almacenamiento, impresión, agua y electricidad), a los que el puente asigna algún HS suelto (por ejemplo 4907, billetes y sellos).

**Las puntuaciones ordenan; no son probabilidades.** Van de 0,0003 a 0,0675 (mediana 0,009): la calibración del modelo es deficiente en los extremos (`docs/resultado_backtest.md`) y por D16 se leen como «qué tan cerca está», no como «chance de ocurrir».

## Los 15 sectores mejor puntuados
| # | Sector | Puntaje medio | Máximo (producto líder) | En el top 100 | Candidatos / productos del sector |
|---|---|---|---|---|---|
| 1 | Cemento, hormigón y prefabricados | 0,039 | 0,068 (2523 cemento) | 1 | 10 / 10 |
| 2 | Tabaco | 0,032 | 0,036 (2403) | 2 | 2 / 3 |
| 3 | Petróleo refinado y combustibles | 0,029 | 0,032 (2710) | 1 | 9 / 9 |
| 4 | Avicultura y porcicultura | 0,022 | 0,032 (3101 abonos animales) | 3 | 7 / 7 |
| 5 | Ganadería bovina y otras especies | 0,022 | 0,032 (3101) | 5 | 15 / 17 |
| 6 | Molinería (trigo, maíz y otros) | 0,020 | 0,041 (1103 sémolas) | 4 | 7 / 9 |
| 7 | Panificados | 0,019 | 0,019 (1905) | 0 | 1 / 1 |
| 8 | Bebidas, alcohol y agua envasada | 0,015 | 0,039 (2202 aguas) | 2 | 8 / 8 |
| 9 | Azúcar | 0,014 | 0,014 (1702) | 0 | 1 / 3 |
| 10 | Cultivos anuales | 0,014 | 0,046 (1008 cereales) | 3 | 29 / 38 |
| 11 | Textiles e hilandería | 0,013 | 0,041 (5805) | 10 | 90 / 100 |
| 12 | Confecciones | 0,012 | 0,026 (6113) | 2 | 39 / 45 |
| 13 | Alimentos balanceados y para mascotas | 0,012 | 0,012 (2309) | 0 | 2 / 2 |
| 14 | Pesca y acuicultura | 0,011 | 0,025 (7116) | 1 | 14 / 16 |
| 15 | Silvicultura y extracción de madera | 0,011 | 0,026 (0810) | 1 | 8 / 10 |

## Los productos mejor puntuados
Cemento (2523, 0,068), plomo (7806, 0,051), vidrio (7001, 0,051), plásticos n.c.p. (3915, 0,050), aceites vegetales (1508, 0,048), cereales (1008, 0,046), otros productos vegetales (1404, 0,046), embarcaciones (8908 y 8904, 0,044 a 0,046), fibras (5505), maquinaria de perforación (8430), metales (7112), contenedores (8609), tapices (5805), sémolas (1103), cinc (7902) y harinas (1102).

## Cómo leerlo (y lo que no dice)
- **La media por sector es sensible al tamaño y a la composición del sector:** los sectores con pocos productos (panificados: 1; tabaco: 2 candidatos) salen arriba por un solo producto. Por eso el máximo, el conteo en el top 100 y el número de candidatos van al lado. Los sectores que combinan una media alta con varios productos en el top (por ejemplo ganadería, molinería o textiles con 5, 4 y 10 productos) son los más robustos.
- **Efectos del puente y de la depuración que hay que revisar:** el sector 3 (petróleo refinado) refleja reexportaciones de derivados que la depuración solo marca parcialmente; productos como 3101 (abonos animales) y 7116 (manufacturas de perlas) están asignados a sectores por el puente HS de forma poco intuitiva (ganadería, pesca).
- **No contempla brechas ni valor:** esto es solo cercanía (densidad con efectos de producto). Qué falta (límites duros y brechas, `docs/mapa_brechas.md`) y cuánto valdría el sector (PCI, salario, encadenamientos; Fase 3) se cruzan después.
- El orden depende de un solo año de corte (2024) y de un solo modelo; la sensibilidad (otros cortes, HS6, tabla bruta) no está hecha.
