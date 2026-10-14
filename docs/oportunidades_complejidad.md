# Oportunidades de complejidad de Paraguay: cercanía × PCI, COG y escalera (corte 2024)

Código: `src/modelos/oportunidades.py` (`uv run python -m src.modelos.oportunidades`) y `src/figuras/oportunidades.py`. Salidas en `data/model/` (no versionadas): `oportunidades_PRY_2024.csv`, `escalera_PRY_2024.csv`, `habilitadores_PRY_2024.csv`. Figura: `docs/figuras/oportunidades_PRY_2024.png`.

## La pregunta
No solo qué productos están cerca de lo que Paraguay ya hace, sino **cuáles de esos son más complejos** (mayor PCI) y qué productos complejos habilita cada cosa que ya exporta. Es la parte de «valor» del plan (pregunta 2) puesta junto a la cercanía.

## Cómo se hizo (decisiones del equipo, 2026-10-14)
- **PCI y COG del Atlas de Complejidad Económica** (Growth Lab), HS92 a 4 dígitos, año 2024. PCI: complejidad del producto (promedio 0 entre productos). COG: cuánto abre el producto el camino hacia otros productos complejos que el país aún no hace. También el ECI de Paraguay del Atlas.
- **Cercanía = la densidad de TAPE** (D3, tabla depurada de D6) y **dos ejes sin fusionarlos en un puntaje único**: la cercanía tiene respaldo predictivo (D16) y la complejidad es una medida de valor; fusionarlas exigiría un peso arbitrario.
- **Candidatos:** los 1.019 productos sin presencia D13 y con RCA < 0,5 que tienen PCI y COG. **Cuadrantes:** *cercano* = densidad en el cuartil superior de los candidatos; *complejo* = PCI > 0.
- **Escalera:** para cada producto que Paraguay ya exporta (93 con presencia D13 en 2024), sus vecinos de mayor proximidad con PCI mayor que el suyo; para cada candidato, los productos actuales que lo vuelven alcanzable.

## Lo que se ve
- **Paraguay es complejidad baja pero sube:** ECI −0,28 en 2024 (Atlas), contra −1,10 en 2000 y −0,57 en 2022; el PCI medio de los 93 productos que exporta con ventaja es −0,79.
- **Lo cercano es simple y lo complejo está lejos.** Entre los candidatos, la correlación entre densidad y PCI es **−0,66** (−0,34 con la puntuación del modelo). Reparto: **26 cercanos y complejos**, 229 cercanos y simples, 599 lejanos y complejos y 165 lejanos y simples. Es el patrón clásico del espacio de productos: subir de complejidad exige saltos largos.
- **Cercano y complejo, con mayor puntuación del modelo** (densidad, puntuación, PCI, COG): residuos de madera 4401 (0,103; 0,018; 0,09; 0,05), avena 1004 (0,100; 0,015; 0,30; 0,16), pieles de visón 4302, hojas de afeitar 8212 (0,102; 0,014; 0,52; 0,12), revestimientos de PVC para pisos 3918 (0,138; 0,013; 0,80; 0,33), lanolina 1505 (0,100; 0,012; 0,64; 0,34), marcos de madera 4414 y colza 1205. Los cercanos y complejos con **mayor COG** son la lanolina 1505 (0,34), los revestimientos de PVC 3918 (0,33) y las hormonas 2937 (0,28, PCI 1,49); entre los productos de PCI > 0 con mayor puntuación, pero lejanos, están los tanques de aluminio 7611, los residuos de estaño 8002, las bebidas fermentadas 2206, los generadores 8405 y los hilados de algodón 5207.
- **Escalera:** 89 de los 93 productos presentes tienen al menos un vecino más complejo (445 escalones). Ejemplos: la soja (PCI −2,57) lleva a torta de soja (−1,55), sorgo y aceite de soja (−1,23); la carne bovina deshuesada (−1,09) a grasas bovinas (−0,45), menudencias (−0,41) y lácteos; los **arneses y conductores** (8544, −0,26) a **construcciones plásticas (3925), estructuras de acero (7308) y partes de asientos (9401)**, con PCI de 0,13 a 0,32 y proximidad 0,63, un camino natural para la maquila; el etanol (−1,22) a bebidas fermentadas (+0,10).

## Cómo leerlo
- **Es asociación, no promesa:** «te acerca a productos más complejos», no «sube tu ECI». El vínculo entre complejidad y crecimiento tiene respaldo en la literatura, con matices y críticas; aquí no se prueba.
- **Cercanía alta no equivale a puntuación alta del modelo.** La densidad es la cercanía; la puntuación del modelo (`candidatos_sector.md`) suma la propensión de cada producto a ser adoptado. Productos muy cercanos pero que casi nadie adopta (tijeras 8213, flores artificiales 6702, caseína 3501) quedan en «cercano y complejo» por densidad pero con puntuación baja: la lista anterior se ordena por la puntuación para evitar ese efecto. Los dos criterios están en la tabla (`oportunidades_PRY_2024.csv`) y cambiar el eje horizontal por la puntuación es una decisión pendiente.
- **No considera brechas ni límites** (los productos de la lista pueden requerir recursos o capacidades que Paraguay no tiene; ver `docs/mapa_brechas.md`).
- Complejidad por producto del Atlas, calculada con su propio RCA y su propia muestra: no coincide exactamente con los de TAPE. Pendiente (opcional): recalcularla con el RCA depurado.
- La prueba opcional (¿a igual densidad, los productos más complejos entran menos?) no se hizo.
