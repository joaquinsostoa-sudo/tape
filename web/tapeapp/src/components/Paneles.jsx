import React, { useMemo, useState } from 'react';
import { Layers, Factory, Target, AlertTriangle, X, MapPin } from 'lucide-react';
import {
  CAPAS, CLASES, COLOR_CLASE, D, DESCRIPCION_CLASE, ESTADO, IDX, NIVEL, NOMBRE_CAPA, S, SECTORES_REF, SEC, celda, compatibles, etiquetaEscalon, indiceCapa, mediana, titulo,
} from '../lib.js';

const ORDEN_COMPLEJIDAD = ['simple', 'intermedia', 'compleja'];
const ORDEN_RELATIVA = ['menos compleja', 'similar', 'más compleja'];

function Chip({ activo, onClick, children, title }) {
  return (
    <button type="button" className={`chip ${activo ? 'chip-activo' : ''}`} onClick={onClick} title={title}>
      {children}
    </button>
  );
}

function Grupo({ titulo: t, ayuda, opciones, valor, onChange }) {
  const alternar = (o) => onChange(valor.includes(o) ? valor.filter((x) => x !== o) : [...valor, o]);
  return (
    <div className="grupo-filtro">
      <div className="grupo-t" title={ayuda}>{t}</div>
      <div className="chips">
        {opciones.map((o) => (
          <Chip key={o} activo={valor.includes(o)} onClick={() => alternar(o)}>{o}</Chip>
        ))}
      </div>
    </div>
  );
}

// Lista de actividades con filtros por complejidad, complejidad relativa al país y situación en Paraguay (D38, 2A y 4A).
export function ListaActividades({ sectorId, onSelect }) {
  const [complejidad, setComplejidad] = useState([]);
  const [relativa, setRelativa] = useState([]);
  const [situacion, setSituacion] = useState([]);
  const [texto, setTexto] = useState('');
  const pasa = (s) =>
    (!complejidad.length || complejidad.includes(s.complejidad)) &&
    (!relativa.length || relativa.includes(s.relativa)) &&
    (!situacion.length || situacion.includes(s.situacion_pais)) &&
    (!texto || s.nombre.toLowerCase().includes(texto.toLowerCase()));
  const con = SECTORES_REF.filter(pasa).sort((a, b) => b.n_productores - a.n_productores);
  const sin = S.filter((s) => !s.con_referencia && (!texto || s.nombre.toLowerCase().includes(texto.toLowerCase())));
  return (
    <div className="lista">
      <input className="busca" placeholder="Buscar actividad" value={texto} onChange={(e) => setTexto(e.target.value)} />
      <Grupo titulo="Complejidad" ayuda="Tercios del índice de complejidad del producto (PCI) del Atlas, agregado al sector" opciones={ORDEN_COMPLEJIDAD} valor={complejidad} onChange={setComplejidad} />
      <Grupo titulo="Frente a lo que produce Paraguay" ayuda="PCI del sector contra la mediana de las actividades que Paraguay ya produce (±10 puntos de percentil)" opciones={ORDEN_RELATIVA} valor={relativa} onChange={setRelativa} />
      <Grupo titulo="Situación en Paraguay" ayuda="Distritos que hoy la producen según el mapa MIC 2026" opciones={['se produce', 'se produce poco']} valor={situacion} onChange={setSituacion} />
      <div className="lista-n">{con.length} actividades con productores suficientes para comparar</div>
      <div className="filas">
        {con.map((s) => (
          <button type="button" key={s.id} className={`fila ${s.id === sectorId ? 'fila-activa' : ''}`} onClick={() => onSelect(s.id)}>
            <div className="fila-nombre">{s.nombre}</div>
            <div className="fila-meta">
              <span className="mini">{s.complejidad || 'sin PCI'}</span>
              <span className="mini">{s.relativa || ''}</span>
              <span className="mini">{s.n_productores} distritos la producen</span>
              <span className="mini">{s.capas.length} {s.capas.length === 1 ? 'capa' : 'capas'}</span>
            </div>
          </button>
        ))}
      </div>
      <details className="sin-ref">
        <summary>Sin productores suficientes para comparar ({sin.length})</summary>
        <div className="nota">En Paraguay hay menos de 5 distritos con estas actividades en el mapa MIC (que solo cubre industrias): no hay con qué compararlas.</div>
        {sin.map((s) => (
          <div key={s.id} className="fila fila-apagada" title="Sin productores suficientes en Paraguay para comparar">
            <div className="fila-nombre">{s.nombre}</div>
          </div>
        ))}
      </details>
    </div>
  );
}

