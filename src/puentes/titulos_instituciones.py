"""Ubicación de las instituciones del registro de títulos del MEC (D17).

El registro de títulos no trae distrito, solo la institución. Se la ubica cruzando con el listado de instituciones del MEC
(educación superior 2018, un campus por fila, con distrito). Reglas declaradas en `docs/supuestos.md` (D17) antes de construir:

1. Conteos 2013-2025 por carrera, título, institución, año y mes (sin documento ni nombre de personas).
2. Cruce por nombre: base exacta; si no, por similitud de palabras (Jaccard ≥ 0,80 y ventaja ≥ 0,10 sobre el segundo; entre 0,60 y 0,80 queda como candidato a revisar).
3. Si el nombre trae un lugar («- CAMPUS ALTO PARANA», «SEDE ENCARNACION», «- CAACUPE») que coincide con un distrito, se asigna ese distrito.
4. Si la institución tiene varios campus y el nombre no dice cuál, se asigna a la sede principal (el distrito con más filas en el listado de 2018) con confianza baja; la sensibilidad reparte parejo entre sus distritos.

Salidas: `data/clean/titulos_conteos.parquet`, `data/clean/puente_titulos_institucion.csv` (una fila por institución) y
`data/clean/titulos_institucion_distrito.csv` (pesos por distrito en los dos escenarios).
Uso: uv run python -m src.puentes.titulos_instituciones
"""
from __future__ import annotations

import re
import tempfile
import zipfile
from difflib import SequenceMatcher
from pathlib import Path

import duckdb
import pandas as pd

from .distritos import departamento, llave, normalizar
from .taxonomia_tape import RAIZ

TITULOS_ZIP = RAIZ / "data" / "raw" / "mec_titulos" / "registros_titulos.csv.zip"
INSTITUCIONES = RAIZ / "data" / "raw" / "mec_escuelas" / "instituciones_20261015.csv"
PUENTE_DISTRITOS = RAIZ / "data" / "clean" / "puente_distritos_2022.csv"
CONTEOS = RAIZ / "data" / "clean" / "titulos_conteos.parquet"
ANEAES = RAIZ / "data" / "clean" / "aneaes_programas.parquet"
WEB = RAIZ / "data" / "clean" / "ubicaciones_web_instituciones.csv"
VALIDACION = RAIZ / "data" / "clean" / "validacion_instituciones.csv"
SALIDA = RAIZ / "data" / "clean" / "puente_titulos_institucion.csv"
SALIDA_PESOS = RAIZ / "data" / "clean" / "titulos_institucion_distrito.csv"
DESDE, HASTA = 2013, 2025
ANIO_CAMPUS = "2018"
UMBRAL_ACEPTA = 0.80
VENTAJA = 0.10
UMBRAL_REVISAR = 0.60
UMBRAL_SEGURO = 0.90  # los cruces por similitud entre 0,80 y 0,90 se asignan (regla D17) pero quedan marcados para revisión
ABREVIATURAS = {
    "UNIV": "UNIVERSIDAD", "UNIVERS": "UNIVERSIDAD", "INST": "INSTITUTO", "TEC": "TECNICO", "TECN": "TECNICO",
    "NTRA": "NUESTRA", "SRA": "SENORA", "FORM": "FORMACION", "DOC": "DOCENTE", "SUP": "SUPERIOR",
    "PRIV": "PRIVADA", "NAC": "NACIONAL", "EDUC": "EDUCACION", "GRAL": "GENERAL", "MCAL": "MARISCAL", "DR": "DOCTOR",
    "REG": "REGIONAL", "ESC": "ESCUELA",
}
ALIAS_DISTRITOS = {  # nombres del listado del MEC que no se parecen al de la tabla de distritos
    ("BOQUERON", "FERNHEIM"): "FILADELFIA",  # la colonia Fernheim tiene su centro en Filadelfia
    ("CORDILLERA", normalizar("1º DE MARZO")): "PRIMERO DE MARZO",
}
UMBRAL_DISTRITO = 0.6
PESO_ANEAES = 1e-4  # los programas acreditados solo desempatan la sede principal: nunca superan una fila entera del MEC
ALIAS_SEDES = {"SAN PEDRO DEL YCAMANDYYU": ("SAN PEDRO", "SAN PEDRO")}
VACIAS = {"DE", "DEL", "LA", "EL", "LOS", "LAS", "Y", "PARA", "EN", "E"}
MARCAS_LUGAR = {"CAMPUS", "UNIVERSITARIO", "SEDE", "SUBSEDE", "FILIAL", "UNIDAD", "ACADEMICA", "EXTENSION", "REGIONAL",
               "DISTRITO", "DEPARTAMENTO", "DPTO"}
