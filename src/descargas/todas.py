"""Corre todas las descargas de Fase 1, de la más chica a la más pesada. Cada fuente es independiente."""
from . import atlas, baci, concordancias, pwt, wdi

PASOS = [("concordancias", concordancias), ("wdi", wdi), ("pwt", pwt), ("atlas", atlas), ("baci", baci)]


def main() -> None:
    fallos: list[str] = []
    for nombre, modulo in PASOS:
        print(f"=== {nombre}")
        try:
            modulo.main()
        except Exception as e:  # noqa: BLE001  (se informa y se sigue con la siguiente fuente)
            fallos.append(f"{nombre}: {e}")
            print(f"FALLÓ {nombre}: {e}")
    print("RESUMEN:", "todo bien" if not fallos else fallos)


if __name__ == "__main__":
    main()
