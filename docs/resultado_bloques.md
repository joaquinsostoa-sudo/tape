# Bloques de productos × dotaciones (2015)

**Descriptivo, sin controles de causalidad.** Código: `src/modelos/bloques_dotaciones.py`; figura: `docs/figuras/bloques_dotaciones_2015.png`; tabla completa: `data/model/bloques_dotaciones_2015.csv`;
países y terciles: `data/model/bloques_paises_2015.csv`. Pedido de Joaquín: resumir con un cuadro lo que explican las dotaciones.

## Cómo se hizo
- **Muestra:** 144 países (D8) en 2015. **Ventaja** en un bloque = RCA del bloque ≥ 1, con el comercio mundial y sin la energía binacional. Número de países con ventaja: primarios agropecuarios 88, manufacturas agropecuarias 71, minerales y energía 69, liviana 49, manufacturas de minerales 38, pesada y de tecnología media 34, alta tecnología 17.
- **Bloques:** la clasificación tecnológica de Lall (2000) llevada a HS4 (`docs/clasificacion_lall.md`), en siete bloques para el cuadro (los seis anteriores, con la manufactura pesada y media tecnología aparte de la alta).
- **Dotaciones:** tierra cultivable, agua dulce, reservas de petróleo, de gas, de carbón y de minerales, capital humano, capital por trabajador (tercil bajo = trabajo abundante), electricidad barata y logística (LPI); el PIB per cápita va como referencia.
- **Terciles** entre los países de la muestra con dato. Con más de un tercio de ceros (las reservas), «bajo» = sin reservas y el resto se parte por la mediana.
- **Cada celda:** diferencia, en puntos porcentuales, entre el % de países con ventaja en el tercil alto de la dotación y en el bajo; el punto indica p < 0,05 (Fisher). El segundo panel compara países por encima y por debajo de la mediana de la dotación **dentro de cada tercil de ingreso** y promedia; cada celda tiene pocos países (unos 14), así que es ruidoso.

## Qué se lee
| Dotación | Bloque donde más se nota | Diferencia (alto − bajo) | Dentro de terciles de ingreso |
|---|---|---|---|
| Tierra cultivable | Primarios agropecuarios | +40 pp (42 % → 81 % de los países) | +32 |
| Agua dulce | Primarios agropecuarios | +22 | +23 |
| Reservas de petróleo | Minerales y energía | +52 (28 % → 80 %) | +32 |
| Reservas de gas | Minerales y energía | +50 | +27 |
| Reservas de minerales (USGS) | Minerales y energía y primarios agropecuarios | +26 y +26 | +17 y +8 |
| Electricidad barata | Minerales y energía | +36 | +26 |
| Capital humano | Manufactura pesada y tec. media | +45 (7 % → 52 %) | +23 |
| Capital por trabajador | Manufactura pesada y tec. media | +43 | +55 |
| Logística (LPI) | Manufactura pesada, alta tecnología | +45 y +30 | +30 y +22 |

- **Recursos → bloques de recursos.** Tierra y agua con primarios agropecuarios, petróleo y gas con minerales y energía; son diferencias grandes, significativas y que **se mantienen dentro de cada nivel de ingreso**. Los países con muchas reservas de energía tienen menos ventaja en manufacturas agropecuarias y livianas (−20 a −33 pp), reflejo de la «enfermedad holandesa» y del ingreso.
- **Capacidades → manufactura pesada y de tecnología media y alta.** Capital humano, capital por trabajador y logística se asocian con ventaja en estos bloques, pero **también el PIB per cápita (+45)**: sin controlar por ingreso no se separan. Dentro de terciles de ingreso, el capital por trabajador y la logística siguen asociados con la manufactura pesada (+55 y +30), con la advertencia de que cada celda es ruidosa.
- **Manufactura liviana: sin patrón claro.** No hay gradiente en capital por trabajador (35 %, 35 % y 35 % de los países en los terciles bajo, medio y alto): «trabajo abundante» no explica por sí solo la ventaja en manufactura liviana. La logística muestra +19 pp (+31 dentro de ingreso), un patrón que no coincide con el esperado.
- **Electricidad barata:** se asocia con minerales y energía (+36), y **negativamente** con la manufactura pesada (−17): los países con electricidad barata (hidro, petróleo) son los de recursos, no los de manufactura.
- **Segundo panel, con cuidado:** algunos signos cambian respecto del primero (capital humano y primarios agropecuarios pasa de −21 a +24; capital por trabajador con manufactura liviana de 0 a +36). Con unos 14 países por celda, esas diferencias no deben leerse como resultados.

## Paraguay (2015)
- **RCA por bloque:** primarios agropecuarios **13,0** (tercero del mundo), manufacturas agropecuarias 1,65 (con ventaja); liviana 0,47; pesada y tec. media 0,15; manufacturas de minerales 0,20; minerales y energía 0,11; alta tecnología 0,02.
- **Terciles:** **alto** en tierra cultivable, agua dulce y electricidad barata; **bajo** en reservas de petróleo, gas, carbón y minerales; **medio** en capital humano, capital por trabajador, logística y PIB per cápita.
- **Lectura:** el perfil exportador de Paraguay encaja con sus dotaciones de recursos (tierra y agua altas, ventaja enorme en primarios agropecuarios). No tiene ventaja en manufactura pesada ni en alta tecnología, y sus capacidades (capital humano, capital por trabajador, logística) están en el tercil medio, justo donde la asociación con esos bloques es débil.

## Límites
- Un solo año (2015) y un corte transversal; las dotaciones de recursos y la electricidad barata son características casi fijas del país.
- Los terciles de reservas son «con» o «sin» reservas más una división de los que tienen. Los minerales del USGS son una foto de 2023-2025 y solo informan los principales productores.
- La clasificación de Lall es de 2000 y los bloques son una decisión del equipo; hay productos con confianza media o baja (`docs/clasificacion_lall.md`).
- Es un resumen de la asociación entre dotación y ventaja revelada, no una prueba: las regresiones con efectos fijos (`docs/resultado_presente.md`) son la versión controlada.