function Barra({ nombre, valor, extra }) {
  return (
    <div className="barra-fila">
      <div className="barra-nombre">{nombre}</div>
      <div className="barra-pista">
        <div className="barra-relleno" style={{ width: `${valor === null || valor === undefined ? 0 : valor}%` }} />
      </div>
      <div className="barra-valor">{valor === null || valor === undefined ? 'sin dato' : Math.round(valor)}{extra}</div>
    </div>
  );
}

function Estado({ e }) {
  return <span className={`estado estado-${e}`}>{ESTADO[e]}</span>;
}

function Actor({ celdaS }) {
  if (!celdaS) return null;
  if (celdaS.clase === 4) return <span className="actor actor-duro">Límite duro: no tiene los recursos que exige</span>;
  if (celdaS.nivel < 0) return null;
  return <span className="actor">Quién actúa: {NIVEL[celdaS.nivel]}</span>;
}

function BloqueActividad({ sector, i }) {
  const c = celda(sector.id, i);
  if (!c) return null;
  const hayRango = c.rangoInd !== null && c.rangoInd !== undefined;
  const total = D.filter((_, k) => celda(sector.id, k)?.rangoInd).length;
  return (
    <div className="bloque">
      <div className="bloque-t"><Factory size={14} /> {sector.nombre}</div>
      <div className="clase-txt" title={DESCRIPCION_CLASE[c.clase]}>{CLASES[c.clase]}{c.yaProduce ? ' · ya se produce acá' : ' · aún no se produce acá'}</div>
      {sector.capas.map((capa) => {
        const pos = CAPAS.indexOf(capa);
        const e = c.estados[pos];
        const idx = indiceCapa(i, sector, capa);
        const umbral = sector.umbrales[capa];
        return (
          <div key={capa} className="capa-fila">
            <span>{NOMBRE_CAPA[capa === 'recursos' ? sector.clase_tierra || 'recursos' : capa]}</span>
            <span className="capa-num">
              {idx !== null && idx !== undefined ? `${Math.round(idx)}` : ''}
              {umbral !== null && umbral !== undefined ? ` / umbral ${Math.round(umbral)}` : ' / sin referencia'}
            </span>
            <Estado e={e} />
          </div>
        );
      })}
      <div className="bloque-pie">
        <Actor celdaS={c} />
        {c.escalon !== null && c.escalon !== undefined && <span className="mini">Complejidad: {etiquetaEscalon(c.escalon)}</span>}
        {hayRango && <span className="mini">Puesto {c.rangoInd} de {total} distritos comparables</span>}
        {c.limitante && c.clase >= 2 && c.clase <= 3 && <span className="mini">Capa que más limita: {NOMBRE_CAPA[c.limitante] || c.limitante}</span>}
      </div>
      {sector.capas.length === 1 && <div className="aviso-leve">Esta actividad exige una sola capa (capital humano): aparece viable en casi todos lados, y esa afirmación es débil.</div>}
      {Object.values(sector.confianza).includes('baja') && <div className="aviso-leve">La referencia se apoya en 5 a 9 distritos productores: confianza baja.</div>}
      {sector.capas_sin_dato.length > 0 && <div className="aviso-leve">No se pudo medir: {sector.capas_sin_dato.map((x) => NOMBRE_CAPA[x] || x).join(', ')} (sin dato, no se imputa).</div>}
    </div>
  );
}

