import React, { useEffect, useState } from 'react';
import { Info, Map as MapIcon, Moon, Sun, Factory, X } from 'lucide-react';
import './styles.css';
import Mapa from './components/Mapa.jsx';
import { FichaDepartamento, FichaDistrito, ListaActividades, ResumenActividad } from './components/Paneles.jsx';
import { D, DEPS, INDICADORES, SEC, VISTA_PAIS, diag, titulo, valorDepartamento, vistaDepartamento } from './lib.js';

const pais = () => ({ ...VISTA_PAIS, clave: Date.now() });

export default function App() {
  const [tema, setTema] = useState(() => (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'));
  const [modo, setModo] = useState('actividad');
  const [sectorId, setSectorId] = useState(null);
  const [indicador, setIndicador] = useState('base');
  const [depSel, setDepSel] = useState(null);
  const [distSel, setDistSel] = useState(null);
  const [vista, setVista] = useState(pais());
  const [aviso, setAviso] = useState(false);

  useEffect(() => {
    document.documentElement.dataset.theme = tema;
  }, [tema]);

  const elegirModo = (m) => {
    setModo(m);
    setDistSel(null);
    if (m === 'territorio') {
      setDepSel(null);
      setVista(pais());
    }
  };
  const elegirSector = (sid) => {
    setSectorId(sid);
    setModo('actividad');
    setDepSel(null);
  };
  const elegirDepartamento = (nombre) => {
    setModo('territorio');
    setDepSel(nombre);
    setDistSel(null);
    setVista({ ...vistaDepartamento(nombre), clave: Date.now() });
  };
  const elegirDistrito = (id) => {
    setDistSel(id);
    const d = D.find((x) => x.id === id);
    if (modo === 'territorio' && d && depSel !== d.departamento) {
      setDepSel(d.departamento);
      setVista({ ...vistaDepartamento(d.departamento), clave: Date.now() });
    }
  };
  const volverPais = () => {
    setDepSel(null);
    setDistSel(null);
    setVista(pais());
  };

  const derecha = distSel ? (
    <FichaDistrito key={`${distSel}-${sectorId}`} id={distSel} sectorId={modo === 'actividad' ? sectorId : null} onClose={() => setDistSel(null)} onSector={elegirSector} onDepartamento={elegirDepartamento} />
  ) : modo === 'territorio' && depSel ? (
    <FichaDepartamento key={depSel} nombre={depSel} onClose={volverPais} onDistrito={elegirDistrito} onSector={elegirSector} />
  ) : modo === 'actividad' && sectorId ? (
    <ResumenActividad sectorId={sectorId} onDistrito={elegirDistrito} />
  ) : (
    <div className="ficha ficha-vacia">
      <h2>Cómo leer esta herramienta</h2>
      <p>Compara cada distrito con los que <strong>ya producen</strong> una actividad industrial y muestra qué capacidades tiene y cuáles le faltan: capital humano, formación específica, energía, logística y recursos.</p>
      <p><strong>Por actividad:</strong> elegí una actividad a la izquierda y el mapa muestra dónde hay más o menos capacidades para producirla.</p>
      <p><strong>Por territorio:</strong> elegí un indicador, tocá un departamento y después un distrito para ver su ficha.</p>
      <p className="nota">Es una descripción de distancias frente a lo que ya existe, no una predicción ni una probabilidad de éxito. Resultados como asociación, no causalidad.</p>
    </div>
  );

  return (
    <div className="app">
      <header className="barra">
        <div className="marca">
          <span className="logo">TAPE</span>
          <span className="sub">Territorio, Actividades y Potencial Económico · Paraguay</span>
        </div>
        <nav className="modos">
          <button type="button" className={`modo ${modo === 'actividad' ? 'modo-activo' : ''}`} onClick={() => elegirModo('actividad')}><Factory size={14} /> Por actividad</button>
          <button type="button" className={`modo ${modo === 'territorio' ? 'modo-activo' : ''}`} onClick={() => elegirModo('territorio')}><MapIcon size={14} /> Por territorio</button>
        </nav>
        <div className="acciones">
          <button type="button" className="icono" onClick={() => setAviso(!aviso)} aria-label="Cómo se lee"><Info size={16} /></button>
          <button type="button" className="icono" onClick={() => setTema(tema === 'dark' ? 'light' : 'dark')} aria-label="Cambiar tema">{tema === 'dark' ? <Sun size={16} /> : <Moon size={16} />}</button>
        </div>
      </header>
      {aviso && (
        <div className="aviso">
          <button type="button" className="cerrar" onClick={() => setAviso(false)} aria-label="Cerrar"><X size={14} /></button>
          <strong>Qué es y qué no es.</strong> {diag.meta.aviso} El estándar de comparación es el percentil 10 de los distritos que hoy producen cada actividad en el mapa MIC 2026 (una foto, no una serie): con otro estándar cambian muchas celdas. El mapa MIC solo cubre industrias, así que no hay diagnóstico para el agro ni los servicios. Los distritos creados después de 2012 se dibujan como puntos. Versión {diag.meta.version} ({diag.meta.decisiones}).
        </div>
      )}
      <main className="cuerpo">
        <aside className="izq">
          {modo === 'actividad' ? (
            <ListaActividades sectorId={sectorId} onSelect={elegirSector} />
          ) : (
            <div className="lista">
              <div className="grupo-t">Indicador del mapa</div>
              <select className="selector" value={indicador} onChange={(e) => setIndicador(e.target.value)}>
                {INDICADORES.map((x) => <option key={x.id} value={x.id}>{x.nombre}</option>)}
              </select>
              <div className="migas">
                <button type="button" className="enlace" onClick={volverPais}>Paraguay</button>
                {depSel && <span> › {titulo(depSel)}</span>}
                {distSel && <span> › {titulo(D.find((x) => x.id === distSel)?.nombre)}</span>}
              </div>
              <div className="grupo-t">Departamentos</div>
              <div className="filas">
                {DEPS.map((dp) => {
                  const v = valorDepartamento(dp.nombre, indicador);
                  return (
                    <button type="button" key={dp.nombre} className={`fila fila-chica ${depSel === dp.nombre ? 'fila-activa' : ''}`} onClick={() => elegirDepartamento(dp.nombre)}>
                      <div className="fila-nombre">{titulo(dp.nombre)}</div>
                      <div className="fila-meta"><span className="mini">{v === null ? 'sin dato' : Math.round(v)}</span></div>
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        </aside>
        <section className="centro">
          <Mapa modo={modo} sectorId={modo === 'actividad' ? sectorId : null} indicador={indicador} depSel={depSel} distSel={distSel} onDistrito={elegirDistrito} onDepartamento={elegirDepartamento} tema={tema} vista={vista} />
          {modo === 'actividad' && sectorId && <div className="titulo-mapa">{SEC[sectorId].nombre}</div>}
        </section>
        <aside className="der">{derecha}</aside>
      </main>
    </div>
  );
}
