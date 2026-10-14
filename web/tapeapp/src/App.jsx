import React, { useState, useEffect, useMemo } from 'react';
import {
  ComposableMap, Geographies, Geography, ZoomableGroup
} from 'react-simple-maps';
import {
  Sun, Moon, MapPin, X, TrendingUp, Layers,
  AlertTriangle, Target
} from 'lucide-react';

import geojsonData from './data/gadm41_PRY_1.json';
import departamentosData from './data/departamentos.json';

const styleTag = document.createElement('style');
styleTag.innerHTML = `
  :root, [data-theme="light"] {
    --color-bg-app: #f4f6f8;
    --color-surface: #ffffff;
    --color-surface-alt: #f1f3f6;
    --color-border: #e2e8f0;
    --color-text: #0f172a;
    --color-text-secondary: #475569;
    --color-text-muted: #94a3b8;
    --color-accent: #0f172a;
    --color-accent-text: #ffffff;
    --color-shadow: rgba(15, 23, 42, 0.08);
    --color-success: #059669;
    --color-warning: #d97706;
    --color-danger: #dc2626;
    --map-empty: #e2e8f0;
    --map-low: #fef3c7;
    --map-mid: #fbbf24;
    --map-high: #d97706;
    --map-top: #92400e;
  }
  [data-theme="dark"] {
    --color-bg-app: #0b0f19;
    --color-surface: #111827;
    --color-surface-alt: #1f2937;
    --color-border: #374151;
    --color-text: #f9fafb;
    --color-text-secondary: #9ca3af;
    --color-text-muted: #6b7280;
    --color-accent: #f9fafb;
    --color-accent-text: #111827;
    --color-shadow: rgba(0,0,0,0.4);
    --color-success: #10b981;
    --color-warning: #f59e0b;
    --color-danger: #ef4444;
    --map-empty: #1f2937;
    --map-low: #422006;
    --map-mid: #78350f;
    --map-high: #b45309;
    --map-top: #f59e0b;
  }
  html, body, #root {
    height: 100vh; width: 100vw; margin: 0; padding: 0; overflow: hidden;
    font-family: 'Inter', -apple-system, sans-serif;
    background: var(--color-bg-app); color: var(--color-text);
  }
  .rsm-geography { transition: fill 0.15s ease; cursor: pointer; }
  .rsm-geography:hover { filter: brightness(1.15); }
  ::-webkit-scrollbar { width: 6px; }
  ::-webkit-scrollbar-thumb { background: var(--color-text-muted); border-radius: 10px; }
  @keyframes slideIn {
    from { transform: translateX(100%); opacity: 0; }
    to   { transform: translateX(0);    opacity: 1; }
  }
`;
document.head.appendChild(styleTag);

(function initTheme() {
  const stored = localStorage.getItem('theme');
  const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  document.documentElement.setAttribute('data-theme', stored || (prefersDark ? 'dark' : 'light'));
})();

const GADM_TO_ID = {
  'PRY.1_1':  'alto_paraguay',
  'PRY.2_1':  'alto_parana',
  'PRY.3_1':  'amambay',
  'PRY.4_1':  'asuncion',
  'PRY.5_1':  'boqueron',
  'PRY.6_1':  'caaguazu',
  'PRY.7_1':  'caazapa',
  'PRY.8_1':  'canindeyu',
  'PRY.9_1':  'central',
  'PRY.10_1': 'concepcion',
  'PRY.11_1': 'cordillera',
  'PRY.12_1': 'guaira',
  'PRY.13_1': 'itapua',
  'PRY.14_1': 'misiones',
  'PRY.15_1': 'neembucu',
  'PRY.16_1': 'paraguari',
  'PRY.17_1': 'presidente_hayes',
  'PRY.18_1': 'san_pedro',
};

const useTheme = () => {
  const [theme, setTheme] = useState(
    () => document.documentElement.getAttribute('data-theme') || 'light'
  );
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);
  return [theme, () => setTheme(t => (t === 'dark' ? 'light' : 'dark'))];
};

const colorForECI = (eci, min, max) => {
  if (eci == null) return 'var(--map-empty)';
  const range = max - min || 1;
  const t = (eci - min) / range;
  if (t < 0.25) return 'var(--map-low)';
  if (t < 0.50) return 'var(--map-mid)';
  if (t < 0.75) return 'var(--map-high)';
  return 'var(--map-top)';
};

