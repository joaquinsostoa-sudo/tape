# Matcheo del capital humano para un bien cercano y más complejo que aún no se produce

Fecha: 2026-10-16. Código: `src/puentes/matcheo_bien_nuevo.py` (8 pruebas en `tests/test_matcheo_bien_nuevo.py`). Regla declarada antes de implementar: D32 en `docs/supuestos.md`.
Salidas (en `data/model/`): `matcheo_8430.csv`, `matcheo_2202.csv` y sus `*_sensibilidad.csv`.

**Resultado en una línea: la regla C funciona mecánicamente tal como se declaró, pero con los dos ejemplos elegidos NO es informativa, porque los vecinos del bien no son afines a él.** Se registra tal cual y no se cambió la regla.

## Qué hace la regla (D32)
Un bien que todavía no se produce no tiene productores de referencia, así que:
1. Se toman como **vecinos** los 5 productos que Paraguay ya exporta más próximos al bien (por φ).
2. La **referencia** son los distritos con industrias del mapa MIC en el sector de algún vecino.
3. El **peldaño** es cuánto más exige el bien que sus vecinos (percentil del requisito de habilidades del NBER entre 1.099 productos).
4. El **umbral** es el percentil 10 de la referencia (base y formación específica del sector del bien); a la formación específica se le suma el peldaño.
5. Las categorías son las de D31 (lista, falta formación específica, falta base, faltan ambas) y se cruzan con la **densidad** (qué parte de los bienes relacionados ya produce el distrito) para decir si es candidato, qué desarrollar, capacidad sin uso o no es candidato.
6. Sensibilidad: **B** (sin peldaño), **A** (requisito propio del bien), escalas de 15 y 60 km y reparto parejo.

## Los dos ejemplos
| | 8430 Maquinaria de perforación y excavación | 2202 Aguas con azúcar añadida |
|---|---|---|
| Sector del bien / NBER | S39 Maquinaria y equipo / 0,353 (exige) | S19 Bebidas / 0,319 (exige) |
| Vecinos (producto, φ, sector) | cereales (0,38, S01), papel (0,31, S26), artículos de cuero (0,30, S43), madera (0,30, S24), huesos y subproductos (0,29, S47) | chatarra de hierro (0,57, S47), chatarra de aluminio (0,56, S47), plásticos (0,55, S32), plomo (0,53, S37), chatarra de cobre (0,52, S47) |
| Peldaño | bien en el percentil 68 y vecinos en el 22: **+45,8 puntos** (4 vecinos con dato) | bien en el 58 y vecinos en el 41: **+17,3 puntos** (2 vecinos con dato) |
| Distritos de referencia | **230 de 263** | 127 |
| Umbrales (base / formación) | 14 / 58 | 15 / 30 |

Categorías (regla C, 30 km, sede principal) y cruce con la densidad:

| | 8430 | 2202 |
|---|---|---|
| Lista | 107 | 178 |
| Falta formación específica | 119 | 44 |
| Falta base | 4 | 6 |
| Faltan ambas | 32 | 34 |
| **Candidato** (densidad alta y lista) | 59 | 99 |
| **Qué desarrollar** (densidad alta, sin lista) | 73 | 33 |
| **Capacidad sin uso** (densidad baja y lista) | 48 | 79 |
| **No es candidato** | 82 | 51 |

Sensibilidad (distritos que cambian de categoría frente al principal):

| Variante | 8430 | 2202 |
|---|---|---|
| Regla B (sin peldaño) | **120** | 45 |
| Regla A (requisito propio del bien) | **155** | 131 |
| Escala de 15 km | 50 | 46 |
| Escala de 60 km | 24 | 23 |
| Reparto parejo entre sedes | 34 | 31 |

## Por qué no es informativo
1. **Los vecinos no tienen que ver con el bien.** Paraguay no exporta nada parecido a la maquinaria de perforación, así que lo «más cercano» son cereales, papel, cuero y madera, con una cercanía débil (φ de 0,29 a 0,38). Para las aguas con azúcar, los vecinos son chatarras y metales.
2. **La referencia es casi todo el país** (230 de 263 distritos para 8430): los sectores de esos vecinos son muy comunes, y el percentil 10 de «casi todos» es un umbral de base de 14, que casi cualquier distrito pasa.
3. **El resultado depende del peldaño.** Con el peldaño en 46 puntos, 120 distritos cambian de categoría entre las reglas B y C; con el requisito propio (A) cambian 155. El peldaño no se puede calibrar (cuánto más capital humano pide un bien más complejo).
4. **No es un problema de estos dos casos.** Entre los 137 candidatos «cercano y sube» con requisito y sector, la cercanía media de los 5 vecinos tiene mediana 0,44 (de 0,38 en el cuartil inferior a 0,51 en el superior), y la referencia mediana es de **150 distritos**: solo 43 candidatos tienen una referencia de entre 10 y 120 distritos. Los bienes con vecinos afines (por ejemplo prendas de vestir, φ de 0,6 a 0,7 con otras prendas) son simples en el NBER (0,2 a 0,3), así que no «suben» en capital humano. **Una cosa es que el bien suba en complejidad económica (PCI) y otra que exija más personal calificado (NBER); no coinciden.**

## Qué falta decidir
Opciones, sin cambiar nada hasta que Joaquín elija (cualquier cambio se declara antes de usarlo):
1. **Exigir una calidad mínima de vecinos:** el matcheo solo se aplica si, por ejemplo, la cercanía media de los vecinos es al menos 0,5 y la referencia está entre 10 y 120 distritos; el resto queda como «sin vecinos confiables». Deja pocos bienes.
2. **Cambiar la referencia:** en vez de «cualquier distrito que produce un sector vecino», tomar los distritos con mayor densidad de bienes relacionados (por ejemplo, el cuartil superior de la densidad). Más selectivo.
3. **Dejarlo como mecánica y no como resultado:** usar la regla solo cuando los vecinos sean afines y mostrar siempre el requisito propio del bien (regla A) y el peldaño por separado.
4. **Elegir otros bienes de ejemplo** que cumplan una calidad mínima de vecinos.

## Límites
- «Aún no se produce» es a nivel de exportaciones por producto; el mapa MIC es una foto de 2026 y todos los sectores de manufactura tienen industrias.
- La densidad solo ve la manufactura (el MIC no cubre agro ni servicios), por eso los vecinos agropecuarios no cuentan en ella.
- El enlace producto → sector → distritos es grueso. Pocos vecinos con dato del NBER (4 de 5 y 2 de 5).
- Es un diagnóstico y no una recomendación de localización; resultados como asociación, no causalidad.
