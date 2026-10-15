# Oportunidades de complejidad de Paraguay: cercanía × complejidad, COG y escalera (corte 2024)

Código: `src/modelos/oportunidades.py` (`uv run python -m src.modelos.oportunidades`) y `src/figuras/oportunidades.py`. Salidas en `data/model/` (no versionadas): `oportunidades_PRY_2024.csv`, `escalera_PRY_2024.csv`, `habilitadores_PRY_2024.csv`. Figura: `docs/figuras/oportunidades_PRY_2024.png` (panel A: complejidad intrínseca; panel B: complejidad relativa).

## La pregunta
No solo qué productos están cerca de lo que Paraguay ya hace, sino **cuáles de esos son más complejos**, y de dos maneras: (A) **intrínseca**, un producto de PCI alto sin importar de dónde se parte, y (B) **relativa («peldaño»)**, un producto más complejo que lo que Paraguay ya hace cerca de él, que es lo más parecido a una escalera. Es la parte de «valor» del plan (pregunta 2) puesta junto a la cercanía.

## Cómo se hizo (decisiones del equipo, 2026-10-14)
- **PCI y COG del Atlas de Complejidad Económica** (HS92, 4 dígitos, 2024). PCI: complejidad del producto (promedio 0). COG: cuánto abre el producto el camino hacia otros productos complejos que el país aún no hace. También el ECI de Paraguay del Atlas.
- **Eje de cercanía = la puntuación del modelo** (densidad + propensión del producto, de `candidatos_sector.md`); la densidad cruda queda en la tabla. **Dos ejes sin fusionar en un puntaje único**: la cercanía tiene respaldo predictivo (D16) y la complejidad es una medida de valor.
- **Candidatos:** los 991 productos sin presencia D13, con RCA < 0,5 y con PCI, COG y al menos un producto presente cercano. *Cercano* = puntuación en el cuartil superior de los candidatos.
- **(A) Intrínseca:** *complejo* = PCI > 0.
- **(B) Relativa:** salto = PCI del candidato − PCI de referencia, donde la referencia es el promedio, ponderado por la proximidad φ, de los 5 productos que Paraguay ya exporta más próximos al candidato. *Sube* = salto > 0.
- **Escalera:** para cada producto que Paraguay ya exporta (93 con presencia D13 en 2024), sus vecinos de mayor proximidad con PCI mayor que el suyo; para cada candidato, los productos actuales que lo vuelven alcanzable.

## Lo que se ve
- **Paraguay es de complejidad baja pero sube:** ECI −0,28 en 2024 (Atlas), contra −1,10 en 2000 y −0,57 en 2022; el PCI medio de los 93 productos que exporta con ventaja es −0,79.
- **A. Intrínseca (eje: puntuación):** 81 cercanos y complejos, 167 cercanos y simples, 527 lejanos y complejos y 216 lejanos y simples. Entre los candidatos, lo complejo sigue estando lejos (la correlación entre densidad y PCI es −0,66).
- **B. Relativa:** **153 candidatos cercanos que suben** (más complejos que lo que Paraguay hace cerca de ellos), 95 cercanos que no suben, 577 lejanos que suben y 166 lejanos que no suben. Como la canasta de Paraguay es de PCI bajo, subir respecto de ella es mucho más frecuente que ser complejo en términos absolutos: el 62 % de los cercanos sube, contra el 33 % que es complejo.
- **Cercanos y complejos con mayor puntuación (A):** tanques de aluminio 7611, residuos de estaño 8002, bebidas fermentadas 2206 (sidra e hidromiel), generadores 8405, tejidos en juegos 6308, partes de armas 9305, láminas de plomo 7804, cables de cobre 7413, hilados de algodón 5207.
- **Cercanos que suben con mayor puntuación (B), con su salto:** cemento 2523 (+0,14), manufacturas de plomo 7806 (+0,46), desechos de vidrio 7001 (+0,44), desechos de plástico 3915 (+0,38), aceite de maní 1508 (+0,04), maquinaria de perforación 8430 (+0,27), sémola de maíz 1103 (+0,32), aguas con azúcar 2202 (+0,63) y mezclas de hidrocarburos aromáticos 2707 (+0,35).
- **Escalera:** 89 de los 93 productos presentes tienen al menos un vecino más complejo (445 escalones). La soja (PCI −2,57) lleva a torta de soja (−1,55), sorgo y aceite de soja (−1,23); la carne bovina deshuesada (−1,09) a grasas bovinas (−0,45), menudencias (−0,41) y lácteos; los **arneses** (8544, −0,26) a **estructuras de acero (7308), construcciones plásticas (3925) y partes de asientos (9401)**, con PCI de 0,13 a 0,32 y proximidad de 0,63; el etanol (−1,22) a bebidas fermentadas (+0,10). La ficha de la herramienta muestra estos escalones para cada producto exportado y, para cada candidato, su salto frente a lo que Paraguay hace cerca.

## Cómo leerlo (y lo que no dice)
- **Es asociación, no promesa:** «te acerca a productos más complejos», no «sube tu ECI». El vínculo entre complejidad y crecimiento tiene respaldo en la literatura, con matices y críticas; aquí no se prueba.
- **La puntuación del modelo arrastra la propensión de cada producto a ser adoptado, y eso favorece a categorías residuales:** entre los candidatos mejor puntuados hay muchos desechos y chatarras (3915, 7001, 7112, 7902, 5505), partidas «n.e.s.» y productos especiales (armas 9301 y 9305, monedas 7118, planeadores 8801). Son productos que muchos países «entran» con frecuencia pero que no son oportunidades productivas en sentido estricto. **Pendiente:** decidir si se excluyen del listado (por ejemplo con una lista de partidas de desechos y residuales) o se muestran con una marca.
- El salto relativo depende de cuántos productos presentes se usan como referencia (5) y de que el PCI de Paraguay es bajo: es una medida de «peldaño», no de valor absoluto.
- **No considera brechas ni límites** (los productos de la lista pueden requerir recursos o capacidades que Paraguay no tiene; ver `docs/mapa_brechas.md`).
- La complejidad por producto es la del Atlas, calculada con su propio RCA y su propia muestra, y no coincide exactamente con los de TAPE. Pendientes opcionales: recalcularla con el RCA depurado y la prueba de si, a igual cercanía, los productos más complejos entran menos.
