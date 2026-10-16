# Capital humano específico: carreras → sectores, títulos por sector × distrito y exigencia de formación

Fecha: 2026-10-16. Código: `src/puentes/carrera_sector.py` y `src/puentes/exigencia_sector.py` (11 pruebas en `tests/test_carrera_sector.py` y `tests/test_exigencia_sector.py`). Reglas declaradas antes de construir: D27 (versión final) y D28 en `docs/supuestos.md`, con las decisiones de Joaquín.
Salidas (en `data/clean/`, sin datos personales): `puente_carrera_sector.csv`, `titulos_sector_distrito.csv`, `titulos_distrito.csv` y `exigencia_formacion_sector.csv`.

## En palabras simples
Una carrera no «pertenece» a un sector: forma gente que trabaja en uno o varios. Para poder decir «en este distrito hay X graduados disponibles para el sector Y» hicimos dos pasos que se pueden revisar:
1. **Carrera → campo de estudio** (por ejemplo «Ingeniería Agronómica» → *agronomía y producción*). Son 52 campos, cada uno con su código CINE-F aproximado.
2. **Campo → sectores TAPE.** Agronomía sirve a cinco sectores agropecuarios; enfermería, a salud.

Las decisiones de Joaquín que definen el cruce:
- **Cuenta completa:** si un campo sirve a varios sectores, **cada título cuenta entero en cada uno**. Se mide cuántos trabajadores calificados están *disponibles* para un sector, no cuántos trabajan efectivamente en él. Consecuencia: **los sectores no se pueden sumar entre sí** (un agrónomo aparece en cinco). Para totales hay una tabla aparte, `titulos_distrito.csv`, donde cada título cuenta una sola vez.
- **Base transversal:** derecho, contabilidad, auditoría, economía, administración de empresas y marketing (22,5 % de los títulos) **no van a ningún sector**. Suman al total del distrito y del departamento. Cada una guarda, solo como información, el sector de servicios al que iría si algún día se mapean los servicios.
- **Niveles:** el indicador de formación específica usa **técnico y grado**. Docente, especialización, maestría y doctorado se guardan aparte.
- **Exigencia de formación (D28):** un sector de manufactura «exige formación específica» si su requisito de habilidades del NBER es **≥ 0,28**.

## Control del cruce
| Qué se mide | Resultado |
|---|---|
| Títulos clasificados (campo asignado) | **99,9 %** (778 títulos de 242 carreras sin clasificar, casi todos títulos extranjeros en portugués). Meta de D27: 95 % |
| Base transversal | 22,5 % de los títulos |
| Confianza de la carrera (% del total) | alta 81,5 %; media 17,8 %; baja 0,7 % |
| Total en `titulos_distrito.csv` | 688.161 en cada escenario de sede (cuadra, sin doble conteo) |
| Ubicación de la institución (% del total) | alta 18,4 %; media 20,7 %; baja 51,0 %; sin ubicar 10,0 % |

Por nivel del título (% del total): grado 55,5; docente 15,3; especialización 13,5; técnico 8,6; maestría 5,5; doctorado 1,3; otro 0,2.

## Lo que se encontró
**La oferta de graduados técnicos y de grado para la manufactura es chica.** Las carreras que sirven a algún sector de manufactura suman **35.302 títulos de técnico y grado (5,1 % del total), contados una sola vez**. Más de la mitad son farmacia y bioquímica (17.397); siguen electricidad y energía (6.212), ingeniería industrial (2.778), alimentos y agroindustria (1.785) y diseño gráfico (1.335). Educación y salud concentran la mayor parte del resto.

**Qué sectores exigen formación específica (NBER, corte 0,28):** 16 de los 35 sectores de manufactura con dato.