CONECTORES = {"DE", "DEL", "LA", "EL", "EN"}


def partir(institucion: str) -> tuple[str, str]:
    """Separa el nombre en (base, lugar): por « - » o por una marca (CAMPUS, SEDE, SUBSEDE, FILIAL). Ambos normalizados."""
    t = re.sub(r"\s+", " ", str(institucion)).strip()
    partes = re.split(r"\s+[-–—]\s+", t, maxsplit=1)
    if len(partes) == 2:
        return normalizar(partes[0]), normalizar(partes[1])
    n = normalizar(t)
    m = re.search(r"\b(CAMPUS|SEDE|SUBSEDE|FILIAL)\b", n)
    if m:
        return n[: m.start()].strip(), n[m.start():].strip()
    return n, ""


def palabras(nombre: str) -> frozenset[str]:
    """Conjunto de palabras del nombre normalizado, con abreviaturas expandidas y sin palabras vacías."""
    out = set()
    for p in normalizar(nombre).split():
        p = ABREVIATURAS.get(p, p)
        if p not in VACIAS:
            out.add(p)
    return frozenset(out)


def jaccard(a: frozenset[str], b: frozenset[str]) -> float:
    return len(a & b) / len(a | b) if a and b else 0.0


def lugar_limpio(lugar: str) -> str:
    """Quita las palabras de marca (CAMPUS, SEDE, FILIAL...) y los conectores del comienzo; deja el nombre del lugar."""
    p = [x for x in normalizar(lugar).split() if x not in MARCAS_LUGAR]
    while p and p[0] in CONECTORES:
        p = p[1:]
    return " ".join(p)


# ---------------------------------------------------------------- lectura
def contar_titulos(zip_ruta: Path = TITULOS_ZIP, desde: int = DESDE, hasta: int = HASTA) -> pd.DataFrame:
    """Conteos por año, mes, carrera, título e institución. El archivo con personas se extrae a una carpeta temporal que se borra."""
    with tempfile.TemporaryDirectory() as tmp, zipfile.ZipFile(zip_ruta) as z:
        nombre = z.namelist()[0]
        z.extract(nombre, tmp)
        ruta = (Path(tmp) / nombre).as_posix()
        con = duckdb.connect()
        df = con.sql(f"""
            select try_cast(anio as int) anio, try_cast(mes as int) mes, carrera_id, carrera, titulo_id, titulo,
                   institucion_id, institucion, tipo_institucion, count(*) titulos
            from read_csv_auto('{ruta}', all_varchar=true)
            where try_cast(anio as int) between {desde} and {hasta}
            group by all
        """).df()
        con.close()
    return df


def leer_campus(ruta: Path = INSTITUCIONES, anio: str = ANIO_CAMPUS) -> pd.DataFrame:
    """Filas de educación superior del listado del MEC (un campus por fila) con la base del nombre y el departamento normalizado."""
    con = duckdb.connect()
    df = con.sql(f"""
        select codigo_establecimiento, nombre_institucion, nombre_departamento, nombre_distrito
        from read_csv_auto('{Path(ruta).as_posix()}', all_varchar=true, sample_size=-1)
        where anio = '{anio}' and upper(niveles_modalidades) like '%SUPERIOR%'
    """).df()
    con.close()
    df["base"] = [partir(n)[0] for n in df["nombre_institucion"]]
    df["dep"] = [departamento(n) for n in df["nombre_departamento"]]
    df["clave"] = [llave(n) for n in df["nombre_distrito"]]
    return df.assign(peso_fila=1.0, fuente="mec")


def leer_distritos(ruta: Path = PUENTE_DISTRITOS) -> pd.DataFrame:
    """Distritos del país (nombres de 2022 y de 2012) con su unidad del Censo 2011: dep, clave, distrito, unidad_2011."""
    d = pd.read_csv(ruta)
    filas = []
    for _, r in d.iterrows():
        for col in ("distrito_2022", "distrito_2012"):
            if isinstance(r[col], str) and r[col]:
                filas.append((departamento(r["departamento"]), llave(r[col]),
                              r["distrito_2022"] if isinstance(r["distrito_2022"], str) else r[col], r["unidad_2011"]))
    return pd.DataFrame(filas, columns=["dep", "clave", "distrito", "unidad_2011"]).drop_duplicates(["dep", "clave"])


