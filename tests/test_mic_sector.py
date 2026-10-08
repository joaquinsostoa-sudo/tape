import pandas as pd
import pytest

from src.puentes.mic_sector import RESUMEN, M, construir
from src.puentes.taxonomia_tape import SECTORES

pytestmark = pytest.mark.skipif(not RESUMEN.exists(), reason="falta el resumen del mapa MIC en data/raw")


def test_los_pesos_de_cada_subsector_suman_uno_salvo_los_sin_sector():
    for sub, (conf, clases) in M.items():
        assert (sum(p for _, p in clases) == pytest.approx(1.0)) or (conf == "sin_sector" and not clases), sub


def test_cubre_los_73_subsectores_y_todos_los_sectores_existen():
    p = construir(pd.read_csv(RESUMEN))
    assert p.subsector_mic.nunique() == 73
    validos = {s.id for s in SECTORES} | {""}
    assert set(p.sector_id) <= validos
    sin = {s for s, (_, clases) in M.items() if not clases}
    assert sin == {"AGROINDUSTRIA GENERAL", "INDUSTRIA GENERAL Y MULTIACTIVIDAD", "OTROS INDUSTRIALES"}
    suma = p.groupby("subsector_mic").peso.sum()
    assert all(abs(v - 1) < 1e-9 for k, v in suma.items() if k not in sin)


def test_las_industrias_conservan_su_total_al_repartirse():
    r = pd.read_csv(RESUMEN)
    p = construir(r).merge(r, left_on=["sector_mic", "subsector_mic"], right_on=["sector", "subsector"])
    asignado = (p.peso * p.n_industrias).sum()
    sin = r[r.subsector.isin([s for s, (c, cl) in M.items() if not cl])].n_industrias.sum()
    assert asignado + sin == pytest.approx(r.n_industrias.sum())
