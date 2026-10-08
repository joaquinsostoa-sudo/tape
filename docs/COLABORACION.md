# Cómo trabajar en TAPE entre dos personas

## Principio: tres capas, cada una con su lugar
| Capa | Qué es | Dónde vive | Cómo se comparte |
|---|---|---|---|
| **Código y documentos** | `src/`, `tests/`, `docs/`, `CLAUDE.md`, tablas puente pequeñas de `data/clean/` | Git (repositorio privado) | `git pull` / `git push` |
| **Datos automáticos** | BACI, Atlas, WDI, concordancias, límites (≈ 4 GB) | No se comparten: cada uno los baja | `uv run python -m src.descargas.todas` |
| **Datos manuales** | Archivos que no se bajan solos (lista abajo) | Carpeta compartida de Drive `TAPE_datos_manuales/` | Copiar a `data/raw/<fuente>/` |

Los derivados (`data/clean`, `data/model`) **no se suben**: se regeneran con `uv run python -m src.reconstruir_todo`. Solo se versionan las tablas pequeñas que son resultados de trabajo (taxonomía, puentes, equivalencias), indicadas en `.gitignore`.

## Puesta en marcha (una vez)
```bash
git clone <URL del repositorio> TAPE
cd TAPE
uv sync
uv run python -m src.descargas.todas        # baja ≈ 4 GB (BACI, Atlas, WDI, concordancias, límites)
# copiar los archivos manuales de Drive a las carpetas indicadas abajo
uv run python -m src.reconstruir_todo
uv run pytest
```
Requisitos: Python 3.12 y `uv` (en Windows: `winget install astral-sh.uv`), y Git.

## Archivos manuales (Drive → `data/raw/`)
| Archivo | Destino |
|---|---|
| `pwt1001.xlsx` (Penn World Table 10.01) | `data/raw/pwt/` |
| `PIB_33_actividades_desde_1991.xlsx`, `Tabla_correspondencia_CNAEP1.0_CIIU4.pdf`, `SCN_Paraguay_Anio_Base_2014.pdf` | `data/raw/bcp_cuentas_nacionales/` |
| `Anexo_Estadistico_CRA.xlsx`, `Metodologia_CRA.pdf` | `data/raw/bcp_cuentas_regionales/` |
| `industrias_mapa_mic_2026-10-08.json` (17.080 industrias del mapa MIC) | `data/raw/mic_mapa/` |
| `Informe-MAQUILA-AGOSTO26.pdf` | `data/raw/mic_maquila/` |

Cada archivo nuevo que se agregue se anota en `data/fuentes.csv` (fecha, versión, licencia) y en esta tabla.

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