def resolver_sede(sede: str, distritos: pd.DataFrame) -> tuple[str, str] | None:
    """Lleva la sede de ANEAES a (departamento, clave de distrito). None si no es un distrito único (departamento solo, «No aplica», hospitales)."""
    n = normalizar(re.split(r"\s+[-–—]\s+", str(sede), maxsplit=1)[0])
    if not n or n == "NO APLICA" or n.startswith("UNIDAD"):
        return None
    if n in ALIAS_SEDES:
        return (ALIAS_SEDES[n][0], llave(ALIAS_SEDES[n][1]))
    for dep in sorted(set(distritos["dep"]), key=len, reverse=True):  # «Santa Rosa Misiones»: el departamento al final desambigua
        if n.endswith(" " + dep):
            c = distritos[(distritos["dep"] == dep) & (distritos["clave"] == llave(n[: -len(dep)].strip()))]
            if len(c) == 1:
                return (dep, c.iloc[0]["clave"])
    c = distritos[distritos["clave"] == llave(n)]
    return (c.iloc[0]["dep"], c.iloc[0]["clave"]) if len(c) == 1 else None


def leer_aneaes(distritos: pd.DataFrame, ruta: Path = ANEAES) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Sedes de los programas acreditados por ANEAES, con el mismo formato que el listado del MEC. Devuelve (sedes, no resueltas)."""
    d = pd.read_parquet(ruta)
    g = d.groupby(["institucion", "sede"]).size().rename("programas").reset_index()
    res = [resolver_sede(s, distritos) for s in g["sede"]]
    g["ok"] = [r is not None for r in res]
    ok = g[g["ok"]].copy()
    ok["dep"] = [r[0] for r in res if r is not None]
    ok["clave"] = [r[1] for r in res if r is not None]
    ok["base"] = [partir(n)[0] for n in ok["institucion"]]
    ok["nombre_distrito"] = ok["sede"]
    ok["nombre_institucion"] = ok["institucion"]
    ok = ok.groupby(["nombre_institucion", "base", "dep", "clave", "nombre_distrito"], as_index=False)["programas"].sum()
    ok = ok.assign(peso_fila=ok["programas"] * PESO_ANEAES, fuente="aneaes").drop(columns="programas")
    return ok, g[~g["ok"]][["institucion", "sede", "programas"]]


def leer_web(distritos: pd.DataFrame, ruta: Path = WEB) -> dict[str, list[tuple[str, str]]]:
    """Ubicaciones buscadas en la web: {nombre normalizado: [(dep, clave), ...]} con la sede central primero."""
    if not Path(ruta).exists():
        return {}
    w = pd.read_csv(ruta, dtype=str).fillna("")
    conocidas = set(zip(distritos["dep"], distritos["clave"], strict=True))
    out: dict[str, list[tuple[str, str]]] = {}
    for r in w.itertuples():
        sedes = []
        for s in str(r.sedes).split(";"):
            if "/" in s:
                dep, dist = s.split("/", 1)
                k = (departamento(dep), llave(dist))
                if k in conocidas:
                    sedes.append(k)
        if sedes:
            out[normalizar(r.nom)] = sedes
    return out


def leer_validadas(ruta: Path = VALIDACION) -> dict[str, str]:
    """Cruces validados por el equipo: {nombre normalizado del registro: nombre de la institución del MEC o ANEAES} (solo validado = si)."""
    if not Path(ruta).exists():
        return {}
    v = pd.read_csv(ruta, dtype=str).fillna("")
    v = v[v["validado"].str.strip().str.lower().isin(["si", "sí"])]
    return {normalizar(n): b for n, b in zip(v["nom"], v["base_mec"], strict=True) if b}


def ajustar_distritos(campus: pd.DataFrame, distritos: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Empareja los distritos del listado del MEC que se escriben distinto en la tabla de distritos (similitud dentro del departamento)."""
    conocidas = set(zip(distritos["dep"], distritos["clave"], strict=True))
    ajustes, nuevo = [], {}
    for dep, nombre, clave in campus[["dep", "nombre_distrito", "clave"]].drop_duplicates().itertuples(index=False):
        if (dep, clave) in conocidas:
            continue
        opciones = distritos[distritos["dep"] == dep]
        alias = ALIAS_DISTRITOS.get((dep, normalizar(nombre)))
        if alias:
            destino, sim = llave(alias), 1.0
        elif len(opciones):
            sims = [(SequenceMatcher(None, clave, c).ratio(), c) for c in opciones["clave"]]
            sim, destino = max(sims)
        else:
            sim, destino = 0.0, ""
        if sim >= UMBRAL_DISTRITO and (dep, destino) in conocidas:
            nuevo[(dep, clave)] = destino
            ajustes.append((dep, nombre, destino, round(sim, 2)))
        else:
            ajustes.append((dep, nombre, "", round(sim, 2)))
    campus = campus.copy()
    campus["clave"] = [nuevo.get((d, c), c) for d, c in zip(campus["dep"], campus["clave"], strict=True)]
    return campus, pd.DataFrame(ajustes, columns=["departamento", "distrito_mec", "clave_tabla", "similitud"])