function ListaSectores({ items, onSector, vacio, i, mostrar = 12 }) {
  const [todos, setTodos] = useState(false);
  const ver = todos ? items : items.slice(0, mostrar);
  if (!items.length) return <div className="nota">{vacio}</div>;
  return (
    <div>
      {ver.map(({ s, c }) => (
        <button type="button" key={s.id} className="fila fila-chica" onClick={() => onSector(s.id)}>
          <div className="fila-nombre">{s.nombre}</div>
          <div className="fila-meta">
            <span className="mini">{c.clase <= 1 ? CLASES[c.clase] : `${c.nBrechas} ${c.nBrechas === 1 ? 'brecha' : 'brechas'}`}</span>
            {c.limitante && c.clase >= 2 && <span className="mini">limita: {NOMBRE_CAPA[c.limitante] || c.limitante}</span>}
            {c.nivel >= 0 && <span className="mini">actúa: {NIVEL[c.nivel]}</span>}
            {c.escalon !== null && c.escalon !== undefined && <span className="mini">{etiquetaEscalon(c.escalon).split(' ')[0]} {etiquetaEscalon(c.escalon).startsWith('similar') ? '' : 'compleja'}</span>}
            <span className="mini">{s.capas.length} {s.capas.length === 1 ? 'capa' : 'capas'}</span>
          </div>
        </button>
      ))}
      {items.length > mostrar && (
        <button type="button" className="ver-mas" onClick={() => setTodos(!todos)}>{todos ? 'Ver menos' : `Ver las ${items.length}`}</button>
      )}
    </div>
  );
}

// Ficha de un distrito (D38): capas, lo que ya produce, lo que podría desarrollarse y lo que le falta.
export function FichaDistrito({ id, sectorId, onClose, onSector, onDepartamento }) {
  const [tab, setTab] = useState('capacidades');
  const [filtro, setFiltro] = useState('todas');
  const i = IDX[id];
  const d = D[i];
  const sector = sectorId ? SEC[sectorId] : null;
  const oportunidades = useMemo(() => {
    const base = compatibles(i).map((s) => ({ s, c: celda(s.id, i) })).sort((a, b) => (a.c.rangoDist ?? 1e9) - (b.c.rangoDist ?? 1e9));
    if (filtro === 'todas') return base;
    if (filtro === 'más compleja') return base.filter(({ c }) => c.escalon !== null && c.escalon > 10);
    return base.filter(({ s }) => s.complejidad === filtro);
  }, [i, filtro]);
  const brechas = useMemo(
    () =>
      SECTORES_REF.map((s) => ({ s, c: celda(s.id, i) }))
        .filter(({ c }) => c && !c.yaProduce && (c.clase === 2 || c.clase === 3))
        .sort((a, b) => a.c.nBrechas - b.c.nBrechas || b.c.margen - a.c.margen),
    [i],
  );
  const tabs = [
    { id: 'capacidades', label: 'Capacidades', icon: Layers },
    { id: 'produce', label: 'Ya produce', icon: Factory },
    { id: 'oportunidades', label: 'Podría desarrollar', icon: Target },
    { id: 'brechas', label: 'Le faltan', icon: AlertTriangle },
  ];
  return (
    <div className="ficha">
      <div className="ficha-cab">
        <div>
          <div className="ficha-tipo">Distrito</div>
          <h2>{titulo(d.nombre)}</h2>
          <button type="button" className="enlace" onClick={() => onDepartamento(d.departamento)}><MapPin size={12} /> {titulo(d.departamento)}</button>
          {d.poblacion !== null && <span className="mini"> · {d.poblacion.toLocaleString('es-PY')} habitantes (2022)</span>}
        </div>
        <button type="button" className="cerrar" onClick={onClose} aria-label="Cerrar"><X size={16} /></button>
      </div>
      {!d.poligono && <div className="aviso-leve">Distrito creado después de 2012{d.padre && d.padre !== 'nan' ? ` (dentro de ${titulo(d.padre)})` : ''}: sin contorno propio, se dibuja como punto.</div>}
      {sector && <BloqueActividad sector={sector} i={i} />}
      <div className="tabs">
        {tabs.map((t) => (
          <button type="button" key={t.id} className={`tab ${tab === t.id ? 'tab-activa' : ''}`} onClick={() => setTab(t.id)}>
            <t.icon size={13} /> {t.label}
          </button>
        ))}
      </div>
      {tab === 'capacidades' && (
        <div className="bloque">
          <div className="nota">Posición del distrito entre los 263 (percentil 0 a 100; 100 es lo mejor). Lo que hay cerca también cuenta, con un peso que baja con la distancia (escala de 30 km).</div>
          {Object.entries(d.capas).map(([k, v]) => <Barra key={k} nombre={NOMBRE_CAPA[k === 'base' ? 'base' : k] || k} valor={v} />)}
        </div>
      )}
      {tab === 'produce' && (
        <div className="bloque">
          <div className="nota">Actividades con al menos una industria en este distrito (mapa MIC 2026, una foto, no una serie).</div>
          {d.produce.length === 0 && <div className="nota">No hay industrias registradas en este distrito.</div>}
          {d.produce.map((sid) => (
            <button type="button" key={sid} className="fila fila-chica" disabled={!SEC[sid]?.con_referencia} onClick={() => SEC[sid]?.con_referencia && onSector(sid)}>
              <div className="fila-nombre">{SEC[sid]?.nombre || sid}</div>
            </button>
          ))}
        </div>
      )}
      {tab === 'oportunidades' && (
        <div className="bloque">
          <div className="nota">Actividades que el distrito aún no tiene y para las que cumple, o casi cumple, lo que tienen quienes ya producen. Es una comparación, no una predicción: no dice que vaya a desarrollarse.</div>
          <select className="selector" value={filtro} onChange={(e) => setFiltro(e.target.value)}>
            <option value="todas">Todas</option>
            <option value="simple">Simples</option>
            <option value="intermedia">Intermedias</option>
            <option value="compleja">Complejas</option>
            <option value="más compleja">Más complejas que lo que produce el distrito</option>
          </select>
          <ListaSectores items={oportunidades} onSector={onSector} vacio="Ninguna actividad cumple con esos filtros." i={i} />
        </div>
      )}
      {tab === 'brechas' && (
        <div className="bloque">
          <div className="nota">Actividades con una o dos brechas frente a quienes ya producen, con la capa que más limita y quién debe actuar (mercado, acción colectiva o Estado).</div>
          <ListaSectores items={brechas} onSector={onSector} vacio="No hay actividades con brechas en este rango." i={i} />
        </div>
      )}
    </div>
  );
}

