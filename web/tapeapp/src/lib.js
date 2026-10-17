// Datos y utilidades de la herramienta TAPE (diagnóstico multi-capa D36/D37, interfaz D38).
// Todo sale de `data/diagnostico.json` y `data/distritos_geo.json`, generados por `src/herramienta/exportar_diagnostico.py`.
import diag from './data/diagnostico.json';
import geoDist from './data/distritos_geo.json';
import gadm from './data/gadm41_PRY_1.json';

export { diag, geoDist, gadm };
export const D = diag.distritos;
export const S = diag.sectores;
export const CE = diag.celdas;
export const CAPAS = diag.meta.capas; // base, formacion, energia, logistica, recursos
export const CLASES = diag.meta.clases;
export const IDX = Object.fromEntries(D.map((d, i) => [d.id, i]));
export const SEC = Object.fromEntries(S.map((s) => [s.id, s]));
export const DEPS = diag.departamentos;

export const NOMBRE_CAPA = {
  base: 'Capital humano (base)',
  formacion: 'Formación específica',
  energia: 'Energía',
  logistica: 'Logística',
  recursos: 'Recursos',
  agricultura: 'Recursos: agricultura',
  pastura: 'Recursos: pastura',
  plantacion_forestal: 'Recursos: plantación forestal',
};
export const NIVEL = ['Mercado', 'Ajuste puntual (privado)', 'Acción colectiva', 'Estado'];
export const ESTADO = { '0': 'sin brecha', '1': 'cerca del umbral', '2': 'con brecha', '-': '' };

// Clases del mapa de calor por actividad (D38, 3A): de más a menos capacidades, más datos incompletos y sin referencia.
export const COLOR_CLASE = {
  light: ['#0b4f52', '#3f9a9c', '#a9d6d4', '#e4eeee', '#c4b09c', '#f1e2a0', '#eef1f3'],
  dark: ['#5cc4c8', '#3b8f92', '#27626a', '#1c3f47', '#6b5646', '#6b5f2e', '#1f2c32'],
};
export const DESCRIPCION_CLASE = [
  'Cumple todas las capas que exige la actividad',
  'Sin brechas, pero al menos una capa a menos de 10 puntos del umbral',
  'Una capa con brecha',
  'Dos o más capas con brecha',
  'Límite duro: no tiene los recursos que exige la actividad',
  'Falta el dato de una capa en este distrito',
  'No hay productores suficientes en Paraguay para comparar',
];

const MINUSCULAS = new Set(['de', 'del', 'la', 'las', 'los', 'y', 'e']);

