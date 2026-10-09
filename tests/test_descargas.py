from src.descargas.comun import (
    archivos_dataverse,
    es_html_inesperado,
    sha256_archivo,
    ya_descargado,
)


def test_html_inesperado_se_detecta_solo_si_el_archivo_no_es_html():
    assert es_html_inesperado("text/html; charset=utf-8", "pwt110.xlsx")
    assert not es_html_inesperado("application/octet-stream", "pwt110.xlsx")
    assert not es_html_inesperado("text/html", "pagina.html")


def test_archivos_dataverse_extrae_nombre_e_id():
    resp = {"data": {"files": [{"dataFile": {"filename": "a.csv", "id": 7}},
                                {"dataFile": {"filename": "b.csv", "id": 9}}]}}
    assert archivos_dataverse(resp) == {"a.csv": 7, "b.csv": 9}


def test_simel_url_datos_y_tablas_unicas():
    from src.descargas import simel

    assert simel.url_datos("DF_X") == "https://sdmx.simel.mtess.gov.py/rest/data/PY110,DF_X,1.0/all"
    assert len(simel.TABLAS) == len(set(simel.TABLAS)) == 10


def test_todas_incluye_cada_modulo_de_descarga():
    """Cada módulo de src/descargas con un main() de descarga debe estar en todas.py (la guía lo promete)."""
    from src.descargas import todas

    esperados = {"concordancias", "limites_admin", "wdi", "pwt", "simel", "atlas", "baci"}
    assert {nombre for nombre, _ in todas.PASOS} == esperados


def test_sha256_y_ya_descargado(tmp_path):
    f = tmp_path / "x.bin"
    f.write_bytes(b"abc")
    assert sha256_archivo(f) == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    assert ya_descargado(f, 3) and not ya_descargado(f, 4) and ya_descargado(f, None)
    assert not ya_descargado(tmp_path / "no_existe", None)