// Ficha de un departamento: agregado de sus distritos (los datos entran a nivel distrito; no se inventan datos departamentales).
export function FichaDepartamento({ nombre, onClose, onDistrito, onSector }) {
  const ds = D.map((d, i) => ({ d, i })).filter(({ d }) => d.departamento === nombre);
  const capas = Object.keys(ds[0].d.capas).map((k) => ({ k, v: mediana(ds.map(({ d }) => d.capas[k])) }));
  const cuenta = (filtro) => {
    const m = {};
    ds.forEach(({ i }) => SECTORES_REF.forEach((s) => {
      const c = celda(s.id, i);
      if (c && filtro(c)) m[s.id] = (m[s.id] || 0) + 1;
    }));
    return Object.entries(m).sort((a, b) => b[1] - a[1]).slice(0, 8);
  };
  const compat = cuenta((c) => !c.yaProduce && c.clase <= 1);
  const produce = cuenta((c) => c.yaProduce);
  return (
    <div className="ficha">
      <div className="ficha-cab">
        <div>
          <div className="ficha-tipo">Departamento</div>
          <h2>{titulo(nombre)}</h2>
          <span className="mini">{ds.length} distritos · {ds.reduce((a, { d }) => a + (d.poblacion || 0), 0).toLocaleString('es-PY')} habitantes (2022)</span>
        </div>
        <button type="button" className="cerrar" onClick={onClose} aria-label="Cerrar"><X size={16} /></button>
      </div>
      <div className="bloque">
        <div className="bloque-t"><Layers size={14} /> Capacidades (mediana de sus distritos)</div>
        {capas.map(({ k, v }) => <Barra key={k} nombre={NOMBRE_CAPA[k] || k} valor={v} />)}
      </div>
      <div className="bloque">
        <div className="bloque-t"><Factory size={14} /> Actividades que más distritos producen</div>
        {produce.map(([sid, n]) => (
          <button type="button" key={sid} className="fila fila-chica" onClick={() => onSector(sid)}>
            <div className="fila-nombre">{SEC[sid].nombre}</div><div className="fila-meta"><span className="mini">{n} de {ds.length} distritos</span></div>
          </button>
        ))}
      </div>
      <div className="bloque">
        <div className="bloque-t"><Target size={14} /> Actividades compatibles en más distritos que aún no las tienen</div>
        <div className="nota">Distritos que aún no la producen y no tienen brechas frente a quienes sí. Es una comparación, no una predicción.</div>
        {compat.length === 0 && <div className="nota">Ninguna.</div>}
        {compat.map(([sid, n]) => (
          <button type="button" key={sid} className="fila fila-chica" onClick={() => onSector(sid)}>
            <div className="fila-nombre">{SEC[sid].nombre}</div><div className="fila-meta"><span className="mini">{n} de {ds.length} distritos</span></div>
          </button>
        ))}
      </div>
      <div className="bloque">
        <div className="bloque-t"><MapPin size={14} /> Distritos</div>
        <div className="chips">
          {ds.map(({ d }) => <Chip key={d.id} onClick={() => onDistrito(d.id)}>{titulo(d.nombre)}</Chip>)}
        </div>
      </div>
    </div>
  );
}

