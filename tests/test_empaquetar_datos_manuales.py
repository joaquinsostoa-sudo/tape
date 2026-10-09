from src import empaquetar_datos_manuales as m


def test_seleccion_excluye_readme_manifiestos_txt_y_copias_previas(tmp_path):
    for ruta in ("ephc/2023/REG01.csv", "ephc/2022_sitio_previo/REG01.csv", "ephc/README.md",
                 "ephc/MANIFEST.json", "mic_maquila/informe.pdf", "mic_maquila/informe.txt",
                 "atlas/grande.csv", "pwt/pwt1001.xlsx"):
        f = tmp_path / ruta
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text("x")
    elegidos = {f.relative_to(tmp_path).as_posix() for f in m.seleccionar(tmp_path, ["ephc", "mic_maquila", "pwt"])}
    assert elegidos == {"ephc/2023/REG01.csv", "mic_maquila/informe.pdf", "pwt/pwt1001.xlsx"}


def test_las_carpetas_automaticas_no_se_empaquetan():
    assert not {"atlas", "baci", "wdi", "concordancias", "limites_admin", "simel"} & set(m.MANUALES)
