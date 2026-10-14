// Tabla de normalización GADM → ID
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

const ParaguayMap = ({ data, selectedId, onSelect, colorScale }) => {
  return (
    <ComposableMap
      projection="geoMercator"
      projectionConfig={{ center: [-58.5, -23.5], scale: 2400 }}
      style={{ width: '100%', height: '100%' }}
    >
      <ZoomableGroup>
        <Geographies geography="/data/gadm41_PRY_1.json">
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