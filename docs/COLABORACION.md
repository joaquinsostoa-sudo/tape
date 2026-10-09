# Cómo trabajar en TAPE entre dos personas

## Principio: tres capas, cada una con su lugar
| Capa | Qué es | Dónde vive | Cómo se comparte |
|---|---|---|---|
| **Código y documentos** | `src/`, `tests/`, `docs/`, `CLAUDE.md`, tablas puente pequeñas de `data/clean/` | Git (repositorio privado) | `git pull` / `git push` |
| **Datos automáticos** | BACI, Atlas, WDI, PWT (aviso abajo), concordancias, límites administrativos y 10 tablas de SIMEL (≈ 4 GB) | No se comparten: cada uno los baja | `uv run python -m src.descargas.todas` |
| **Datos manuales** | Archivos que no se bajan solos (lista abajo, 45 MB) | Carpeta compartida de Drive: `TAPE_datos_manuales.zip` | Descomprimir en la raíz del repositorio |

Los derivados (`data/clean`, `data/model`) **no se suben**: se regeneran con `uv run python -m src.reconstruir_todo`. Solo se versionan las tablas pequeñas que son resultados de trabajo (taxonomía, puentes, equivalencias), indicadas en `.gitignore`.

## Puesta en marcha (una vez)
```bash
git clone <URL del repositorio> TAPE
cd TAPE
uv sync
uv run python -m src.descargas.todas        # baja ≈ 4 GB (BACI, Atlas, WDI, concordancias, límites, SIMEL)
# descomprimir TAPE_datos_manuales.zip (de Drive) en la raíz del repositorio: crea data/raw/<fuente>/...
uv run python -m src.reconstruir_todo
uv run pytest
```
Requisitos: Python 3.12 y `uv` (en Windows: `winget install astral-sh.uv`), y Git.

`reconstruir_todo` salta los pasos cuyas entradas faltan (dice cuáles) y sigue; si un paso falla por otra causa, lo informa y termina con error. Sin los datos automáticos corren los pasos de datos manuales, pero los que necesitan límites, Atlas o concordancias se saltan o fallan. Pasa lo mismo con `pytest`: unas 13 pruebas se saltan si faltan datos.

**Aviso PWT:** `src.descargas.pwt` no baja el archivo: la página lo bloquea por script. `pwt1001.xlsx` viene en el zip.

## Archivos manuales: el contenido de `TAPE_datos_manuales.zip` (2026-10-09)
Se descomprime en la raíz y deja cada archivo en `data/raw/<fuente>/`. No incluye los README ni los manifiestos (ya están en Git).

| Carpeta `data/raw/` | Archivos | Origen |
|---|---|---|
| `pwt/` | `pwt1001.xlsx` (Penn World Table 10.01) | GGDC, descarga manual |
| `bcp_cuentas_nacionales/` | `PIB_33_actividades_desde_1991.xlsx`, `Tabla_correspondencia_CNAEP1.0_CIIU4.pdf`, `SCN_Paraguay_Anio_Base_2014.pdf` | BCP |
| `bcp_cuentas_regionales/` | `Anexo_Estadistico_CRA.xlsx`, `Metodologia_CRA.pdf` | BCP |
| `bcp_credito/` | `Boletin_Bancos_Ago26.xlsm` (33 MB; datos en un modelo Power Pivot que solo lee Excel) y `Creditos_bcp_sector_082026.xlsx` (serie mensual por sector 2020-2026, extraída con Excel) | BCP, Superintendencia de Bancos |
| `ephc/` | `2022/` a `2025/`: REG01, REG02 e INGREFAM en CSV, más el diccionario de 2025 (136 MB) | INE |
| `aneaes/` | 5 `.xls` de carreras y programas, acreditados y no acreditados (se leen con `xlrd`) | ANEAES |
| `censo_agropecuario/` | `CAN2022_Volumen_I.xlsx` (78 cuadros por departamento) y `CAN2022_fincas_por_distrito.xlsx` (fincas y superficie por distrito) | MAG |
| `mip_cepal_oit/` | `Simulador-MIP-Paraguay.xlsm` (MIP de 21 sectores; autoría por confirmar) | BCP y terceros |
| `mec_escuelas/` | `establecimientos_2012.pdf` (30 MB) e `instituciones_2018.csv` | MEC |
| `mic_maquila/` | `Informe-MAQUILA-AGOSTO26.pdf` | MIC |
| `mic_mapa/` | 9 archivos (JSON y CSV) de las pestañas A, B, C, E, F, G y H del visor del MIC, leídos con el navegador | MIC (visor sin licencia declarada) |

**Qué no está en el zip:**
- `ephc/2022_sitio_previo/`: copia anterior de la EPHC 2022 que solo existe en la computadora de Joaquín; no hace falta (ver `data/raw/ephc/README.md`).
- Las 10 tablas de SIMEL (`data/raw/simel/`): se bajan solas.
- Lo pendiente de conseguir: registro de títulos y de carreras del MEC, Censo Económico 2011, pedidos formales (ver `docs/ESTADO.md`).

**Cómo se regenera el zip:**
```bash
uv run python -m src.empaquetar_datos_manuales    # deja TAPE_datos_manuales.zip junto a la carpeta del repositorio
```
Cuando se agregue un archivo manual nuevo, hay que anotarlo en `data/fuentes.csv`, en el README de su carpeta y en esta tabla (y en `MANUALES` de `src/empaquetar_datos_manuales.py` si es una carpeta nueva), regenerar el zip y subirlo a Drive.

## Reglas de trabajo
1. **Una tarea, una rama.** Rama `fase1/1-1-limpieza-baci`, un cambio acotado, pruebas que pasan (`uv run pytest`, `uv run ruff check src tests`) y mensaje de commit claro. Se integra a `main` por *pull request* revisado por la otra persona.
2. **No editar `data/raw/`.** Es solo lectura.
3. **Decisiones metodológicas se acuerdan antes de implementarse** y se anotan en `docs/supuestos.md` (fecha, alternativa descartada, quién decidió). Las opciones abiertas están en `docs/PLAN_fase0_fase1.md`.
4. **No trabajar dos personas en la misma tarea.** Se reparte en `docs/ESTADO.md` (sección "Quién hace qué").
5. **Claude Code**: cada persona lo abre en su carpeta clonada; `CLAUDE.md` le da el contexto. Antes de empezar: `git pull`. Al terminar una tarea: commit y `git push`.
6. **Datos con personas.** El registro de títulos del MEC trae nombre y documento: no se sube a ningún lado; se trabaja solo con agregados.

## Licencias y reservas
- Repositorio **privado**. La propuesta comercial prevé abrir código y metodología más adelante; hasta revisar las licencias de cada fuente (BACI, Atlas, MIC, INE) no se publica nada.
- Los datos del visor del MIC se leyeron de una página pública sin licencia declarada: son provisorios hasta tener la entrega oficial.