# ---------------------------------------------------------------- reglas
def cruzar_base(base: str, bases_mec: dict[str, frozenset[str]]) -> tuple[str, str | None, float, str | None]:
    """Devuelve (método, base del MEC, similitud, candidato a revisar). Método: exacto, similitud, revisar o sin_cruce."""
    if base in bases_mec:
        return "exacto", base, 1.0, None
    p = palabras(base)
    puntajes = sorted(((jaccard(p, q), b) for b, q in bases_mec.items()), reverse=True)
    if not puntajes or puntajes[0][0] < UMBRAL_REVISAR:
        return "sin_cruce", None, puntajes[0][0] if puntajes else 0.0, None
    mejor, segundo = puntajes[0], (puntajes[1][0] if len(puntajes) > 1 else 0.0)
    if mejor[0] >= UMBRAL_ACEPTA and mejor[0] - segundo >= VENTAJA:
        return "similitud", mejor[1], mejor[0], None
    return "revisar", None, mejor[0], mejor[1]


def resolver_lugar(lugar: str, deps_pista: set[str], distritos: pd.DataFrame, distritos_campus: set[tuple[str, str]]):
    """Resuelve el lugar del nombre: ('distrito', dep, clave), ('departamento', dep) o None si no es un lugar reconocible."""
    txt = lugar_limpio(lugar)
    if not txt:
        return None
    clave = llave(txt)
    cand = distritos[distritos["clave"] == clave]
    if len(cand) > 1 and deps_pista:
        cand = cand[cand["dep"].isin(deps_pista)]
    if len(cand) > 1:
        en_campus = cand[[(a, b) in distritos_campus for a, b in zip(cand["dep"], cand["clave"])]]
        cand = en_campus if len(en_campus) else cand
    if len(cand) == 1:
        return ("distrito", cand.iloc[0]["dep"], cand.iloc[0]["clave"])
    if len(cand) == 0:
        deps = {departamento(txt)}
        if deps & set(distritos["dep"]):
            return ("departamento", next(iter(deps)))
    return None


def sede_principal(filas: pd.Series, dep_nombre: dict[tuple[str, str], str]) -> tuple[tuple[str, str], bool]:
    """Distrito con más filas; en empate, el que lleva el nombre de su departamento (o Asunción). Devuelve (dep, clave) y si hubo empate."""
    mx = filas.max()
    top = [k for k, v in filas.items() if v == mx]
    if len(top) == 1:
        return top[0], False
    asuncion = [k for k in top if k[0] == "ASUNCION"]
    capital = asuncion or [k for k in top if k[1] == llave(k[0])]
    return (capital[0] if capital else min(top)), True


