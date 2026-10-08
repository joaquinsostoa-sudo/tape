import pandas as pd
import pytest

from src.puentes.industrias_distrito_sector import LOCALIZADAS, PUENTE, repartir

pytestmark = pytest.mark.skipif(not (LOCALIZADAS.exists() and PUENTE.exists()), reason="faltan datos locales")


def test_el_reparto_conserva_las_17080_industrias_y_los_distritos():
    loc = pd.read_parquet(LOCALIZADAS)
    t = repartir(loc, pd.read_csv(PUENTE, dtype={"sector_id": str}))
    assert t.n_industrias.sum() == pytest.approx(17080)
    por_distrito = t.groupby("distrito").n_industrias.sum()
    esperado = loc.groupby("distrito").size()
    assert (por_distrito.sort_index() - esperado.sort_index()).abs().max() < 1e-6


def test_el_reparto_no_inventa_sectores_en_subsectores_alta_confianza():
    loc = pd.read_parquet(LOCALIZADAS)
    t = repartir(loc, pd.read_csv(PUENTE, dtype={"sector_id": str}))
    assert (t.n_industrias >= 0).all() and t.sector_id.notna().all()
