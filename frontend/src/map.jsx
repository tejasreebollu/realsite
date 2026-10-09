import React, { useEffect, useRef, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, ZoomControl, useMap, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import { ChevronDown, ChevronUp, ExternalLink, RotateCcw, Pencil, Hand, X } from 'lucide-react';
import { compactMoney, money, areaText } from './api';
import 'leaflet/dist/leaflet.css';
import './map-options.css';
import DrawLayer, { boundaryError, readBoundary } from './map-draw';

const centers = { hyderabad: [17.4401, 78.3910], bengaluru: [12.9716, 77.5946], bangalore: [12.9716, 77.5946], mumbai: [19.0760, 72.8777], pune: [18.5204, 73.8567], 'new delhi': [28.6139, 77.2090] };

const basemaps = {
  automatic: {
    url: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  },
  satellite: {
    url: 'https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attribution: 'Tiles &copy; <a href="https://www.arcgis.com/home/item.html?id=10df2279f9684e4a9f6a7f08febac2a9">Esri</a> &mdash; Sources: Esri, Maxar, Earthstar Geographics, and the GIS User Community',
  },
};
const climateRisks = ['None selected', 'Wind', 'Flood', 'Air', 'Fire', 'Heat'];

function MapController({ items, city, onBounds, onCenter, searchOnMove, resetKey, small, drawing, polygon }) {
  const map = useMap();
  const coordsKey = items.map(p => p.id).join(',');
  useEffect(() => {
    // Fit when the search changes; do not refit in response to a viewport query.
    if (drawing || polygon) return;
    if (centers[city?.toLowerCase()]) map.setView(centers[city.toLowerCase()], small ? 14 : 12);
    else if (items.length) map.fitBounds(items.map(p => [p.lat, p.lng]), { padding: [50, 50], maxZoom: small ? 14 : 13 });
    else map.setView([21.1, 78.5], 5);
  }, [city, resetKey]);
  useEffect(() => {
    if (drawing || polygon) return;
    if (items.length && !centers[city?.toLowerCase()] && !searchOnMove) map.fitBounds(items.map(p => [p.lat, p.lng]), { padding: [50, 50], maxZoom: small ? 14 : 13 });
    if (small && items.length === 1) map.setView([items[0].lat, items[0].lng], 14);
  }, [coordsKey]);
  useEffect(() => {
    const observer = new ResizeObserver(() => map.invalidateSize());
    observer.observe(map.getContainer());
    return () => observer.disconnect();
  }, [map]);
  useEffect(() => { onCenter(map.getCenter()); }, [map, onCenter]);
  useMapEvents({ moveend: () => {
    onCenter(map.getCenter());
    if (drawing || polygon || !searchOnMove || !onBounds) return;
    const bounds = map.getBounds();
    onBounds({ north: bounds.getNorth(), south: bounds.getSouth(), east: bounds.getEast(), west: bounds.getWest() });
  } });
  return null;
}

export default function PropertyMap({ items, city, hovered, rental, total, onBounds, hasBounds, small = false, polygon = '', onPolygon }) {
  const [drawing, setDrawing] = useState(false);
  const [drawMode, setDrawMode] = useState('pen');
  const [drawNotice, setDrawNotice] = useState('');
  const [points, setPoints] = useState([]);
  const [finished, setFinished] = useState(false);
  const drawError = drawNotice || (finished ? boundaryError(points) : '');
  const [searchOnMove, setSearchOnMove] = useState(false);
  const cancelDrawing = () => { setDrawing(false); setPoints([]); setFinished(false); setDrawNotice(''); };
  useEffect(() => { cancelDrawing(); }, [city, polygon]);
  useEffect(() => {
    if(!drawing) return;
    const cancel=e=>{if(e.key==='Escape') cancelDrawing();};
    document.addEventListener('keydown',cancel);
    return()=>document.removeEventListener('keydown',cancel);
  },[drawing]);
  const [resetKey, setResetKey] = useState(0);
  const [tileError, setTileError] = useState(false);
  const [view, setView] = useState('automatic');
  const [risk, setRisk] = useState('None selected');
  const [optionsOpen, setOptionsOpen] = useState(false);
  const [center, setCenter] = useState(() => {
    const point = centers[city?.toLowerCase()] || [17.4401, 78.3910];
    return { lat: point[0], lng: point[1] };
  });
  const optionsRef = useRef();
  const buttonRef = useRef();
  const layer = view === 'satellite' ? basemaps.satellite : basemaps.automatic;
  const streetViewUrl = 'https://www.google.com/maps/@?' + new URLSearchParams({ api: '1', map_action: 'pano', viewpoint: `${center.lat.toFixed(6)},${center.lng.toFixed(6)}` });

  useEffect(() => { setTileError(false); }, [view]);
  useEffect(() => {
    if (!optionsOpen) return;
    optionsRef.current?.querySelector('input[name="map-view"]:checked')?.focus({ preventScroll: true });
    const outside = event => { if (!optionsRef.current?.contains(event.target)) setOptionsOpen(false); };
    const escape = event => { if (event.key === 'Escape') { setOptionsOpen(false); buttonRef.current?.focus(); } };
    document.addEventListener('pointerdown', outside);
    document.addEventListener('keydown', escape);
    return () => { document.removeEventListener('pointerdown', outside); document.removeEventListener('keydown', escape); };
  }, [optionsOpen]);

  return <div className={'property-map ' + (small ? 'small-map' : '') + (drawing ? ' drawing draw-' + drawMode + (finished ? ' draw-ready' : '') : '') + (polygon ? ' has-polygon' : '')}>
    <MapContainer center={centers[city?.toLowerCase()] || [17.4401, 78.3910]} zoom={12} zoomControl={false} scrollWheelZoom={!small}>
      <TileLayer key={view === 'satellite' ? 'satellite' : 'automatic'} url={layer.url} maxZoom={19} attribution={layer.attribution} eventHandlers={{ tileerror: () => setTileError(true), tileload: () => setTileError(false) }} />
      <MapController items={items} city={city} onBounds={onBounds} onCenter={setCenter} searchOnMove={searchOnMove} resetKey={resetKey} small={small} drawing={drawing} polygon={polygon} />
      {!small && <DrawLayer active={drawing} points={points} setPoints={setPoints} finished={finished} setFinished={setFinished} polygon={polygon} mode={drawMode} onNotice={setDrawNotice} />}
      {items.map(item => <Marker key={item.id} position={[item.lat, item.lng]} zIndexOffset={hovered === item.id ? 1000 : 0} icon={L.divIcon({ className: 'price-marker ' + (rental ? 'rental-marker ' : '') + (hovered === item.id ? 'hovered' : ''), html: `<span>${compactMoney(item.price)}</span>`, iconSize: [72, 28], iconAnchor: [36, 28] })}>
        <Popup><a className="map-popup" href={(() => { const url = new URL(location.href); url.searchParams.set('property', item.id); return url.pathname + url.search; })()}><img src={item.images[0]} alt={item.title} /><strong>{money(item.price)}{item.purpose === 'rent' ? '/mo' : ''}</strong><span>{item.kind === 'Open Plot' || ['Commercial Building', 'Office', 'Shop'].includes(item.kind) ? areaText(item) + ' · ' + item.kind : item.beds + ' beds · ' + item.baths + ' baths · ' + areaText(item)}</span><span>{item.title}</span><b>View property →</b></a></Popup>
      </Marker>)}
      <ZoomControl position="bottomright" />
    </MapContainer>
    {!small && drawing && <>
      <section className="map-draw-toolbar" aria-label="Draw search area">
        <div className="draw-tools"><button className={'outline ' + (drawMode === 'pen' ? 'draw-selected' : '')} aria-label="Pen" title="Draw with a pen" aria-pressed={drawMode === 'pen'} onClick={() => setDrawMode('pen')}><Pencil size={17} /><span>Pen</span></button><button className={'outline ' + (drawMode === 'move' ? 'draw-selected' : '')} aria-label="Move map" title="Move or zoom the map" aria-pressed={drawMode === 'move'} onClick={() => setDrawMode('move')}><Hand size={17} /><span>Move map</span></button></div>
        <div className="draw-actions"><button className="outline" aria-label="Redraw area" title="Start again" disabled={!points.length} onClick={() => {setPoints([]);setFinished(false);setDrawNotice('');setDrawMode('pen');}}><RotateCcw size={16} /><span>Redraw</span></button><button className="primary" disabled={!finished || !!boundaryError(points)} onClick={() => {setSearchOnMove(false);onPolygon(JSON.stringify(points));cancelDrawing();}}>Apply</button><button className="outline draw-cancel" aria-label="Cancel" title="Cancel drawing" onClick={cancelDrawing}><X size={18} /></button></div>
      </section>
      <div className={'map-draw-hint ' + (drawError ? 'draw-error' : '')} role={drawError ? 'alert' : 'status'}>{drawError || (finished ? 'Area ready. Drag a corner to adjust, then Apply.' : drawMode === 'move' ? 'Move or zoom to your area, then select Pen.' : 'Press, draw around your area, then release.')}</div>
    </>}
    {!small && !drawing && <><div className="map-count">{items.length < total ? `${items.length} of ` : ''}{total} homes</div><div className="map-top-actions">{(hasBounds || polygon) && <button className="outline" onClick={() => { setSearchOnMove(false); onBounds(null); if(polygon) onPolygon(''); }}>Remove Boundary <X size={17} /></button>}<button className="outline" onClick={() => {setPoints([]);setFinished(false);setDrawNotice('');setDrawMode('pen');setOptionsOpen(false);setDrawing(true);}}>Draw</button>{polygon && <button className="outline" aria-label="Edit boundary" onClick={() => {setPoints(readBoundary(polygon));setFinished(true);setDrawNotice('');setDrawMode('move');setOptionsOpen(false);setDrawing(true);}}>Edit area</button>}{!polygon && <button className="primary" onClick={() => { setSearchOnMove(false); onBounds(null); if(polygon) onPolygon(''); setResetKey(k => k + 1); }}><RotateCcw size={15} />Re-centre</button>}</div><label className="search-map-checkbox"><input type="checkbox" disabled={!!polygon} checked={searchOnMove && !polygon} onChange={e => setSearchOnMove(e.target.checked)} />{polygon ? 'Search limited to your drawn area' : 'Search as I move the map'}</label></>}
    {!small && !drawing && <div className="map-options-control" ref={optionsRef}>
      {optionsOpen && <section className="map-options-panel" aria-label="Map options" id="map-options-panel">
        <div className="map-options-heading">Map Options</div>
        <div className="map-options-body">
          <fieldset className="map-view-options"><legend className="sr-only">Map view</legend>{[['automatic', 'Automatic'], ['satellite', 'Satellite'], ['street', 'Street view']].map(([value, text]) => <label className="map-radio" key={value}><input type="radio" name="map-view" value={value} checked={view === value} onChange={() => setView(value)} /><span>{text}</span></label>)}</fieldset>
          <fieldset className="climate-options"><legend>Climate Risk</legend><div className="climate-options-grid">{climateRisks.map(value => <label className="map-radio" key={value}><input type="radio" name="climate-risk" value={value} checked={risk === value} onChange={() => setRisk(value)} /><span>{value}</span></label>)}</div></fieldset>
          {view === 'street' && <div className="map-option-note"><p>Explore Street View at the centre of this map. Imagery availability varies by location.</p><a href={streetViewUrl} target="_blank" rel="noopener noreferrer">Open in Google Maps <ExternalLink size={13} /></a></div>}
          {risk !== 'None selected' && <p className="climate-unavailable" role="status">{risk} risk data is unavailable for this area. No climate overlay is displayed.</p>}
        </div>
      </section>}
      <button ref={buttonRef} className={'map-options-button ' + (optionsOpen ? 'open' : '')} aria-label="Map options" aria-expanded={optionsOpen} aria-controls="map-options-panel" onClick={() => setOptionsOpen(open => !open)}>Map {optionsOpen ? <ChevronUp size={19} /> : <ChevronDown size={19} />}</button>
    </div>}
    {!small && !drawing && view === 'street' && !optionsOpen && <div className="street-view-access"><a href={streetViewUrl} target="_blank" rel="noopener noreferrer">Open Street View <ExternalLink size={14} /></a><small>Opens Google Maps · Imagery may not be available.</small></div>}
    {!small && !drawing && risk !== 'None selected' && !optionsOpen && <div className="climate-map-status" role="status">{risk} risk data unavailable · No overlay displayed</div>}
    {tileError && <div className="map-offline">{view === 'satellite' ? 'Satellite imagery is unavailable.' : 'Map tiles are unavailable.'} Listings and property locations remain available.{view === 'satellite' && <button onClick={() => setView('automatic')}>Use automatic map</button>}</div>}
  </div>;
}