export function titulo(texto) {
  return String(texto || '')
    .toLowerCase()
    .replace(/(^|[\s.(-])([a-zñ]+)/g, (m, a, b, pos) => a + (pos > 0 && MINUSCULAS.has(b) ? b : b[0].toUpperCase() + b.slice(1)));
}

export function celda(sid, i) {
  const c = CE[sid] && CE[sid][i];
  if (!c) return null;
  return { clase: c[0], yaProduce: c[1] === 1, nBrechas: c[2], margen: c[3], nivel: c[4], estados: c[5], rangoInd: c[6], rangoDist: c[7], escalon: c[8], limitante: c[9] };
}

export function etiquetaEscalon(e) {
  if (e === null || e === undefined) return '';
  return e > 10 ? 'más compleja que lo que produce el distrito' : e < -10 ? 'menos compleja que lo que produce el distrito' : 'similar a lo que produce el distrito';
}

// Índice del distrito en la capa que exige la actividad (la formación específica no se guarda por distrito: solo su estado).
export function indiceCapa(i, sector, capa) {
  const c = D[i].capas;
  if (capa === 'recursos') return c[sector.clase_tierra] ?? null;
  return c[capa] ?? null;
}

export function mediana(valores) {
  const v = valores.filter((x) => x !== null && x !== undefined && !Number.isNaN(x)).sort((a, b) => a - b);
  if (!v.length) return null;
  const m = Math.floor(v.length / 2);
  return v.length % 2 ? v[m] : (v[m - 1] + v[m]) / 2;
}

export const SECTORES_REF = S.filter((s) => s.con_referencia);

// Actividades compatibles: con referencia, que el distrito aún no produce y sin brechas (clases 0 y 1).
export function compatibles(i) {
  return SECTORES_REF.filter((s) => {
    const c = celda(s.id, i);
    return c && !c.yaProduce && c.clase <= 1;
  });
}

export const INDICADORES = [
  { id: 'base', nombre: 'Capital humano (base)', tipo: 'capa' },
  { id: 'energia', nombre: 'Energía', tipo: 'capa' },
  { id: 'logistica', nombre: 'Logística', tipo: 'capa' },
  { id: 'agricultura', nombre: 'Recursos: agricultura', tipo: 'capa' },
  { id: 'pastura', nombre: 'Recursos: pastura', tipo: 'capa' },
  { id: 'plantacion_forestal', nombre: 'Recursos: plantación forestal', tipo: 'capa' },
  { id: 'compatibles', nombre: 'Actividades compatibles que aún no produce', tipo: 'cuenta' },
  { id: 'producen', nombre: 'Actividades que ya produce', tipo: 'cuenta' },
];

const CACHE = {};
export function valorDistrito(i, ind) {
  if (ind === 'compatibles') {
    CACHE.comp = CACHE.comp || D.map((_, k) => compatibles(k).length);
    return CACHE.comp[i];
  }
  if (ind === 'producen') return D[i].produce.length;
  return D[i].capas[ind];
}

export function valorDepartamento(dep, ind) {
  return mediana(D.filter((d) => d.departamento === dep).map((d) => valorDistrito(IDX[d.id], ind)));
}

export function rango(valores) {
  const v = valores.filter((x) => x !== null && x !== undefined);
  return [Math.min(...v), Math.max(...v)];
}

function mezclar(a, b, t) {
  const h = (s) => [1, 3, 5].map((k) => parseInt(s.slice(k, k + 2), 16));
  const [r1, g1, b1] = h(a);
  const [r2, g2, b2] = h(b);
  const c = (x, y) => Math.round(x + (y - x) * t);
  return `rgb(${c(r1, r2)},${c(g1, g2)},${c(b1, b2)})`;
}

// Rampa de un solo tono: claro a oscuro (modo claro) o oscuro a brillante (modo oscuro); más capacidad = más marcado.
export function colorRampa(t, tema) {
  if (t === null || t === undefined || Number.isNaN(t)) return tema === 'dark' ? '#1f2c32' : '#eef1f3';
  const x = Math.max(0, Math.min(1, t));
  return tema === 'dark' ? mezclar('#1c3f47', '#5cc4c8', x) : mezclar('#e4eeee', '#0b4f52', x);
}

// Caja geográfica de un departamento (a partir de sus distritos) → centro y zoom para el mapa.
export function vistaDepartamento(dep) {
  const pts = [];
  const mias = new Set(D.filter((d) => d.departamento === dep).map((d) => d.id));
  const recorrer = (c) => {
    if (typeof c[0] === 'number') pts.push(c);
    else c.forEach(recorrer);
  };
  geoDist.features.filter((f) => mias.has(f.properties.id)).forEach((f) => recorrer(f.geometry.coordinates));
  D.filter((d) => d.departamento === dep && !d.poligono && d.lat !== null).forEach((d) => pts.push([d.lon, d.lat]));
  if (!pts.length) return { center: [-58.4, -23.4], zoom: 1 };
  const lons = pts.map((p) => p[0]);
  const lats = pts.map((p) => p[1]);
  const w = Math.max(...lons) - Math.min(...lons);
  const h = Math.max(...lats) - Math.min(...lats);
  const zoom = Math.min(9, Math.max(1, 0.75 * Math.min(10.5 / Math.max(w, 0.05), 9.5 / Math.max(h, 0.05))));
  return { center: [(Math.max(...lons) + Math.min(...lons)) / 2, (Math.max(...lats) + Math.min(...lats)) / 2], zoom };
}

export const VISTA_PAIS = { center: [-58.4, -23.4], zoom: 1 };