const CapabilityBar = ({ label, value }) => {
  const pct = Math.round(value * 100);
  const color =
    value > 0.7 ? 'var(--color-success)' :
    value > 0.4 ? 'var(--color-warning)' :
    'var(--color-danger)';
  return (
    <div style={{ marginBottom: '14px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
        <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--color-text-secondary)' }}>
          {label.replace(/_/g, ' ')}
        </span>
        <span style={{ fontSize: '13px', fontWeight: 800, color }}>{pct}%</span>
      </div>
      <div style={{ height: '6px', background: 'var(--color-surface-alt)', borderRadius: '100px', overflow: 'hidden' }}>
        <div style={{ height: '100%', width: `${pct}%`, background: color, borderRadius: '100px', transition: 'width 0.4s ease' }} />
      </div>
    </div>
  );
};

const ParaguayMap = ({ data, selectedId, onSelect, colorScale }) => {
  return (
    <ComposableMap
      projection="geoMercator"
      projectionConfig={{ center: [-58.5, -23.5], scale: 2400 }}
      style={{ width: '100%', height: '100%' }}
    >
      <ZoomableGroup>
        <Geographies geography={geojsonData}>
          {({ geographies }) =>
            geographies.map((geo) => {
              const gadmId = geo.properties.GID_1;
              const id = GADM_TO_ID[gadmId] || gadmId;
              const dep = data.find(d => d.id === id);
              const isSelected = selectedId === id;
              const fill = dep ? colorScale(dep.eci) : 'var(--map-empty)';
              return (
                <Geography
                  key={geo.rsmKey}
                  geography={geo}
                  fill={fill}
                  stroke={isSelected ? 'var(--color-accent)' : 'var(--color-border)'}
                  strokeWidth={isSelected ? 2 : 0.5}
                  onClick={() => onSelect(id)}
                  style={{
                    default: { outline: 'none' },
                    hover:   { outline: 'none' },
                    pressed: { outline: 'none' },
                  }}
                />
              );
            })
          }
        </Geographies>
      </ZoomableGroup>
    </ComposableMap>
  );
};

const DepartmentPanel = ({ dep, onClose }) => {
  const [tab, setTab] = useState('resumen');
  if (!dep) return null;

  const tabs = [
    { id: 'resumen',       label: 'Resumen',       icon: TrendingUp },
    { id: 'capacidades',   label: 'Capacidades',   icon: Layers },
    { id: 'brechas',       label: 'Brechas',       icon: AlertTriangle },
    { id: 'oportunidades', label: 'Oportunidades', icon: Target },
  ];

  return (
    <aside style={{
      width: '420px', maxWidth: '92vw',
      background: 'var(--color-surface)',
      borderLeft: '1px solid var(--color-border)',
      display: 'flex', flexDirection: 'column',
      boxShadow: '-10px 0 30px var(--color-shadow)',
      animation: 'slideIn 0.25s ease', zIndex: 200,
    }}>
      <div style={{ padding: '24px', borderBottom: '1px solid var(--color-border)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <h2 style={{ margin: 0, fontSize: '22px', fontWeight: 900 }}>{dep.name}</h2>
            <p style={{ margin: '4px 0 0', fontSize: '13px', color: 'var(--color-text-secondary)' }}>
              {dep.population?.toLocaleString()} habitantes
            </p>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-text-secondary)', padding: '4px' }}>
            <X size={20} />
          </button>
        </div>
        <div style={{ marginTop: '16px', display: 'flex', alignItems: 'baseline', gap: '10px' }}>
          <span style={{ fontSize: '32px', fontWeight: 900 }}>{dep.eci?.toFixed(2)}</span>
          <span style={{ fontSize: '13px', color: 'var(--color-text-secondary)', fontWeight: 600 }}>
            ECI · Complejidad Económica
          </span>
        </div>
      </div>

      <div style={{ display: 'flex', borderBottom: '1px solid var(--color-border)', overflowX: 'auto' }}>
        {tabs.map(t => {
          const Icon = t.icon;
          const active = tab === t.id;
          return (
            <button key={t.id} onClick={() => setTab(t.id)} style={{
              flex: 1, padding: '14px 10px', background: 'none', border: 'none',
              borderBottom: active ? '2px solid var(--color-accent)' : '2px solid transparent',
              cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center',
              gap: '6px', fontSize: '12px', fontWeight: 700,
              color: active ? 'var(--color-text)' : 'var(--color-text-muted)',
              whiteSpace: 'nowrap',
            }}>
              <Icon size={14} /> {t.label}
            </button>
          );
        })}
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: '24px' }}>
        {tab === 'resumen' && (
          <>
            <h3 style={styles.panelSectionTitle}>Sectores con ventaja</h3>
            {dep.top_sectors?.length ? dep.top_sectors.slice(0, 5).map((s, i) => (
              <div key={i} style={styles.sectorRow}>
                <span style={{ fontSize: '14px', fontWeight: 600 }}>{s.name}</span>
                <span style={{ fontSize: '13px', fontWeight: 800, color: 'var(--color-success)' }}>LQ {s.lq.toFixed(1)}</span>
              </div>
            )) : <p style={{ fontSize: '13px', color: 'var(--color-text-muted)' }}>Sin datos</p>}
          </>
        )}
        {tab === 'capacidades' && (
          <>
            <h3 style={styles.panelSectionTitle}>Capacidades locales</h3>
            {Object.keys(dep.capabilities || {}).length ? (
              Object.entries(dep.capabilities).map(([k, v]) => <CapabilityBar key={k} label={k} value={v} />)
            ) : <p style={{ fontSize: '13px', color: 'var(--color-text-muted)' }}>Sin datos</p>}
          </>
        )}
        {tab === 'brechas' && (
          <>
            <h3 style={styles.panelSectionTitle}>Brechas detectadas</h3>
            {dep.gaps?.length ? dep.gaps.map((g, i) => (
              <div key={i} style={{
                ...styles.gapRow,
                borderLeft: `3px solid ${
                  g.severity === 'alta' ? 'var(--color-danger)' :
                  g.severity === 'media' ? 'var(--color-warning)' :
                  'var(--color-success)'
                }`
              }}>
                <span style={{ fontSize: '11px', fontWeight: 800, textTransform: 'uppercase', color: 'var(--color-text-muted)' }}>{g.severity}</span>
                <p style={{ margin: '4px 0 0', fontSize: '14px' }}>{g.text}</p>
              </div>
            )) : <p style={{ fontSize: '13px', color: 'var(--color-text-muted)' }}>Sin datos</p>}
          </>
        )}
        {tab === 'oportunidades' && (
          <>
            <h3 style={styles.panelSectionTitle}>Productos factibles</h3>
            {dep.opportunities?.length ? dep.opportunities.map((o, i) => (
              <div key={i} style={styles.sectorRow}>
                <span style={{ fontSize: '14px', fontWeight: 600 }}>{o.product}</span>
                <span style={{ fontSize: '13px', fontWeight: 800, color: 'var(--color-text-secondary)' }}>
                  {(o.probability * 100).toFixed(0)}%
                </span>
              </div>
            )) : <p style={{ fontSize: '13px', color: 'var(--color-text-muted)' }}>Sin datos</p>}
          </>
        )}
      </div>
    </aside>
  );
};

