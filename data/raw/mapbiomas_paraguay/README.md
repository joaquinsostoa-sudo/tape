# MapBiomas Paraguay: estadísticas de cobertura y uso del suelo

- **Institución:** MapBiomas Paraguay (red colaborativa). Contacto de la página: paraguaymapbiomas@gmail.com
- **Registro:** fila `mapbiomas_paraguay` de `data/fuentes.csv`
- **Archivo (descargado el 2026-10-16 con autorización de Joaquín):** `Statistics-Paraguay-Col2-V1.xlsx` (35,7 MB), de https://paraguay.mapbiomas.org/en/estadisticas/
- **Licencia:** «de uso público, abierto y gratuito, sujetos a citación» (CC BY 4.0 según la página). Citar a MapBiomas Paraguay, Colección 2.

## Qué trae
Hojas `READ_ME`, `COVERAGE`, `TRANSITIONS`, `METADATA` y dos tablas dinámicas. `COVERAGE` tiene las hectáreas por clase de cobertura y uso del suelo, año por año de 1985 a 2023 (columnas `y1985` a `y2023`), para el país (10 filas), departamentos, **distritos (`POLITICAL_LEVEL_4`: 2.230 filas, 260 distritos)**, territorios indígenas y áreas protegidas.
Clases: 1.1 a 1.3 bosque natural, 2.1 y 2.2 vegetación herbácea natural, **3.1 pastura, 3.2 agricultura, 3.3 plantación forestal**, 4 sin vegetación y 5 agua. Verificado: la agricultura de los distritos suma 4.141.176 ha y la del país 4.141.174.

## Límites
- Es cobertura **satelital**: dice cuánta tierra es agrícola, no cuánto rinde, qué cultivo es ni a qué cultivo se destina. La clase «agricultura» no separa soja de otros cultivos.
- La versión dice «V1» y la colección es la 2; la página no explica el significado de «V1».
- Los nombres de distrito vienen en mayúsculas y con acentos; se unen a los 263 distritos del Censo 2022 por nombre (4 quedan sin dato: Itacuá, San José de los Arroyos, Bella Vista y Nueva Asunción).
- Limpieza: `src/limpieza/mapbiomas.py` -> `data/clean/mapbiomas_uso_distrito.csv`.
