from src.descargas.comun import archivos_dataverse, sha256_archivo, ya_descargado


def test_archivos_dataverse_extrae_nombre_e_id():
    resp = {"data": {"files": [{"dataFile": {"filename": "a.csv", "id": 7}},
                                {"dataFile": {"filename": "b.csv", "id": 9}}]}}
    assert archivos_dataverse(resp) == {"a.csv": 7, "b.csv": 9}


def test_sha256_y_ya_descargado(tmp_path):
    f = tmp_path / "x.bin"
    f.write_bytes(b"abc")
    assert sha256_archivo(f) == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    assert ya_descargado(f, 3) and not ya_descargado(f, 4) and ya_descargado(f, None)
    assert not ya_descargado(tmp_path / "no_existe", None)
