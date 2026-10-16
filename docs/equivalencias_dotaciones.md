# Equivalencias entre las dotaciones nacionales y los datos por distrito

Fecha: 2026-10-16. Estado: **inventario y propuesta** (no se construyó nada nuevo; las decisiones están pendientes de Joaquín). Capital humano ya está hecho (D27 a D32).

## En palabras simples
En el modelo nacional (M1) cada país tenía cuatro «dotaciones»: **energía** (precio de la electricidad), **capital físico** por trabajador, **crédito** sobre el PIB y **logística** (índice LPI), más el capital humano. Para el territorio hay que ver **qué dato equivalente existe a nivel de distrito o departamento**. Esta tabla dice, capa por capa, qué hay, con qué cobertura y **si el concepto cambia** (por ejemplo, de «precio de la energía» a «potencia disponible»). La regla del proyecto es no desagregar artificialmente: cada dato entra en su nivel nativo.

## La tabla
| Capa | Dato nacional (M1) | Equivalente distrital o departamental | Cobertura | ¿Cambia el concepto? | Confianza |
|---|---|---|---|---|---|
| **Energía** | Precio de la electricidad (Doing Business 2014-2019) | **Potencia disponible (MW)** en las subestaciones, 2025-2033 (mapa MIC): 104 subestaciones en 74 distritos; en 2026 hay 1.705 MW disponibles en 69 distritos y, de 2026 a 2033, siempre entre 69 y 71 distritos; los MW totales suben a 1.963 en 2028 y bajan a 1.424 en 2033 (2025, 2029 y 2030 traen una sola de las dos redes y no son comparables). También la **distancia a la subestación de 220 kV** más cercana (38 de 104 son de 220 kV o más) | 74 de 263 distritos tienen subestación; con proximidad (D30) se cubren todos | **Sí**: de *precio* a *disponibilidad*. No hay precio por distrito (no se verificó si la tarifa varía por distrito) | Media |
| **Logística** | LPI (1 a 5) | (a) **Distancia a aduanas, puertos y pasos de frontera**: 35 puntos en 18 distritos, con exportaciones por punto (USD 10.840 millones en total); (b) **km de ruta nacional** en el distrito: 22 rutas, 199 de 263 distritos con ruta (mediana 22 km); (c) distancias a Asunción, Ciudad del Este, Encarnación y Puerto Central (263 de 263) | 263 distritos | **Sí**: de *desempeño percibido* a *acceso físico*. Distancia en línea recta, no tiempo de viaje | Media-alta |
| **Capital físico** | Capital real por trabajador (Penn World Table) | **No hay equivalente directo.** Proxies indirectos: aglomeración (17.080 industrias del MIC en 242 distritos; establecimientos del Censo Económico 2011), PIB regional por rama (18 departamentos, 2021-2024) y PEA | Distrito (aglomeración) y departamento (PIB) | **Sí, mucho**: un proxy de actividad, no de capital | Baja |
| **Crédito** | Crédito privado / PIB (WDI) | **Ninguno territorial**: el BCP publica el crédito por sector y por banco, no por departamento ni distrito | — | — | Sin dato |
| **Capital humano** | Años de estudio (Penn World Table) | **Hecho**: base (escolaridad, salud, graduados transversales), formación específica por sector, proximidad y diagnóstico (D27 a D32) | 263 distritos | Sí (D29) | Media |
| **Recursos** (límite duro en el mapa de brechas) | Reservas de carbón, gas y petróleo (nacionales); minerales (USGS) | **Fincas y superficie agropecuaria** por distrito (Censo Agropecuario 2022: fincas, superficie, superficie media y fincas por 1.000 habitantes). Las reservas minerales y energéticas existen solo a nivel nacional | 263 distritos (agro) | Solo agro | Media (agro) |
| **Mercado local** (no estaba en M1) | — | Población y PEA 2022 (263 distritos) | 263 | Capa nueva | Alta |
| **Conectividad digital** | — | Internet en establecimientos educativos: solo 2012 a 2016 y con valores incompletos | — | — | **No sirve** (se descarta) |

## Del lado del bien: los requisitos ya existen
Para cada capa, el bien (producto o sector) ya tiene un **requisito** calculado en la Fase 1: energía (intensidad energética, NBER-CES), capital (intensidad de capital, NBER-CES), habilidades (D28) y **valor/peso** (si es un bien pesado, la logística pesa más). Con eso se puede usar el mismo esquema que en capital humano: *¿el bien exige esta capa?* (requisito sobre la mediana) y, si la exige, **diagnóstico frente a los distritos que ya producen** (D31), con proximidad (D30) cuando corresponda.

## Lo que esto implica
- **Energía y logística son las más sólidas** y las más útiles como diagnóstico (límite duro: un distrito sin potencia disponible cerca no puede alojar una industria que consume mucha energía).
- **Capital físico y crédito no tienen equivalente territorial**; quedan como indicadores nacionales o por departamento, y se informa que no se pueden diagnosticar por distrito.
- **La potencia disponible es estable en número de distritos (69 a 71) pero cambia en cantidad**: 1.705 MW en 2026, 1.963 en 2028 y 1.424 en 2033. En 2026 los mayores son Asunción (323 MW), Lambaré (214), Valenzuela (137), Ciudad del Este (104) y Villeta (81). **Los años 2025, 2029 y 2030 traen una sola de las dos redes**, así que conviene medir con 2026 (o promediar 2026 a 2028) y no con un año suelto. En la red de 220 kV y 66 kV, 77 de las 104 subestaciones tienen potencia disponible cero en 2025 y 37 tienen alguna en 2026.

## Qué falta decidir
1. Qué capas construir y en qué orden.
2. Para energía: usar la potencia disponible (disponibilidad), la distancia a la subestación o ambas; y con qué año (propongo 2026, o el promedio de 2026 a 2028).
3. Para logística: qué medidas incluir (aduanas y puertos, ruta nacional, distancias a polos).
4. Para capital físico: incluir un proxy débil (aglomeración y PIB departamental) o dejarlo afuera.
