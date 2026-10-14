import numpy as np

from src.herramienta import exportar_pry as ep


def test_disposicion_junta_los_productos_conectados_y_separa_los_grupos():
    n = 8
    phi = np.zeros((n, n))
    for grupo in ([0, 1, 2, 3], [4, 5, 6, 7]):
        for a in grupo:
            for b in grupo:
                if a != b:
                    phi[a, b] = 0.8
    phi[3, 4] = phi[4, 3] = 0.05
    xy = ep.disposicion(phi, k=3, iteraciones=200)
    assert xy.shape == (n, 2) and xy.min() >= 0 and xy.max() <= 1.0 + 1e-9
    d = np.sqrt(((xy[:, None] - xy[None]) ** 2).sum(-1))
    dentro = np.mean([d[a, b] for g in ([0, 1, 2, 3], [4, 5, 6, 7]) for a in g for b in g if a != b])
    fuera = np.mean([d[a, b] for a in range(4) for b in range(4, 8)])
    assert dentro < fuera


def test_disposicion_es_reproducible_y_tolera_productos_sin_vecinos():
    phi = np.zeros((5, 5))
    phi[0, 1] = phi[1, 0] = 0.5
    a, b = ep.disposicion(phi, k=2, iteraciones=50), ep.disposicion(phi, k=2, iteraciones=50)
    assert np.allclose(a, b) and np.isfinite(a).all()


def test_pagina_inserta_los_datos_y_escapa_el_cierre_de_script():
    from src.herramienta.construir_pagina import construir

    html = construir("<script>__DATOS__</script>", '{"a":"</script>"}')
    assert html == r'<script>{"a":"<\/script>"}</script>'
