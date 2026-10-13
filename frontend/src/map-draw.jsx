import React, { useEffect, useRef } from 'react';
import { useMap, Polygon, Polyline, Marker } from 'react-leaflet';
import L from 'leaflet';
import './map-draw.css';
import { tidyStroke } from './stroke-shape';

export function readBoundary(value) {
  try { const p = JSON.parse(value); return Array.isArray(p) && p.length >= 3 && p.length <= 64 && p.every(v => Array.isArray(v) && v.length === 2 && v.every(Number.isFinite)) ? p : []; } catch { return []; }
}
const cross = (a,b,c) => (b[1]-a[1])*(c[0]-a[0])-(b[0]-a[0])*(c[1]-a[1]);
const onLine = (a,b,c) => Math.abs(cross(a,b,c)) <= 1e-10 && [0,1].every(k => c[k] >= Math.min(a[k],b[k])-1e-10 && c[k] <= Math.max(a[k],b[k])+1e-10);
export function boundaryError(points) {
  if (points.length < 3) return 'Add at least 3 corners, or drag around an area.';
  if (points.length > 64) return 'Use up to 64 corners.';
  if (new Set(points.map(p => p.join(','))).size !== points.length) return 'Corners must be different.';
  if (Math.abs(points.reduce((s,a,i) => { const b=points[(i+1)%points.length]; return s+a[1]*b[0]-b[1]*a[0]; },0)) <= 1e-10) return 'Draw a larger area with at least 3 different corners.';
  for (let i=0;i<points.length;i++) for(let j=i+2;j<points.length;j++) {
    if(i===0 && j===points.length-1) continue;
    const a=points[i], b=points[(i+1)%points.length], c=points[j], d=points[(j+1)%points.length];
    if ((cross(a,b,c)*cross(a,b,d)<0 && cross(c,d,a)*cross(c,d,b)<0) || onLine(a,b,c) || onLine(a,b,d) || onLine(c,d,a) || onLine(c,d,b)) return 'The line crosses itself. Move a white corner to fix it, or select Redraw.';
  }
  return '';
}
export default function DrawLayer({ active, points, setPoints, finished, setFinished, polygon, mode, onNotice }) {
  const map = useMap();
  const latest = useRef({points, finished}); latest.current = {points, finished};
  const applied = readBoundary(polygon);
  useEffect(() => {
    if (applied.length && !active) map.fitBounds(applied, {padding:[45,75],animate:false});
  }, [polygon]);
  useEffect(() => {
    if (!active) return;
    map.closePopup();
    // Capture a pen stroke only while drawing. Preview/edit and Move map retain navigation.
    const pen = mode === 'pen' && !finished;
    const handlers = pen ? ['dragging','doubleClickZoom','scrollWheelZoom','touchZoom','boxZoom','keyboard'] : [];
    const enabled = handlers.filter(k => map[k]?.enabled()); enabled.forEach(k => map[k].disable());
    const container = map.getContainer();
    let gesture = null, frame = null;
    const coordinate = e => { const p = map.mouseEventToLatLng(e); return [Number(p.lat.toFixed(6)), Number(p.lng.toFixed(6))]; };
    const publish = () => {
      if (frame != null) return;
      frame = requestAnimationFrame(() => { frame = null; if (gesture) setPoints(gesture.samples.slice()); });
    };
    const down = e => {
      if (!pen || gesture || e.isPrimary === false || e.button !== 0 || e.target.closest('.leaflet-control, .draw-vertex')) return;
      e.preventDefault(); e.stopPropagation(); container.setPointerCapture(e.pointerId);
      onNotice('');
      gesture = {id:e.pointerId, original:latest.current.points, samples:[coordinate(e)], pixels:[L.point(e.clientX,e.clientY)]};
    };
    const move = e => {
      if (!gesture || gesture.id !== e.pointerId) return;
      e.preventDefault(); e.stopPropagation();
      const samples = e.getCoalescedEvents?.();
      for (const sample of samples?.length ? samples : [e]) {
        const pixel = L.point(sample.clientX,sample.clientY);
        if (pixel.distanceTo(gesture.pixels.at(-1)) < 2 || gesture.samples.length >= 8192) continue;
        gesture.samples.push(coordinate(sample)); gesture.pixels.push(pixel);
      }
      publish();
    };
    const up = e => {
      if (!gesture || gesture.id !== e.pointerId) return;
      e.preventDefault(); e.stopPropagation();
      if (frame != null) { cancelAnimationFrame(frame); frame = null; }
      const stroke = gesture; gesture = null;
      if (container.hasPointerCapture(e.pointerId)) container.releasePointerCapture(e.pointerId);
      if (stroke.samples.length < 3) { setPoints(stroke.original); onNotice('Press and hold, draw around an area, then release.'); return; }
      let tolerance = 2.5, simple = L.LineUtil.simplify(stroke.pixels,tolerance);
      while (simple.length > 64 && tolerance < 40) { tolerance *= 1.5; simple = L.LineUtil.simplify(stroke.pixels,tolerance); }
      if (simple.length > 64) simple = Array.from({length:64},(_,i)=>simple[Math.floor(i*simple.length/64)]);
      // Repair a small overlap at closure, retaining the dominant traced region.
      // Intersections introduce a new point, so project cleaned pixels to the map.
      const cleaned = tidyStroke(simple.map(pixel => [pixel.x,pixel.y]));
      const selected = cleaned.map(([clientX,clientY]) => coordinate({clientX,clientY}));
      setPoints(selected); setFinished(true);
    };
    const cancel = () => {
      if (gesture) setPoints(gesture.original);
      gesture = null;
      if (frame != null) { cancelAnimationFrame(frame); frame = null; }
    };
    // A keyboard alternative uses the map centre without altering the pen workflow.
    const keyboard = e => {
      if (!pen || gesture) return;
      const shift = {ArrowLeft:[-35,0],ArrowRight:[35,0],ArrowUp:[0,-35],ArrowDown:[0,35]}[e.key];
      if (shift) { e.preventDefault(); map.panBy(shift,{animate:false}); }
      if (e.key === 'Enter') {
        e.preventDefault();
        if (e.shiftKey && latest.current.points.length >= 3) {setFinished(true); return;}
        if (latest.current.points.length < 64) {const c=map.getCenter(); setPoints([...latest.current.points,[Number(c.lat.toFixed(6)),Number(c.lng.toFixed(6))]]);}
      }
      if (e.key === 'Backspace') { e.preventDefault(); setPoints(latest.current.points.slice(0,-1)); }
    };
    container.addEventListener('pointerdown',down,true); container.addEventListener('pointermove',move,true);
    container.addEventListener('pointerup',up,true); container.addEventListener('pointercancel',cancel,true); container.addEventListener('keydown',keyboard);
    return () => {
      if(frame != null) cancelAnimationFrame(frame);
      container.removeEventListener('pointerdown',down,true); container.removeEventListener('pointermove',move,true);
      container.removeEventListener('pointerup',up,true); container.removeEventListener('pointercancel',cancel,true); container.removeEventListener('keydown',keyboard);
      enabled.forEach(k => map[k].enable());
    };
  }, [active, mode, finished, map, setPoints, setFinished, onNotice]);
  const visible = active ? points : applied;
  const invalid = active && finished && !!boundaryError(points);
  return <>
    {visible.length >= 3 && (finished || !active) ? <Polygon positions={visible} interactive={false} pathOptions={{color:invalid ? '#b42318' : '#0045df',weight:3,fillOpacity:.13,lineCap:'round',lineJoin:'round'}} /> : visible.length >= 2 ? <Polyline positions={visible} interactive={false} smoothFactor={1.5} pathOptions={{color:'#0045df',weight:3,lineCap:'round',lineJoin:'round'}} /> : null}
    {active && finished && visible.map((point,index) => <Marker key={index} position={point} draggable title={'Move boundary corner '+(index+1)} alt={'Boundary corner '+(index+1)} icon={L.divIcon({className:'draw-vertex',html:'<span></span>',iconSize:[32,32],iconAnchor:[16,16]})} eventHandlers={{dragend:event => {const p=event.target.getLatLng();setPoints(current=>current.map((v,i)=>i===index ? [Number(p.lat.toFixed(6)),Number(p.lng.toFixed(6))] : v));onNotice('');}}} />)}
  </>;
}