const App = () => {
  const [theme, toggleTheme] = useTheme();
  const [selectedId, setSelectedId] = useState(null);
  const data = departamentosData;

  const { min, max } = useMemo(() => {
    const ecis = data.map(d => d.eci).filter(v => v != null);
    if (!ecis.length) return { min: 0, max: 1 };
    return { min: Math.min(...ecis), max: Math.max(...ecis) };
  }, [data]);

  const colorScale = (eci) => colorForECI(eci, min, max);
  const selectedDep = data.find(d => d.id === selectedId);

  return (
    <div style={{ display: 'flex', height: '100vh', width: '100vw', overflow: 'hidden', position: 'relative' }}>
      <main style={{
        flex: 1, paddingTop: '64px',
        position: 'relative', background: 'var(--color-bg-app)',
        display: 'flex', justifyContent: 'center', alignItems: 'center',
      }}>
        <ParaguayMap data={data} selectedId={selectedId} onSelect={setSelectedId} colorScale={colorScale} />

        <div style={{
          position: 'absolute', bottom: '24px', left: '24px',
          background: 'var(--color-surface)', padding: '16px',
          borderRadius: '12px', boxShadow: '0 4px 15px var(--color-shadow)',
          border: '1px solid var(--color-border)',
        }}>
          <p style={{ margin: '0 0 10px', fontSize: '11px', fontWeight: 800, textTransform: 'uppercase', color: 'var(--color-text-muted)' }}>
            Complejidad (ECI)
          </p>
          <div style={{ display: 'flex', gap: '4px' }}>
            {['--map-low', '--map-mid', '--map-high', '--map-top'].map(c => (
              <div key={c} style={{ width: '24px', height: '12px', background: `var(${c})`, borderRadius: '3px' }} />
            ))}
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '6px', fontSize: '10px', color: 'var(--color-text-muted)' }}>
            <span>Bajo</span><span>Alto</span>
          </div>
        </div>
      </main>

      {selectedDep && <DepartmentPanel dep={selectedDep} onClose={() => setSelectedId(null)} />}

      <div style={{
        position: 'fixed', top: 0, left: 0, right: 0,
        height: '64px', zIndex: 100,
        background: 'var(--color-surface)',
        borderBottom: '1px solid var(--color-border)',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '0 24px',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <MapPin size={22} />
          <h1 style={{ margin: 0, fontSize: '18px', fontWeight: 900 }}>TAPE · Paraguay</h1>
        </div>
        <button onClick={toggleTheme} style={{
          width: '40px', height: '40px', borderRadius: '50%',
          background: 'var(--color-surface-alt)', border: 'none',
          cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: 'var(--color-text)',
        }}>
          {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
        </button>
      </div>
    </div>
  );
};

const styles = {
  panelSectionTitle: {
    fontSize: '11px', fontWeight: 800, textTransform: 'uppercase',
    color: 'var(--color-text-muted)', margin: '0 0 14px',
  },
  sectorRow: {
    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
    padding: '12px 0', borderBottom: '1px solid var(--color-border)',
  },
  gapRow: {
    padding: '12px 14px', marginBottom: '10px',
    background: 'var(--color-surface-alt)', borderRadius: '8px',
  },
};

export default App;