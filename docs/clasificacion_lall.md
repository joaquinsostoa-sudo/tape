# Clasificación de productos de Lall (2000) en HS4

**Para qué sirve:** agrupar los productos exportados en bloques comparables (primarios, basados en recursos, manufactura liviana, media y alta tecnología) y
cruzarlos con las dotaciones de los países. Archivo: `data/clean/clasificacion_lall_hs4.csv` (1.239 productos HS4 con clase, bloque y confianza por fila).

## De dónde sale
- **Lista:** Lall, S. (2000), QEH Working Paper 44, Anexo, Tabla 1: 230 códigos SITC Rev.2 de 3 dígitos en diez subgrupos. No existe como datos: se lee del PDF por la posición de las
  tres columnas de cada página (`leer_lall`), con control: 230 códigos únicos y verificaciones puntuales contra el documento (por ejemplo, 764 en alta tecnología 1, 781 en media tecnología 1).
- **Puente a HS92:** SITC Rev.2 de 4 dígitos → SITC Rev.3 → HS92 de 6 dígitos con las conversiones del Atlas (cada código de origen suma 1). El voto de cada clase para un HS6
  es la suma de los productos de los dos pesos; se agrega a HS4 con el valor mundial de cada HS6. **Confianza por fila:** alta (la clase ganadora reúne al menos 0,8 de lo clasificado), media (0,5 a 0,8), baja (menos de 0,5).

## Clases y bloques
Doce clases: los diez subgrupos de Lall, con los primarios (PP) y las basadas en recursos «otras» (RB2) divididos entre agro y minerales y energía. Seis bloques para el cuadro de dotaciones
(decisión de presentación, no de Lall): primarios agropecuarios; minerales y energía (primarios minerales, combustibles, metales no ferrosos y minerales metálicos); manufacturas agropecuarias;
manufacturas de minerales (química básica, cemento, vidrio); manufactura liviana (textil, confección, calzado y otras de tecnología baja); manufactura pesada y de tecnología media;
manufactura de tecnología alta.

| Bloque | Productos HS4 |
|---|---|
| Manufactura liviana | 317 |
| Manufactura pesada y de tecnología media | 282 |
| Manufacturas de minerales | 151 |
| Primarios agropecuarios | 141 |
| Manufacturas agropecuarias | 132 |
| Minerales y energía | 119 |
| Manufactura de tecnología alta | 78 |
| Sin clasificar (no están en la lista de Lall: oro no monetario, transacciones especiales) | 19 |

Confianza del bloque: alta en 1.079 productos, media en 133 y baja en 27.

## Controles y límites
- **Control puntual:** soja (1201) y carne bovina (0201) → primarios agropecuarios; petróleo crudo (2709) y mineral de hierro (2601) → minerales y energía; automóviles (8703) → media tecnología;
  telefonía (8517) → alta tecnología; tejidos de punto (6109) → liviana; oro (7108) → sin clasificar, como excluye Lall.
- **Dudas conocidas:** medicamentos (3004) quedan en media tecnología de proceso con confianza media, mientras que Lall pone los farmacéuticos (SITC 541) en alta tecnología; el arnés de cables
  (8544) queda en media tecnología de ingeniería con confianza media. Son efectos del paso entre revisiones del SITC, y por eso la tabla lleva la confianza por fila.
- **La clasificación de Lall es de 2000:** pensada para exportaciones de manufacturas; los primarios y los minerales se agrupan de forma gruesa, y las categorías de «tecnología» no recogen la
  heterogeneidad actual dentro de cada producto.
- **Las reglas de los bloques** (por ejemplo, qué RB2 cuenta como minerales) son decisión del equipo, por revisar.
