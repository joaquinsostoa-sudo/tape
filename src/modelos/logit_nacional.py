"""Logit nacional con capas (tarea 1.9, D2 c): coeficientes θ_k y λ_k con errores agrupados por país.

Pr(E=1) = Λ(α_ct + γ_pt + β d_cpt + Σ_k θ_k r_pk a_ckt + Σ_k λ_k d_cpt r_pk a_ckt)

- Unidad: país × producto HS4 × ventana (t0 = 2000, 2005, 2010, 2015; h = 5). Efectos fijos de país-ventana y de
  producto-ventana (D2 c, especificación del documento, dentro de la muestra).
- Entrada (D7): E = 1[RCA_t0 < 0,5 y RCA_t0+5 ≥ 1], un solo año. El panel incluye los productos que el país no exportaba
  (RCA = 0), que son los que más importan para la diversificación.
- Muestra (D8): población ≥ 1 millón y exportaciones ≥ USD 1.000 millones en t0. φ y densidad se calculan con esa muestra.
- Presencia (D13): RCA ≥ 1 en al menos 2 de los 3 años de calendario que terminan en algún año de la ventana de 5 años
  que termina en t0 (D3: solo datos ≤ t0).
- Sin energía (HS4 2716, Itaipú y Yacyretá). **No marca reexportaciones** (D6): hace falta importar el comercio bilateral;
  es una limitación de esta versión.
- Capas (r_pk, a_ckt; D15): energía (intensidad energética × menos log del precio), capital humano (habilidades × hc), capital
  físico (intensidad de capital × log del stock de capital por trabajador de PWT; el crédito/PIB queda como robustez), logística (menos log valor/peso × LPI). r en logaritmo (energía, capital,
  valor/peso) y estandarizado entre los productos con requisito; a re-estandarizado entre los países de la muestra.
- Agricultura, minería y servicios no tienen requisitos (D4): quedan fuera de este modelo.

Uso: uv run python -m src.modelos.logit_nacional --expo RUTA.parquet  (o --db BASE.duckdb para extraerlas)
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from src.modelos.densidad_np import densidad_df
from src.modelos.logit_disperso import LogitEfectosFijos

RAIZ = Path(__file__).resolve().parents[2]
CLEAN = RAIZ / "data" / "clean"
MODELO = RAIZ / "data" / "model"
VENTANAS = (2000, 2005, 2010, 2015)
H = 5
HS4_ENERGIA = "2716"
MIN_EXPORT = 1_000_000  # miles de USD (BACI): 1.000 millones de USD
MIN_POBLACION = 1_000_000
RCA_ENTRADA_INICIO, RCA_ENTRADA_FIN = 0.5, 1.0
CAPAS_PRINCIPALES = {  # D15: capa -> (columna de requisitos, columna de dotaciones)
    "energia": ("energia", "z_energia"),
    "capital_humano": ("habilidades", "z_capital_humano"),
    "capital_fisico": ("capital", "z_capital_fisico"),  # stock de capital por trabajador (PWT), par del requisito de capital
    "logistica": ("valor_peso", "z_logistica"),
}
# robustez de D15: el crédito/PIB en lugar del capital físico (comparte el requisito de capital)
CAPAS = {**CAPAS_PRINCIPALES, "credito": ("capital", "z_credito")}


def extraer_exportaciones(con, tabla: str = "ef.main.rca_matrix") -> pd.DataFrame:
    """Exportaciones por país (código BACI), año y producto HS4, desde una tabla con year, country, product, x_ik."""
    return con.execute(f"""SELECT year AS anio, country AS codigo_baci, substr(product, 1, 4) AS hs4, SUM(x_ik) AS x
                           FROM {tabla} GROUP BY 1, 2, 3""").df()


def a_iso3(expo: pd.DataFrame, puente: pd.DataFrame) -> pd.DataFrame:
    """Reemplaza el código numérico de BACI por ISO3 (los códigos sin ISO3 se descartan)."""
    e = expo.merge(puente[["codigo_baci", "iso3"]], on="codigo_baci", how="inner")
    return e.groupby(["anio", "iso3", "hs4"], as_index=False).x.sum()


def calcular_rca(expo: pd.DataFrame) -> pd.DataFrame:
    """RCA por año sin la energía de Itaipú y Yacyretá (HS4 2716), con los totales recalculados sin ella."""
    e = expo[expo.hs4 != HS4_ENERGIA].copy()
    xc = e.groupby(["anio", "iso3"]).x.transform("sum")
    xp = e.groupby(["anio", "hs4"]).x.transform("sum")
    xw = e.groupby("anio").x.transform("sum")
    e["rca"] = (e.x / xc) / (xp / xw)
    return e[["anio", "iso3", "hs4", "x", "rca"]]


def paises_elegibles(expo: pd.DataFrame, poblacion: pd.DataFrame, anio: int) -> set[str]:
    """D8: población ≥ 1 millón y exportaciones totales ≥ USD 1.000 millones en `anio`; sin dato de población, fuera."""
    tot = expo[expo.anio == anio].groupby("iso3").x.sum()
    pob = poblacion[poblacion.anio == anio].set_index("iso3").poblacion
    ok = tot[tot >= MIN_EXPORT].index.intersection(pob[pob >= MIN_POBLACION].index)
    return set(ok)


def presencia(rca: pd.DataFrame, t0: int, anios_ventana: int = 5, calendario: int = 3, minimo: int = 2) -> pd.DataFrame:
    """D13 + D3: (iso3, hs4) con RCA ≥ 1 en `minimo` de los `calendario` años de calendario que terminan en algún año
    de la ventana [t0 - anios_ventana + 1, t0]. Los años sin dato cuentan como sin presencia."""
    f = rca[(rca.rca >= 1) & (rca.anio <= t0)][["anio", "iso3", "hs4"]]
    corrido = pd.concat([f.assign(fin=f.anio + k) for k in range(calendario)])
    n = corrido.groupby(["iso3", "hs4", "fin"]).size().rename("n").reset_index()
    ok = n[(n.n >= minimo) & n.fin.between(t0 - anios_ventana + 1, t0)]
    return ok[["iso3", "hs4"]].drop_duplicates()


def panel_ventana(rca: pd.DataFrame, paises: set[str], productos: list[str], t0: int, h: int = H,
                  inicio_max: float = RCA_ENTRADA_INICIO, fin_min: float = RCA_ENTRADA_FIN, dos_de_tres: bool = False) -> pd.DataFrame:
    """Panel de entradas D7: todos los pares país × producto con RCA_t0 < `inicio_max` (0,5), contando RCA = 0.

    Entrada principal: RCA_t0+h ≥ `fin_min` (1). Con `dos_de_tres` (robustez de D7): RCA ≥ `fin_min` en al menos 2 de los
    3 años de calendario que terminan en t0 + h."""
    grilla = pd.MultiIndex.from_product([sorted(paises), productos], names=["iso3", "hs4"]).to_frame(index=False)
    r0 = rca[rca.anio == t0][["iso3", "hs4", "rca"]].rename(columns={"rca": "rca0"})
    r1 = rca[rca.anio == t0 + h][["iso3", "hs4", "rca"]].rename(columns={"rca": "rca1"})
    p = grilla.merge(r0, on=["iso3", "hs4"], how="left").merge(r1, on=["iso3", "hs4"], how="left")
    p[["rca0", "rca1"]] = p[["rca0", "rca1"]].fillna(0.0)
    p = p[p.rca0 < inicio_max].copy()
    if dos_de_tres:
        t1 = t0 + h
        anios_ok = (rca[rca.anio.between(t1 - 2, t1) & (rca.rca >= fin_min)].groupby(["iso3", "hs4"]).size().rename("n_ok"))
        p = p.merge(anios_ok, on=["iso3", "hs4"], how="left")
        p["E"] = (p.n_ok.fillna(0) >= 2).astype(int)
    else:
        p["E"] = (p.rca1 >= fin_min).astype(int)
    p["anio"] = t0
    return p[["anio", "iso3", "hs4", "rca0", "E"]].reset_index(drop=True)


def z(s: pd.Series) -> pd.Series:
    return (s - s.mean()) / s.std()


def requisitos_estandarizados(req: pd.DataFrame) -> pd.DataFrame:
    """r_pk por producto HS4: logaritmo de energía, capital y valor/peso (con signo: más voluminoso = más logística)."""
    r = req.dropna(subset=["energia", "capital", "habilidades", "valor_peso_usd_kg"]).copy()
    out = pd.DataFrame({"hs4": r.hs4})
    out["r_energia"] = z(np.log(r.energia))
    out["r_capital_humano"] = z(r.habilidades)
    out["r_credito"] = z(np.log(r.capital))
    out["r_capital_fisico"] = out.r_credito  # mismo requisito de capital, otra dotación
    out["r_logistica"] = z(-np.log(r.valor_peso_usd_kg))
    return out.reset_index(drop=True)


def sin_variacion(df: pd.DataFrame, y: str, grupos: list[str]) -> pd.DataFrame:
    """Quita, hasta que no quede ninguno, los grupos de efectos fijos sin ninguna entrada o con solo entradas: no
    aportan a las pendientes (sus efectos van a ±infinito) y causan separación perfecta."""
    d = df
    while True:
        malo = pd.Series(False, index=d.index)
        for g in grupos:
            m = d.groupby(g)[y].transform("mean")
            malo |= (m == 0) | (m == 1)
        if not malo.any():
            return d
        d = d[~malo]


def construir_datos(expo: pd.DataFrame, dot: pd.DataFrame, req: pd.DataFrame, pob: pd.DataFrame,
                    ventanas=VENTANAS, h: int = H, revelados: bool = False, solo_con_requisitos: bool = True, **entrada) -> pd.DataFrame:
    """Tabla del logit: una fila por país × producto × ventana, con d_z, interacciones y efectos fijos.

    `entrada` pasa a `panel_ventana` (inicio_max, fin_min, dos_de_tres) para las pruebas de robustez de la entrada.
    Con `revelados` agrega los faltantes del requisito revelado (`requisito_revelado.py`, columnas `f_<capa>`); con
    `solo_con_requisitos=False` incluye todos los productos (r_* queda vacío donde NBER-CES no tiene dato)."""
    rca = calcular_rca(expo)
    r = requisitos_estandarizados(req)
    productos = sorted(set(r.hs4) & set(rca.hs4)) if solo_con_requisitos else sorted(set(rca.hs4))
    trozos = []
    for t0 in ventanas:
        paises = paises_elegibles(expo, pob, t0)
        rca_m = rca[rca.iso3.isin(paises)]  # φ y RCA: solo la muestra D8
        pres = presencia(rca_m, t0)
        p = panel_ventana(rca_m, paises, productos, t0, h, **entrada)
        p = p.merge(densidad_df(pres.rename(columns={"iso3": "country", "hs4": "product"}),
                                p[["iso3", "hs4"]].rename(columns={"iso3": "country", "hs4": "product"})
                                ).rename(columns={"country": "iso3", "product": "hs4"}), on=["iso3", "hs4"], how="left")
        d = dot[(dot.anio == t0) & dot.iso3.isin(paises)]
        a = pd.DataFrame({"iso3": d.iso3})
        for capa, (_, col) in CAPAS.items():
            a[f"a_{capa}"] = z(d[col]).to_numpy()  # re-estandarizada entre los países de la muestra
        a["a_pib"] = z(np.log(d.pib_pc_ppa.where(d.pib_pc_ppa > 0))).to_numpy()  # control de desarrollo
        p = p.merge(a, on="iso3", how="inner")
        if revelados:
            from src.modelos.requisito_revelado import faltantes

            p = p.merge(faltantes(pres, a, p[["iso3", "hs4"]]), on=["iso3", "hs4"], how="left")
        trozos.append(p)
    df = pd.concat(trozos, ignore_index=True).merge(r, on="hs4", how="inner" if solo_con_requisitos else "left")
    # los países sin alguna capa se descartan en cada especificación (`ajustar_especificacion`), según las capas que use
    df["d_z"] = z(df.densidad)
    for capa in CAPAS:
        df[f"ra_{capa}"] = df[f"r_{capa}"] * df[f"a_{capa}"]
        df[f"dra_{capa}"] = df.d_z * df[f"ra_{capa}"]
        df[f"rpib_{capa}"] = df[f"r_{capa}"] * df.a_pib  # control: cada requisito × nivel de desarrollo
    df["pais_ventana"] = df.iso3 + "_" + df.anio.astype(str)
    df["producto_ventana"] = df.hs4 + "_" + df.anio.astype(str)
    return df.reset_index(drop=True)


_RA = {c: f"ra_{c}" for c in CAPAS}
_PRINC4 = [_RA[c] for c in CAPAS_PRINCIPALES]
_CRED4 = [_RA[c] for c in ("energia", "capital_humano", "credito", "logistica")]
_RPIB_PRINC = [f"rpib_{c}" for c in CAPAS_PRINCIPALES]
_RPIB_CRED = [f"rpib_{c}" for c in ("energia", "capital_humano", "credito", "logistica")]
ESPECIFICACIONES = {
    "densidad_sola": ["d_z"],
    "capas": ["d_z", *_PRINC4],
    "capas_e_interacciones": ["d_z", *_PRINC4, *(f"dra_{c}" for c in CAPAS_PRINCIPALES)],
    # control por PIB per cápita (opción prevista en la tarea 1.9): separa «la capa» de «el desarrollo general»
    "capas_con_control_pib": ["d_z", *_PRINC4, *_RPIB_PRINC],
    # robustez de D15: crédito en lugar del capital físico, y los dos juntos
    "capas_con_credito": ["d_z", *_CRED4],
    "capas_con_credito_y_control_pib": ["d_z", *_CRED4, *_RPIB_CRED],
    "cinco_capas": ["d_z", *_RA.values()],
}


def ajustar_especificacion(df: pd.DataFrame, columnas: list[str]) -> tuple[pd.DataFrame, dict]:
    """Ajusta el logit con efectos fijos de país-ventana y producto-ventana; devuelve la tabla de coeficientes."""
    d = sin_variacion(df.dropna(subset=columnas), "E", ["pais_ventana", "producto_ventana"])
    m = LogitEfectosFijos(columnas, ["pais_ventana", "producto_ventana"], C=None).ajustar(d, "E")
    tabla = m.errores_agrupados(d, "E", "iso3")
    info = {"filas": len(d), "filas_descartadas": len(df) - len(d), "entradas": int(d.E.sum()),
            "paises": d.iso3.nunique(), "productos": d.hs4.nunique()}
    return tabla, info


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--expo", help="parquet con anio, iso3, hs4, x (si no existe y hay --db, se extrae)")
    ap.add_argument("--db", help="base DuckDB (ruta o URL) con rca_matrix, para extraer las exportaciones HS4")
    ap.add_argument("--salida", default=str(MODELO / "logit_coeficientes.csv"))
    args = ap.parse_args(argv)
    ruta = Path(args.expo or MODELO / "exportaciones_hs4.parquet")
    if not ruta.exists():
        if not args.db:
            raise SystemExit(f"falta {ruta}: dar --db para extraerlo")
        import duckdb

        con = duckdb.connect()
        if args.db.startswith("http"):
            con.execute("LOAD httpfs")
        con.execute(f"ATTACH '{args.db}' AS ef (READ_ONLY)")
        puente = pd.read_csv(CLEAN / "puente_paises_baci.csv")
        a_iso3(extraer_exportaciones(con), puente).to_parquet(ruta, index=False)
    expo = pd.read_parquet(ruta)
    dot = pd.read_parquet(CLEAN / "dotaciones.parquet")
    req = pd.read_csv(CLEAN / "requisitos_producto_hs4.csv", dtype={"hs4": str})
    pob = pd.read_csv(CLEAN / "poblacion_pais.csv")
    df = construir_datos(expo, dot, req, pob)
    print(f"tabla del logit: {len(df):,} filas, {int(df.E.sum()):,} entradas ({100 * df.E.mean():.2f} %), "
          f"{df.iso3.nunique()} países, {df.hs4.nunique()} productos")
    print(df.groupby("anio").agg(filas=("E", "size"), entradas=("E", "sum"), paises=("iso3", "nunique")).to_string())
    salidas = []
    for nombre, columnas in ESPECIFICACIONES.items():
        tabla, info = ajustar_especificacion(df, columnas)
        print(f"\n== {nombre}: {info['filas']:,} filas ({info['filas_descartadas']:,} descartadas sin variación), "
              f"{info['entradas']:,} entradas")
        print(tabla.round(4).to_string())
        salidas.append(tabla.reset_index(names="variable").assign(especificacion=nombre, **info))
    Path(args.salida).parent.mkdir(parents=True, exist_ok=True)
    pd.concat(salidas).to_csv(args.salida, index=False)
    print(f"\n-> {args.salida}")


if __name__ == "__main__":
    main()
