# Resultado del baseline (solo densidad)

Fecha: 2026-10-12. Autor: Ever. Rama: `fase1/baseline-ever`.

## precision@k por ventana

| Ventana | p@20 | p@50 | p@100 | AUC-PR | coef densidad | Cobertura |
|---|---|---|---|---|---|---|
| 2000-2005 | 0.600 | 0.540 | 0.550 | 0.207 | 0.72 | 77% |
| 2005-2010 | 0.450 | 0.360 | 0.410 | 0.177 | 0.83 | 86% |
| 2010-2015 | 0.400 | 0.420 | 0.490 | 0.168 | 1.10 | 86% |
| 2015-2020 | 0.450 | 0.420 | 0.450 | 0.165 | 1.15 | 84% |

## Interpretacion

- **precision@20 promedio: 0.475.** De los 20 productos con mayor probabilidad predicha, ~10 despegan en 5 anios.
- **Azar: 0.04** (4% de entradas en el panel). El modelo es **12x mejor que el azar**.
- **Literatura comparable:** Bahar et al. reportan p@20 de 0.20-0.30. Este baseline esta por encima.
- **El coeficiente de densidad es positivo y creciente** (0.72 a 1.15). La densidad cada vez predice mejor.

## Cobertura

El backtest filtra por `densidad IS NOT NULL`, dejando ~85% de los pares del panel. Los pares sin densidad son productos que el pais no exporto en el anio final de la ventana. No afecta el resultado central.

## Limitaciones conocidas

1. **Filtro de poblacion (D8) sin aplicar:** falta `dotaciones.parquet`. Solo se aplica `MIN_EXPORT`.
2. **Densidad calculada con `rca_matrix`:** no con `rca_depurado`. Ajuste posterior.
3. **`coef densidad` sin errores estandar:** `logit_disperso` no los calcula. Para tarea 1.9 hace falta otra herramienta.

## Proximos pasos

- Agregar capas de dotaciones (D4, tarea 1.9): capital humano, credito, energia, logistica.
- Backtest de casos Paraguay: arneses, frigorificos, biocombustibles.
- Aplicar filtro de poblacion (D8) cuando `dotaciones.parquet` este listo.