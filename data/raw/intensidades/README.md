# Intensidades por industria (energía, capital, habilidades)

- **Institución:** NBER y Census Bureau (Becker, Gray y Marvakov, 2021)
- **Registro:** fila `intensidades` de `data/fuentes.csv`
- **Decisión:** D4 (2026-10-12): intensidades con NBER-CES; costo de energía por país con proxies de WDI.

## Archivos presentes (2026-10-12, bajados con `src/descargas/nberces.py`)
- `nberces/nberces5818v1_n2012.csv` (5 MB): 22.204 filas, 364 industrias NAICS 2012 de 6 dígitos de la manufactura de EE. UU., 1958-2018. Variables: `emp` (empleo), `pay`, `prode` (trabajadores de producción), `prodh`, `prodw`, `vship` (valor de envíos), `matcost`, `vadd` (valor agregado), `invest`, `invent`, `energy` (costo de energía), `cap`, `equip`, `plant` (stock de capital real), deflactores y TFP.
- `nberces/naics_names_2012.txt`: nombres de los códigos NAICS 2012.
- `nberces/nberces5818v1_technical_notes_Mar2021.pdf`: notas técnicas.

## Cómo se usará (tarea 1.6)
- Intensidad energética = `energy` / `vship` (o valor agregado).
- Intensidad de capital = `cap` / `emp`. **El capital llega hasta 2016**; en 2017 y 2018 viene vacío.
- Habilidades (sustituto) = proporción de trabajadores que no son de producción, (`emp` - `prode`) / `emp`.
- Valor por peso: sale de BACI (valor y toneladas), no de esta base.

## Límites
- Es la tecnología de **Estados Unidos**: supone que producir un bien exige lo mismo en todos los países.
- 364 industrias frente a miles de productos HS: muchos productos van a heredar la misma intensidad.
- No mide habilidades directamente; solo cubre manufactura (agro y minería quedan sin dato).
- Falta el puente NAICS -> HS (tabla de concordancia del Census), que se consigue aparte.
- Sanidad hecha el 2026-10-12 (2018): lo más intensivo en energía es papel prensa, cal, aluminio, gases industriales, cemento y vidrio; lo que más personal de no producción tiene son instrumentos de navegación, computadoras y semiconductores.

## Reglas
- No modificar `data/raw`. Los archivos pesados no se versionan.