// Resumen de la actividad elegida (cuando no hay un distrito seleccionado).
export function ResumenActividad({ sectorId, onDistrito }) {
  const s = SEC[sectorId];
  const celdas = D.map((d, i) => ({ d, c: celda(sectorId, i) })).filter(({ c }) => c);
  const top = celdas.filter(({ c }) => c.rangoInd).sort((a, b) => a.c.rangoInd - b.c.rangoInd).slice(0, 10);
  const colores = COLOR_CLASE.light;
  return (
    <div className="ficha">
      <div className="ficha-cab">
        <div>
          <div className="ficha-tipo">Actividad</div>
          <h2>{s.nombre}</h2>
          <div className="fila-meta">
            <span className="mini">{s.complejidad || 'sin PCI'}</span>
            <span className="mini">{s.relativa}</span>
            <span className="mini">{s.n_productores} distritos la producen</span>
          </div>
        </div>
      </div>
      <div className="bloque">
        <div className="bloque-t"><Layers size={14} /> Capas que exige y estándar de comparación</div>
        <div className="nota">El estándar es el percentil 10 de los distritos que hoy producen la actividad. «Cumple» significa tener lo que tienen quienes producen.</div>
        {s.capas.map((capa) => (
          <div key={capa} className="capa-fila">
            <span>{NOMBRE_CAPA[capa === 'recursos' ? s.clase_tierra || 'recursos' : capa]}</span>
            <span className="capa-num">{s.umbrales[capa] !== null && s.umbrales[capa] !== undefined ? `umbral ${Math.round(s.umbrales[capa])}` : 'sin referencia'}</span>
            <span className="mini">confianza {s.confianza[capa] || '—'}</span>
          </div>
        ))}
        {s.capas.length === 1 && <div className="aviso-leve">Exige una sola capa: aparece viable en casi todos lados, y esa afirmación es débil.</div>}
      </div>
      <div className="bloque">
        <div className="bloque-t"><Target size={14} /> Distritos más compatibles</div>
        <div className="nota">Orden: sin límite duro de recursos, menos brechas y mayor margen sobre el umbral. Tocá uno para ver su ficha.</div>
        {top.map(({ d, c }) => (
          <button type="button" key={d.id} className="fila fila-chica" onClick={() => onDistrito(d.id)}>
            <div className="fila-nombre"><span className="muestra" style={{ background: colores[c.clase] }} /> {titulo(d.nombre)} <span className="mini">({titulo(d.departamento)})</span></div>
            <div className="fila-meta"><span className="mini">{CLASES[c.clase]}</span><span className="mini">{c.yaProduce ? 'ya la produce' : 'no la produce'}</span></div>
          </button>
        ))}
      </div>
    </div>
  );
}