| Exigen formación específica (16) | No exigen (19) |
|---|---|
| Bebidas 0,46; Farmacéutica 0,44; Electrónica y eléctrico 0,44; Maquinaria 0,38; Pinturas y cosmética 0,38; Químicos básicos 0,36; Joyería y diversos 0,36; Azúcar 0,35 (1 producto); Impresión 0,35 (2); Otro transporte 0,34; Petróleo refinado 0,32; Alimentos balanceados 0,30 (2); Muebles 0,29; Aceites 0,29; Metales no ferrosos 0,28; Productos de metal 0,28 | Almidones y yerba 0,278; Molinería 0,26; Confecciones 0,25; Plásticos 0,25; Lácteos 0,25; Cerámica 0,25; Vidrio y piedra 0,24; Tabaco 0,24 (2); Autopartes 0,24; Cuero y calzado 0,24; Confitería y pastas 0,23; Papel y cartón 0,23; Cemento 0,22; Siderurgia 0,21; Madera 0,21; Panificados 0,18 (1); Textiles 0,18; Frutas y hortalizas 0,17; Frigoríficos 0,16 |

Entre paréntesis, los sectores con dato de muy pocos productos (confianza baja).

Sin dato del NBER, y por lo tanto **sin clasificar**: S44 (reparación e instalación de maquinaria), agro, minería y servicios. No se imputa.

## Límites importantes
1. **Los sectores de un mismo campo reciben la misma cifra.** Los 11 sectores de alimentos (S09 a S19) tienen todos 4.496 títulos disponibles y los de ingeniería industrial reparten sobre los 36 sectores de manufactura. El cruce llega al campo de estudio y no distingue un frigorífico de una lechería. Para esos sectores la medida describe el campo, no el sector.
2. **Farmacéutica (S31) concentra 20.769 títulos** porque farmacia y bioquímica se asignaron a S31 y S65 (salud). Casi todos esos graduados trabajan en farmacias y laboratorios clínicos, no en la industria. **Sobrestima** la disponibilidad para la industria farmacéutica. Es una asignación del campo que el equipo debería revisar.
3. **10 sectores están a menos de 0,03 del corte** (S10, S11, S12, S17, S18, S22, S25, S32, S37, S38): su clasificación cambiaría con una diferencia mínima. Varios sectores tienen el dato de muy pocos productos (S16 azúcar 1; S13 panificados 1; S27, S18, S20 con 2): confianza baja. Quedan marcados `cerca_del_corte` y con la confianza.
4. **«No es de producción» no equivale a tener título:** incluye administrativos y vendedores. Es tecnología de EE. UU. de 2012 a 2018 y cubre solo manufactura.
5. **Un título mide egresados**, no ocupación. Es un flujo 2013-2025 sin año base 2010.
6. **La ubicación por distrito hereda la incertidumbre de la sede** (D17): el 51 % de los títulos está ubicado con confianza baja y el 10 % no está ubicado. Todo resultado por distrito debe correrse en los dos escenarios.
7. **Es una asignación propia** de campos y sectores; debe validarla el equipo.
8. Resultados como asociación, no causalidad.

## Cómo se revisó la calidad
La cobertura alta no prueba que las reglas sean buenas. Se revisaron a mano las 210 carreras más grandes y una muestra al azar de 70 más chicas, y aparecieron errores de orden y de palabras demasiado cortas, que se corrigieron y quedaron como pruebas automáticas: Radiología quedaba como comunicación (por «radio»), Matemática como informática (por «tic»), Administración agropecuaria como veterinaria, Medicina veterinaria como salud humana, Fútbol de campo como agronomía y Ciencias sociales como ciencias básicas.

## Cómo se usa para la Fase 2
La capa «capital humano específico: técnicos por sector y distrito» de `docs/supuestos_fase2.md` (D24) sale de `titulos_sector_distrito.csv`, filtrando `nivel` técnico y grado, y se usa en los dos escenarios. El total del distrito, sin doble conteo, está en `titulos_distrito.csv`. La columna `exige_formacion` marca si el sector la necesita; `habilidades_nber` y `confianza_exigencia` acompañan.

## Qué falta
1. **Que el equipo valide** `puente_carrera_sector.csv`, empezando por las 128 carreras que concentran el 80 % de los títulos, y decida sobre farmacia y bioquímica (límite 2).
2. La **base de secundaria completa por distrito** (la otra mitad del capital humano): hace falta el nivel educativo por distrito del Censo 2022, que no está en nuestras tablas.
3. La **oferta actual por sede** con el Registro Nacional de Carreras del MEC (no se bajó todavía).
4. **Salud como indicador aparte:** sigue pendiente tu decisión.
