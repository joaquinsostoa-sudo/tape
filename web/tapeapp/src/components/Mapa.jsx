import React, { useMemo, useRef, useState } from 'react';
import { ComposableMap, Geographies, Geography, Marker, ZoomableGroup } from 'react-simple-maps';
import {
  CLASES, COLOR_CLASE, D, DEPS, DESCRIPCION_CLASE, IDX, INDICADORES, SEC, celda, colorRampa, gadm, geoDist, rango, titulo, valorDepartamento, valorDistrito,
} from '../lib.js';

const GID_A_DEP = Object.fromEntries(DEPS.map((d) => [d.gid, d.nombre]));

// Mapa de Paraguay con dos modos: por actividad (distritos pintados por la clase de la celda sector × distrito) y por territorio (departamentos y, al elegir uno, sus distritos).
export default function Mapa({ modo, sectorId, indicador, depSel, distSel, onDistrito, onDepartamento, tema, vista }) {
  const cont = useRef(null);
  const [hover, setHover] = useState(null);
  const [zoom, setZoom] = useState(vista.zoom);
  const sector = sectorId ? SEC[sectorId] : null;
  const info = INDICADORES.find((x) => x.id === indicador);
  const colores = COLOR_CLASE[tema];

  const escala = useMemo(() => {
    if (info?.tipo !== 'cuenta') return [0, 100];
    return rango(D.map((_, i) => valorDistrito(i, indicador)));
  }, [indicador, info]);
  const norm = (v) => (v === null || v === undefined ? null : (v - escala[0]) / Math.max(escala[1] - escala[0], 1e-9));

  const nivelDep = modo === 'territorio' && !depSel;
  const colorDistrito = (id) => {
    const i = IDX[id];
    if (modo === 'actividad') {
      if (!sector) return colores[6];
      const c = celda(sector.id, i);
      return c ? colores[c.clase] : colores[6];
    }
    if (depSel && D[i].departamento !== depSel) return tema === 'dark' ? '#18242a' : '#f1f4f5';
    return colorRampa(norm(valorDistrito(i, indicador)), tema);
  };
  const bordeProduce = (id) => modo === 'actividad' && sector && celda(sector.id, IDX[id])?.yaProduce;

  const mover = (e) => {
    const r = cont.current.getBoundingClientRect();
    return { x: e.clientX - r.left, y: e.clientY - r.top };
  };
  const textoDistrito = (id) => {
    const i = IDX[id];
    const d = D[i];
    if (modo === 'actividad') {
      const c = sector ? celda(sector.id, i) : null;
      return [`${titulo(d.nombre)} (${titulo(d.departamento)})`, c ? `${CLASES[c.clase]}${c.yaProduce ? ' · ya la produce' : ''}` : 'Elegí una actividad'];
    }
    const v = valorDistrito(i, indicador);
    return [`${titulo(d.nombre)} (${titulo(d.departamento)})`, `${info.nombre}: ${v === null || v === undefined ? 'sin dato' : info.tipo === 'capa' ? `percentil ${Math.round(v)}` : v}`];
  };
  const stroke = tema === 'dark' ? '#0e171b' : '#ffffff';
  const sinPoligono = D.filter((d) => !d.poligono && d.lat !== null && (nivelDep ? false : !depSel || d.departamento === depSel));

  return (
    <div className="mapa" ref={cont}>
      <ComposableMap projection="geoMercator" projectionConfig={{ center: [-58.4, -23.4], scale: 4300 }} width={800} height={760} style={{ width: '100%', height: '100%' }}>
        <ZoomableGroup key={`${vista.center}-${vista.zoom}-${vista.clave}`} center={vista.center} zoom={vista.zoom} minZoom={1} maxZoom={16} onMoveEnd={({ zoom: z }) => setZoom(z)}>
          {nivelDep ? (
            <Geographies geography={gadm}>
              {({ geographies }) =>
                geographies.map((g) => {
                  const dep = GID_A_DEP[g.properties.GID_1];
                  const v = valorDepartamento(dep, indicador);
                  return (
                    <Geography
                      key={g.rsmKey}
                      geography={g}
                      fill={colorRampa(norm(v), tema)}
                      stroke={stroke}
                      strokeWidth={0.6}
                      style={{ default: { outline: 'none' }, hover: { outline: 'none', opacity: 0.85, cursor: 'pointer' }, pressed: { outline: 'none' } }}
                      onClick={() => onDepartamento(dep)}
                      onMouseMove={(e) => setHover({ ...mover(e), texto: [titulo(dep), `${info.nombre} (mediana de sus distritos): ${v === null ? 'sin dato' : info.tipo === 'capa' ? `percentil ${Math.round(v)}` : v}`] })}
                      onMouseLeave={() => setHover(null)}
                    />
                  );
                })
              }
            </Geographies>
          ) : (
            <Geographies geography={geoDist}>
              {({ geographies }) =>
                geographies.map((g) => {
                  const id = g.properties.id;
                  const activo = id === distSel;
                  const produce = bordeProduce(id);
                  return (
                    <Geography
                      key={g.rsmKey}
                      geography={g}
                      fill={colorDistrito(id)}
                      stroke={activo ? (tema === 'dark' ? '#ffffff' : '#0f172a') : produce ? '#c2410c' : stroke}
                      strokeWidth={activo ? 1.6 / Math.sqrt(zoom) : produce ? 1.1 / Math.sqrt(zoom) : 0.3}
                      style={{ default: { outline: 'none' }, hover: { outline: 'none', opacity: 0.8, cursor: 'pointer' }, pressed: { outline: 'none' } }}
                      onClick={() => onDistrito(id)}
                      onMouseMove={(e) => setHover({ ...mover(e), texto: textoDistrito(id) })}
                      onMouseLeave={() => setHover(null)}
                    />
                  );
                })
              }
            </Geographies>
          )}
          {!nivelDep && (
            <Geographies geography={gadm}>
              {({ geographies }) =>
                geographies.map((g) => (
                  <Geography key={g.rsmKey} geography={g} fill="none" stroke={tema === 'dark' ? '#93a5ae' : '#334155'} strokeWidth={0.7 / Math.sqrt(zoom)} style={{ default: { outline: 'none', pointerEvents: 'none' }, hover: { pointerEvents: 'none' }, pressed: { pointerEvents: 'none' } }} />
                ))
              }
            </Geographies>
          )}
          {sinPoligono.map((d) => {
            const activo = d.id === distSel;
            const produce = bordeProduce(d.id);
            return (
              <Marker key={d.id} coordinates={[d.lon, d.lat]}>
                <circle
                  r={5 / Math.sqrt(zoom)}
                  fill={colorDistrito(d.id)}
                  stroke={activo ? (tema === 'dark' ? '#ffffff' : '#0f172a') : produce ? '#c2410c' : tema === 'dark' ? '#e5edf1' : '#0f172a'}
                  strokeWidth={(activo ? 2 : produce ? 1.6 : 0.8) / Math.sqrt(zoom)}
                  style={{ cursor: 'pointer' }}
                  onClick={() => onDistrito(d.id)}
                  onMouseMove={(e) => setHover({ ...mover(e), texto: [...textoDistrito(d.id), 'Distrito creado después de 2012: se dibuja como punto'] })}
                  onMouseLeave={() => setHover(null)}
                />
              </Marker>
            );
          })}
        </ZoomableGroup>
      </ComposableMap>
      {hover && (
        <div className="tooltip" style={{ left: Math.min(hover.x + 14, (cont.current?.clientWidth || 800) - 250), top: hover.y + 14 }}>
          {hover.texto.map((t, k) => (
            <div key={k} className={k === 0 ? 'tt-titulo' : 'tt-linea'}>{t}</div>
          ))}
        </div>
      )}
      <Leyenda modo={modo} sector={sector} info={info} escala={escala} tema={tema} nivelDep={nivelDep} />
    </div>
  );
}