def construir(conteos: pd.DataFrame, campus: pd.DataFrame, distritos: pd.DataFrame,
              web: dict[str, list[tuple[str, str]]] | None = None,
              validadas: dict[str, str] | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Una fila por institución del registro (nombre normalizado) y los pesos por distrito en los escenarios principal y parejo."""
    web = web or {}
    validadas = validadas or {}
    if "peso_fila" not in campus:
        campus = campus.assign(peso_fila=1.0, fuente="mec")
    reg = conteos.assign(nom=[normalizar(x) for x in conteos["institucion"]])
    por_nom = reg.groupby("nom").agg(titulos=("titulos", "sum"), institucion=("institucion", "first"),
                                     institucion_ids=("institucion_id", lambda s: "|".join(sorted(set(s))))).reset_index()
    grupos: dict[frozenset[str], str] = {}
    base_canonica = {}
    for b in campus["base"].unique():
        base_canonica[b] = grupos.setdefault(palabras(b), b)  # nombres del MEC con las mismas palabras son la misma institución
    campus = campus.assign(base=campus["base"].map(base_canonica))
    filas_mec = campus.groupby(["base", "dep", "clave"])["peso_fila"].sum()
    fuentes = campus.groupby("base")["fuente"].agg(lambda s: "+".join(sorted(set(s)))).to_dict()
    bases_mec = {b: palabras(b) for b in filas_mec.index.get_level_values(0).unique()}
    nombre_dist = {(r.dep, r.clave): r.distrito for r in distritos.itertuples()}
    unidad = {(r.dep, r.clave): r.unidad_2011 for r in distritos.itertuples()}
    filas, pesos = [], []
    for r in por_nom.itertuples():
        base, lugar = partir(r.institucion)
        metodo, base_mec, sim, candidato = cruzar_base(base, bases_mec)
        if r.nom in validadas and validadas[r.nom] in bases_mec and metodo in ("revisar", "sin_cruce"):
            metodo, base_mec, sim, candidato = "validado", validadas[r.nom], max(sim, 0.0), None
        campus_filas = filas_mec[base_mec] if base_mec else pd.Series(dtype=int)
        claves = {(d, c): v for (d, c), v in campus_filas.items()}
        res = resolver_lugar(lugar, {d for d, _ in claves}, distritos, set(claves)) if lugar else None
        nota, revisar = "", False
        asig: list[tuple[tuple[str, str], float]] = []
        asig_par: list[tuple[tuple[str, str], float]] = []
        if res and res[0] == "distrito":
            k = (res[1], res[2])
            asig = asig_par = [(k, 1.0)]
            conf, met = "alta", "lugar_en_nombre"
        elif res and res[0] == "departamento" and claves:
            en_dep = pd.Series({k: v for k, v in claves.items() if k[0] == res[1]})
            if len(en_dep):
                k, emp = sede_principal(en_dep, nombre_dist)
                asig = [(k, 1.0)]
                asig_par = [(kk, 1 / len(en_dep)) for kk in en_dep.index]
                conf, met, revisar = "media", "departamento_en_nombre", emp or len(en_dep) > 1
            else:
                conf, met = "baja", "sin_ubicar"
        elif claves:
            if lugar:
                nota = "el sufijo del nombre no es un lugar reconocible (facultad u otro)"
            if len(claves) == 1:
                asig = asig_par = [(next(iter(claves)), 1.0)]
                alta = metodo == "exacto" and "mec" in fuentes.get(base_mec, "")  # solo ANEAES muestra programas acreditados: nunca alta
                conf, met = ("alta" if alta else "media"), f"{metodo}_una_sede"
            else:
                k, emp = sede_principal(pd.Series(claves), nombre_dist)
                asig = [(k, 1.0)]
                asig_par = [(kk, 1 / len(claves)) for kk in claves]
                conf, met, revisar = "baja", f"{metodo}_sede_principal", emp
                if emp:
                    nota = (nota + "; " if nota else "") + "empate de filas entre distritos"
        elif r.nom in web:
            sedes = web[r.nom]
            asig = [(sedes[0], 1.0)]
            asig_par = [(k, 1 / len(sedes)) for k in sedes]
            conf, met = ("media" if len(sedes) == 1 else "baja"), "web"
            claves = dict.fromkeys(sedes, 1.0)
        else:
            conf, met = "", "sin_cruce" if metodo != "revisar" else "candidato_a_revisar"
        filas.append({
            "nom": r.nom, "institucion": r.institucion, "institucion_ids": r.institucion_ids, "titulos": r.titulos,
            "metodo_cruce": metodo, "metodo_ubicacion": met, "similitud": round(sim, 3), "base_mec": base_mec or "", "fuentes_campus": fuentes.get(base_mec, "") if base_mec else ("web" if r.nom in web else ""),
            "candidato": candidato or "",
            "distritos_candidato": "; ".join(sorted(nombre_dist.get(k, k[1]) for k in filas_mec[candidato].index)) if candidato else "",
            "lugar_en_nombre": lugar, "n_distritos_campus": len({c for c in claves}),
            "distrito_principal": nombre_dist.get(asig[0][0], asig[0][0][1]) if asig else "",
            "departamento": asig[0][0][0] if asig else "", "unidad_2011": unidad.get(asig[0][0], "") if asig else "",
            "confianza": conf, "revisar": revisar or met in ("candidato_a_revisar", "sin_cruce") or (metodo == "similitud" and sim < UMBRAL_SEGURO) or fuentes.get(base_mec, "") == "aneaes", "nota": nota,
        })
        for esc, lista in (("principal", asig), ("parejo", asig_par)):
            for (dep, clave), w in lista:
                pesos.append({"nom": r.nom, "escenario": esc, "departamento": dep,
                              "distrito": nombre_dist.get((dep, clave), clave), "unidad_2011": unidad.get((dep, clave), ""),
                              "peso": w, "confianza": conf})
    return pd.DataFrame(filas), pd.DataFrame(pesos)


def resumen(puente: pd.DataFrame) -> pd.DataFrame:
    """Títulos por método de ubicación y confianza, con su porcentaje."""
    tot = puente["titulos"].sum()
    g = puente.groupby(["metodo_ubicacion", "confianza"], dropna=False).agg(
        instituciones=("nom", "count"), titulos=("titulos", "sum")).reset_index()
    g["pct_titulos"] = (100 * g["titulos"] / tot).round(1)
    return g.sort_values("titulos", ascending=False)


def sensibilidad(puente: pd.DataFrame, pesos: pd.DataFrame) -> pd.DataFrame:
    """Títulos por departamento con la sede principal y con el reparto parejo, y cuánto cambia entre ambos escenarios."""
    base = pesos.merge(puente[["nom", "titulos"]], on="nom")
    base["t"] = base["titulos"] * base["peso"]
    tab = base.pivot_table(index="departamento", columns="escenario", values="t", aggfunc="sum", fill_value=0).reset_index()
    tab["diferencia"] = tab["parejo"] - tab["principal"]
    return tab.sort_values("principal", ascending=False)


def main() -> None:
    conteos = contar_titulos()
    conteos.to_parquet(CONTEOS, index=False)
    campus = leer_campus()
    distritos = leer_distritos()
    campus, ajustes = ajustar_distritos(campus, distritos)
    aneaes, aneaes_sin = leer_aneaes(distritos)
    campus = pd.concat([campus, aneaes], ignore_index=True)
    aneaes_sin.to_csv(RAIZ / "data" / "clean" / "titulos_aneaes_sedes_sin_distrito.csv", index=False, encoding="utf-8")
    puente, pesos = construir(conteos, campus, distritos, leer_web(distritos), leer_validadas())
    if not VALIDACION.exists():  # planilla para el equipo; si ya existe no se pisa
        plan = puente[puente["metodo_ubicacion"] == "candidato_a_revisar"].sort_values("titulos", ascending=False)
        plan = plan[["nom", "institucion", "titulos", "candidato", "similitud", "distritos_candidato"]].rename(columns={"candidato": "base_mec"})
        plan.assign(validado="", por="", fecha="", nota="").to_csv(VALIDACION, index=False, encoding="utf-8")
    puente.sort_values("titulos", ascending=False).to_csv(SALIDA, index=False, encoding="utf-8")
    pesos.to_csv(SALIDA_PESOS, index=False, encoding="utf-8")
    sin_distrito = campus[~campus.set_index(["dep", "clave"]).index.isin(distritos.set_index(["dep", "clave"]).index)]
    ajustes.to_csv(RAIZ / "data" / "clean" / "titulos_ajustes_distritos.csv", index=False, encoding="utf-8")
    print(f"ANEAES: {len(aneaes)} sedes con distrito; sin distrito (listadas en titulos_aneaes_sedes_sin_distrito.csv): {len(aneaes_sin)}")
    print("distritos del MEC emparejados por similitud o alias:")
    print(ajustes.to_string(index=False))
    print(f"títulos {int(conteos['titulos'].sum()):,} | instituciones (nombre normalizado) {len(puente)}")
    print(resumen(puente).to_string(index=False))
    sens = sensibilidad(puente, pesos)
    sens.to_csv(RAIZ / "data" / "clean" / "titulos_sensibilidad_departamento.csv", index=False, encoding="utf-8")
    print(f"títulos reubicados entre escenarios: {sens['diferencia'].clip(lower=0).sum() / sens['principal'].sum():.1%} de los ubicados")
    print(f"campus del MEC cuyo distrito no se pudo emparejar con la tabla de distritos: {len(sin_distrito)}")
    if len(sin_distrito):
        print(sin_distrito[["nombre_distrito", "nombre_departamento"]].drop_duplicates().to_string(index=False))


if __name__ == "__main__":
    main()
