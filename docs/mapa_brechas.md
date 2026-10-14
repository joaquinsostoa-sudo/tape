# Mapa de brechas de compatibilidad (Paraguay, 2019)

Código: `src/modelos/mapa_brechas.py` · salidas: `data/model/mapa_brechas_PRY_2019.csv` (una fila por producto HS4), `mapa_brechas_tolerancias_PRY_2019.csv`, `mapa_brechas_validacion_2019.csv`.
Descriptivo: no prueba que cerrar una brecha lleve a producir.

## Cómo se construye
1. **Posición** de cada país en cada dotación: percentil (0–100) entre los 147 países de la muestra D8 de 2019.
2. **Referencia** por producto y dotación: mediana del percentil de los productores (presencia D13), sin el propio país; dos versiones: **todos** los productores e **ingreso similar** (mismo tercio de PIB per cápita; con menos de 5 productores se usa la de todos y se marca).
3. **Brecha** = max(0, referencia − posición). **Índice** = promedio de las brechas con dato (mínimo 9 de 12 dotaciones). **Cuello de botella** = dotación de mayor brecha.
4. **Tolerancia** por dotación y por bloque de Lall: percentil 75 de las brechas entre pares país-producto que **ya producen** (países del tercio de ingreso de Paraguay), piso de 5 puntos. Variante «solo propios»: calibrada solo con lo que Paraguay ya exporta.
5. **Ámbitos**: todos los productos, o solo los **cercanos no exportados** (RCA < 0,5 y densidad en el cuartil superior de los no exportados: 277 de 1.107).

## Dos versiones del índice
| | dotaciones | compatibles entre los 277 cercanos (todos / ingreso similar) | compatibles entre lo que Paraguay YA exporta |
|---|---|---|---|
| 8 dotaciones (sin reservas), tolerancia global | capital humano, K/trabajador, LPI, electricidad, salario, impuesto, tierra, agua | 209 / 206 | no medido |
| 12 dotaciones (con reservas de petróleo, gas, carbón y minerales), tolerancia por bloque | las 8 + 4 de reservas | **17 / 12** | **5 % / 6 %** |

**Control de sensatez que falla:** con 12 dotaciones y la regla «ninguna dotación fuera de tolerancia», solo el 5 % de las exportaciones actuales de Paraguay sería «compatible». La regla es demasiado dura (Paraguay no tiene reservas y las reservas son el cuello de botella en 133 de 277 productos cercanos, sobre todo por carbón) y no sirve tal cual. Con 8 dotaciones el umbral deja pasar casi todo, incluidos minerales metálicos que Paraguay no puede producir (aluminio, manganeso, uranio). Ninguna de las dos versiones es satisfactoria; falta decidir cómo tratar las reservas (ver abajo).

## Validación (país dejado afuera, AUC por país, 147 países)
| puntaje | AUC medio | AUC Paraguay |
|---|---|---|
| densidad | 0,891 | 0,860 |
| −índice (todos) | 0,660 | 0,710 |
| −índice (ingreso similar) | 0,634 | 0,595 |
| logit densidad + índice (todos) | 0,890 | 0,857 |
| logit densidad + índice (ingreso similar) | 0,890 | 0,857 |

(Con 8 dotaciones: densidad + índice 0,894, +0,003.) El índice por sí solo ordena mejor que el azar (0,63–0,66) pero **no agrega nada a la densidad**: sirve como diagnóstico de brechas, no como ranking de candidatos.

## Pendiente de decisión
Cómo entran las reservas: (A) fuera del índice general y solo como filtro de viabilidad para los bloques de recursos (minerales y energía, primarios); (B) dentro, con regla de grado (posición relativa frente a la distribución de los pares que ya producen) en vez de «ninguna fuera de tolerancia»; (C) 8 dotaciones y marcar aparte los productos de recursos naturales sin reservas.

## Segunda versión: relevancia revelada, límite duro y exceso (`src/modelos/mapa_limites.py`)
Declarada en `docs/supuestos.md` antes de correr (2026-10-14). Resultado: control de sensatez cumplido (78 % de las exportaciones actuales de Paraguay compatibles; 195 de 277 cercanos compatibles; 18 con límite duro). El déficit ponderado no mejora la densidad (AUC 0,887 contra 0,891). **La hipótesis del exceso no se cumple**: el coeficiente es positivo (+0,17; tierra sola +0,69), el contrario del declarado. Pendiente: reservas del mineral específico de cada producto.
Estado final de cada producto (`estado` en `mapa_limites_especifico_PRY_2019.csv`): compatible, déficit alto, límite duro o sin dato confiable de reservas. Figura: `docs/figuras/mapa_limites_PRY_2019.png`. Alerta abierta: seda y semillas oleaginosas quedan con límite duro por el carbón (correlación entre dotaciones).