function Leyenda({ modo, sector, info, escala, tema, nivelDep }) {
  const colores = COLOR_CLASE[tema];
  if (modo === 'actividad') {
    const conteo = [0, 0, 0, 0, 0, 0, 0];
    let produce = 0;
    if (sector) {
      D.forEach((_, i) => {
        const c = celda(sector.id, i);
        if (c) {
          conteo[c.clase] += 1;
          if (c.yaProduce) produce += 1;
        }
      });
    }
    return (
      <div className="leyenda">
        <div className="leyenda-t">{sector ? sector.nombre : 'Elegí una actividad'}</div>
        {sector &&
          colores.map((col, k) =>
            conteo[k] > 0 || k <= 3 ? (
              <div className="leyenda-fila" key={k} title={DESCRIPCION_CLASE[k]}>
                <span className="muestra" style={{ background: col }} />
                <span>{CLASES[k]}</span>
                <span className="leyenda-n">{conteo[k]}</span>
              </div>
            ) : null,
          )}
        {sector && (
          <div className="leyenda-fila">
            <span className="muestra borde-produce" />
            <span>Ya la produce (mapa MIC 2026)</span>
            <span className="leyenda-n">{produce}</span>
          </div>
        )}
        <div className="leyenda-nota">Punto = distrito creado después de 2012</div>
      </div>
    );
  }
  const fmt = (v) => (info.tipo === 'capa' ? Math.round(v) : Math.round(v));
  return (
    <div className="leyenda">
      <div className="leyenda-t">{info.nombre}</div>
      <div className="rampa" style={{ background: `linear-gradient(to right, ${colorRampa(0, tema)}, ${colorRampa(1, tema)})` }} />
      <div className="rampa-etq">
        <span>{info.tipo === 'capa' ? 'menos (percentil 0)' : fmt(escala[0])}</span>
        <span>{info.tipo === 'capa' ? 'más (percentil 100)' : fmt(escala[1])}</span>
      </div>
      <div className="leyenda-nota">{nivelDep ? 'Departamento = mediana de sus distritos. Tocá uno para ver sus distritos.' : 'Punto = distrito creado después de 2012'}</div>
    </div>
  );
}
