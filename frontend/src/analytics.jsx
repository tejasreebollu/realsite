import React, { useEffect, useRef, useState } from 'react';
import { ArrowUpRight, Building2, CalendarDays, Download, IndianRupee, LoaderCircle, MapPin, MessageSquare, RefreshCw, Users, ChevronRight, Sparkles } from 'lucide-react';
import { api, compactMoney } from './api';
import './analytics.css';

const COLORS = ['#1767ed', '#20b8ac', '#8a67e8', '#efa94a', '#7587a3', '#e77595'];
const number = value => Number(value).toLocaleString('en-IN');
const price = value => value == null ? '—' : compactMoney(value);
const date = value => new Date(value + 'T12:00:00').toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
const datasets = { all: 'All listings', owner: 'Owner listings', synthetic: 'Synthetic listings' };

function Panel({ title, subtitle, children, className = '', action }) {
  return <article className={'analytics-panel ' + className}><header><div><h3>{title}</h3><p>{subtitle}</p></div>{action}</header>{children}</article>;
}
function Donut({ items, label }) {
  const [focus, setFocus] = useState(null);
  const total = items.reduce((sum, i) => sum + i.count, 0);
  let offset = 0;
  return <div className="analytics-donut"><div className="donut-picture"><svg viewBox="0 0 180 180" role="img" aria-label={`${label}: ${items.map(i => `${i.label} ${i.count}`).join(', ')}`}><circle cx="90" cy="90" r="64" fill="none" stroke="#eef2f8" strokeWidth="22" />{items.map((item, index) => {
    const fraction = total ? item.count / total : 0; const start = offset; offset += fraction;
    return <circle key={item.label} cx="90" cy="90" r="64" fill="none" stroke={COLORS[index % COLORS.length]} strokeWidth={focus === index ? 27 : 22} pathLength="100" strokeDasharray={`${fraction * 100} ${100 - fraction * 100}`} strokeDashoffset={-start * 100} transform="rotate(-90 90 90)" onMouseEnter={() => setFocus(index)} onMouseLeave={() => setFocus(null)}><title>{item.label}: {number(item.count)}</title></circle>;
  })}</svg><div className="donut-center"><strong>{number(focus == null ? total : items[focus].count)}</strong><span>{focus == null ? label : items[focus].label}</span></div></div><div className="donut-legend">{items.map((item, i) => <button key={item.label} onMouseEnter={() => setFocus(i)} onMouseLeave={() => setFocus(null)} onFocus={() => setFocus(i)} onBlur={() => setFocus(null)}><i style={{ background: COLORS[i % COLORS.length] }} /><span>{item.label}</span><b>{number(item.count)}</b><small>{total ? Math.round(item.count / total * 100) : 0}%</small></button>)}</div></div>;
}
function Bars({ items, color = COLORS[0], suffix = '' }) {
  const max = Math.max(1, ...items.map(i => i.count));
  return <div className="analytics-bars">{items.length ? items.map((item, index) => <div className="analytics-bar" key={item.label} title={`${item.label}: ${item.count}${suffix}`}><span>{item.label}</span><div className="bar-track"><i style={{ width: `${item.count / max * 100}%`, background: color === 'multi' ? COLORS[index % COLORS.length] : color }} /></div><b>{number(item.count)}</b></div>) : <p className="analytics-empty">No listings in this selection.</p>}</div>;
}
function ActivityChart({ items, registration = false, wide = false }) {
  const [focus, setFocus] = useState(null);
  const svgRef = useRef(null);
  const [width, setWidth] = useState(680);
  useEffect(() => {
    if (!wide) return;
    const observer = new ResizeObserver(([entry]) => setWidth(Math.max(200, Math.round(entry.contentRect.width))));
    observer.observe(svgRef.current);
    return () => observer.disconnect();
  }, [wide]);
  const chartWidth = wide ? width : 680;
  const chartHeight = wide ? 180 : 200;
  const plotWidth = chartWidth - 76;
  const plotBottom = chartHeight - 32;
  const plotHeight = plotBottom - 30;
  const keys = registration ? ['registrations'] : ['listings', 'inquiries'];
  const max = Math.max(1, ...items.flatMap(item => keys.map(k => item[k])));
  const band = plotWidth / Math.max(1, items.length);
  const barWidth = Math.min(wide ? 24 : 18, band * .42);
  const barGap = Math.min(2, band * .1);
  const x = i => registration ? 48 + i / Math.max(1, items.length - 1) * plotWidth : 48 + (i + .5) * band;
  const y = v => plotBottom - v / max * plotHeight;
  const selected = focus == null ? null : items[focus];
  return <><div className="chart-key">{keys.map((key, i) => <span key={key}><i style={{ background: COLORS[i] }} />{key === 'listings' ? 'New listings' : key === 'inquiries' ? 'Enquiries' : 'Registrations'}</span>)}</div><svg ref={svgRef} className="activity-chart" viewBox={`0 0 ${chartWidth} ${chartHeight}`} role="img" aria-label={registration ? 'Account registrations over the selected period' : 'Grouped bar chart of new listings and enquiries over the selected period'}>
    {[0, 0.5, 1].map(f => <g key={f}><line x1="48" x2={chartWidth - 28} y1={y(max * f)} y2={y(max * f)} stroke="#e9eef6" strokeDasharray="4 5" /><text x="35" y={y(max * f) + 4} textAnchor="end">{number(Math.round(max * f))}</text></g>)}
    {registration ? keys.map((key, ki) => <g key={key}><path d={`M48,${plotBottom} ${items.map((item, i) => `L${x(i)},${y(item[key])}`).join(' ')} L${chartWidth - 28},${plotBottom} Z`} fill={COLORS[ki]} opacity=".055" /><polyline points={items.map((item, i) => `${x(i)},${y(item[key])}`).join(' ')} fill="none" stroke={COLORS[ki]} strokeWidth="2.8" strokeLinejoin="round" /></g>) : items.map((item, i) => <g key={item.date} className="activity-bar-group">{keys.map((key, ki) => <rect key={key} className="activity-data-bar" data-series={key} x={x(i) + (ki === 0 ? -barWidth - barGap / 2 : barGap / 2)} y={y(item[key])} width={barWidth} height={plotBottom - y(item[key])} rx="1" fill={COLORS[ki]} opacity={focus == null || focus === i ? 1 : .6}><title>{date(item.date)}: {number(item[key])} {key}</title></rect>)}</g>)}
    {[0, Math.floor((items.length - 1) / 2), items.length - 1].map((i, index) => <text key={index} x={x(i)} y={chartHeight - 7} textAnchor={index === 0 ? 'start' : index === 2 ? 'end' : 'middle'}>{date(items[i].date)}</text>)}
    {focus != null && <g><line x1={x(focus)} x2={x(focus)} y1="20" y2={plotBottom + 1} stroke="#97a7bd" strokeDasharray="4 4" />{registration && keys.map((key, i) => <circle key={key} cx={x(focus)} cy={y(items[focus][key])} r="5" fill={COLORS[i]} stroke="white" strokeWidth="2" />)}</g>}
    {items.map((item, i) => <rect key={item.date} x={registration ? x(i) - band / 2 : 48 + i * band} y="20" width={registration ? band + 2 : band} height={plotBottom - 17} fill="transparent" tabIndex="0" role="button" aria-label={`${date(item.date)} to ${date(item.end)}: ${keys.map(k => `${item[k]} ${k}`).join(', ')}`} onMouseEnter={() => setFocus(i)} onMouseLeave={() => setFocus(null)} onFocus={() => setFocus(i)} onBlur={() => setFocus(null)}><title>{keys.map(k => `${k}: ${item[k]}`).join(' · ')}</title></rect>)}
  </svg><div className="chart-readout" aria-live="polite">{selected ? `${date(selected.date)}${selected.date !== selected.end ? ' – ' + date(selected.end) : ''} · ${keys.map(k => `${number(selected[k])} ${k === 'listings' ? 'new listings' : k === 'inquiries' ? 'enquiries' : 'registrations'}`).join(' · ')}` : registration ? 'Hover or focus a point to explore activity.' : 'Hover or focus a bar to explore activity.'}</div></>;
}
function CityChart({ items }) {
  const max = Math.max(1, ...items.flatMap(i => [i.active, i.inquiries]));
  const [focus, setFocus] = useState(null);
  return <><div className="chart-key"><span><i style={{ background: COLORS[0] }} />Active listings now</span><span><i style={{ background: COLORS[1] }} />Enquiries in period</span></div><div className="city-comparison">{items.length ? items.slice(0, 8).map(item => <button key={item.city} onMouseEnter={() => setFocus(item)} onMouseLeave={() => setFocus(null)} onFocus={() => setFocus(item)} onBlur={() => setFocus(null)} aria-label={`${item.city}: ${item.active} active listings, ${item.inquiries} enquiries`}><span>{item.city}</span><div>{['active', 'inquiries'].map((key, i) => <div key={key}><i style={{ width: `${item[key] / max * 100}%`, background: COLORS[i] }} /><b>{item[key]}</b></div>)}</div></button>) : <p className="analytics-empty">No city activity to compare.</p>}</div><div className="chart-readout" aria-live="polite">{focus ? `${focus.city} · ${focus.per_100 == null ? 'No active inventory' : focus.per_100 + ' enquiries per 100 active listings'}` : `Top ${Math.min(items.length, 8)} cities by enquiries. All cities are in the table below.`}</div></>;
}
function Histogram({ items }) {
  const max = Math.max(1, ...items.map(i => i.count));
  return <div className="price-histogram">{items.map(item => <div key={item.label}><div className="histogram-column"><b>{item.count}</b><i style={{ height: `${item.count / max * 60}px` }} title={`${item.label}: ${item.count} listings`} /></div><span>{item.label}</span></div>)}</div>;
}
function Change({ current, previous }) {
  const delta = current - previous;
  return <span className={'analytics-change ' + (delta < 0 ? 'down' : '')}>{delta > 0 ? '+' : ''}{number(delta)} <span>vs previous period</span></span>;
}
function exportCities(data) {
  const cell = value => '"' + String(value ?? '').replace(/^\s*[=+@-]/, "'$&").replaceAll('"', '""') + '"';
  const rows = [['Dataset', 'Period start (IST)', 'Period end (IST)', 'City', 'Active listings now', 'For sale', 'For rent', 'Period enquiries (all listing statuses)', 'Period enquiries on active listings', 'Enquiries per 100 active listings', 'Median sale asking price INR', 'Median monthly rent INR'], ...data.cities.map(c => [datasets[data.dataset], data.period.start, data.period.end, c.city, c.active, c.sale, c.rent, c.inquiries, c.active_inquiries, c.per_100, c.median_sale, c.median_rent])];
  const url = URL.createObjectURL(new Blob(['\ufeff' + rows.map(row => row.map(cell).join(',')).join('\r\n')], { type: 'text/csv;charset=utf-8;' }));
  const link = document.createElement('a'); link.href = url; link.download = `realsite-city-analysis-${data.dataset}-${data.period.end}.csv`; link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export default function Analytics({ navigate }) {
  const [days, setDays] = useState(30), [dataset, setDataset] = useState('all');
  const [data, setData] = useState(null), [error, setError] = useState(''), [revision, setRevision] = useState(0), [pricing, setPricing] = useState('sale');
  useEffect(() => {
    let cancelled = false; setData(null); setError('');
    api(`/admin/analytics?days=${days}&dataset=${dataset}`).then(result => { if (!cancelled) setData(result); }).catch(e => { if (!cancelled) setError(e.message); });
    return () => { cancelled = true; };
  }, [days, dataset, revision]);
  const s = data?.summary;
  return <section className="analytics" aria-label="Portal analytics">
    <div className="analytics-toolbar"><div><label><CalendarDays size={15} />Reporting period<select aria-label="Analytics reporting period" value={days} onChange={e => setDays(Number(e.target.value))}><option value="30">Last 30 days</option><option value="90">Last 90 days</option><option value="365">Last 12 months</option></select></label><label><Building2 size={15} />Listing dataset<select aria-label="Analytics listing dataset" value={dataset} onChange={e => setDataset(e.target.value)}>{Object.entries(datasets).map(([key, title]) => <option value={key} key={key}>{title}</option>)}</select></label></div><span className="analytics-period">{data ? `${date(data.period.start)} ${data.period.start.slice(0,4)} – ${date(data.period.end)} ${data.period.end.slice(0,4)} · IST` : 'Loading selected period…'}</span><div className="analytics-actions"><button onClick={() => setRevision(v => v + 1)} aria-label="Refresh analytics" title="Refresh analytics"><RefreshCw size={16} /></button><button disabled={!data} onClick={() => exportCities(data)}><Download size={16} />Export city report</button></div></div>
    {error ? <div className="analytics-error" role="alert"><p>{error}</p><button onClick={() => setRevision(v => v + 1)}>Try again</button></div> : !data ? <div className="loading"><LoaderCircle className="spin" />Preparing your insights…</div> : <>
      <div className="analytics-kpis">{[
        { label: 'Active listings', value: number(s.active), icon: Building2, sub: `${number(s.sale)} sale · ${number(s.rent)} rent`, foot: `${number(s.new_listings)} listings added in period`, color: 'blue' },
        { label: 'Enquiries received', value: number(s.inquiries), icon: MessageSquare, sub: 'Selected listings, including archived', foot: <Change current={s.inquiries} previous={s.previous_inquiries} />, color: 'teal' },
        { label: 'Median sale asking price', value: price(s.median_sale), icon: IndianRupee, sub: 'Active properties for sale', foot: `${number(s.sale)} listings · Includes open plots`, color: 'purple' },
        { label: 'Median monthly rent', value: price(s.median_rent), icon: IndianRupee, sub: 'Active rental properties', foot: `${number(s.rent)} listings · Asking rent / month`, color: 'amber' },
      ].map(item => <article className={'analytics-kpi ' + item.color} key={item.label}><div><span>{item.label}</span><i><item.icon size={19} /></i></div><strong>{item.value}</strong><p>{item.sub}</p><footer>{item.foot}</footer></article>)}</div>
      <div className="analytics-grid analytics-three-grid"><Panel title="Inventory mix" subtitle="Current active listings"><Donut label="listings" items={[{ label: 'For sale', count: s.sale }, { label: 'For rent', count: s.rent }]} /><div className="panel-summary"><span>{s.owner} owner · {s.synthetic} synthetic</span><span>{s.archived} archived in selected dataset</span></div></Panel><Panel title="Property types" subtitle="Where your supply is concentrated"><Bars items={data.types} color="multi" /></Panel><Panel className="pricing-panel" title="Asking price distribution" subtitle={pricing === 'sale' ? 'Sale prices in INR · Active listings' : 'Monthly rents in INR · Active listings'} action={<div className="chart-toggle" aria-label="Price distribution mode">{['sale','rent'].map(key => <button key={key} aria-pressed={pricing === key} className={pricing === key ? 'selected' : ''} onClick={() => setPricing(key)}>{key === 'sale' ? 'Sale' : 'Rent'}</button>)}</div>}><Histogram items={data.pricing[pricing]} /><p className="chart-readout">Ranges include the lower bound and exclude the upper bound.</p></Panel></div>
      <div className="analytics-grid analytics-three-grid"><Panel title="Account composition" subtitle="Current accounts by role · All datasets"><Donut label="accounts" items={data.accounts.roles} /><div className="panel-summary"><span>{data.accounts.active} active · {data.accounts.suspended} suspended</span><span>{data.accounts.demo} demo accounts included</span></div></Panel><Panel className="registration-panel" title="Account growth" subtitle="New registrations in the selected period"><div className="analytics-stat"><strong>{number(data.accounts.registrations)}</strong><span>new registrations</span><Users size={20} /></div><ActivityChart items={data.activity} registration /><div className="panel-summary"><span>{number(data.accounts.saved_searches)} saved searches · Current total</span></div></Panel><Panel title="Agent review pipeline" subtitle="Current applications across the whole portal" action={<button className="analytics-icon-button" onClick={() => navigate('agents')} aria-label="Open agent reviews"><ArrowUpRight size={18} /></button>}><Bars items={data.agents} color="multi" /><div className="analytics-mini-stats"><div><strong>{number(s.saved_homes)}</strong><span>Current saved homes<br />Selected listing dataset</span></div><div><strong>{number(s.without_inquiries)}</strong><span>Active listings without<br />enquiries in period</span></div></div></Panel></div>
      <div className="analytics-grid analytics-activity-grid"><Panel className="activity-panel" title="Listing & enquiry activity" subtitle={`${data.period.bucket_days === 1 ? 'Daily' : data.period.bucket_days + '-day'} totals · New listings and incoming enquiries`} action={<span className="panel-badge">{number(s.new_listings)} new listings</span>}><ActivityChart items={data.activity} wide /><div className="panel-summary"><Change current={s.new_listings} previous={s.previous_new_listings} /><span>Listing additions, rather than historical inventory size</span></div></Panel></div>
      <div className="analytics-grid analytics-three-grid"><Panel className="city-panel" title="City supply & demand" subtitle="Compare listing supply with enquiry volume"><CityChart items={data.cities} /></Panel><Panel title="Inventory age" subtitle="Days since creation · Active listings"><Bars items={data.age} color="multi" /><p className="chart-readout">Older inventory can warrant a review; age alone does not imply poor performance.</p></Panel><Panel title="Planning signals" subtitle="Practical next steps grounded in portal data" className="planning-panel"><div className="planning-signals">{data.signals.map((item, index) => <div key={item.title}><i>{index === 0 ? <MapPin size={17} /> : index === 1 ? <Building2 size={17} /> : <Users size={17} />}</i><div><h4>{item.title}</h4><p>{item.detail}</p></div><button onClick={() => navigate(item.section)} aria-label={`Review: ${item.title}`}><ChevronRight size={19} /></button></div>)}</div></Panel></div>
      <Panel title="City performance" subtitle="A shared starting point for inventory and acquisition planning" action={<span className="panel-badge">{data.cities.length} cities</span>}><div className="analytics-table-wrap"><table className="analytics-table"><caption>Current listing inventory and selected-period enquiries by city. Rates count only enquiries on currently active listings.</caption><thead><tr><th>City</th><th>Active listings</th><th>Sale / Rent</th><th>Enquiries</th><th>Enquiries / 100 active</th><th>Median sale</th><th>Median rent / mo</th></tr></thead><tbody>{data.cities.map(c => <tr key={c.city}><th scope="row"><MapPin size={13} />{c.city}</th><td><b>{number(c.active)}</b></td><td>{c.sale} / {c.rent}</td><td><span className="table-enquiries">{number(c.inquiries)}</span></td><td>{c.per_100 == null ? '—' : c.per_100}</td><td>{price(c.median_sale)}</td><td>{price(c.median_rent)}</td></tr>)}</tbody></table>{!data.cities.length && <p className="analytics-empty">No cities in this selection.</p>}</div></Panel>
      <div className="analytics-footnote"><Sparkles size={16} /><p>Planning signals describe activity on RealSite; they are not market forecasts. Asking prices are not completed sales or revenue. Owner listings can include testing activity. Last refreshed {new Date(data.generated_at).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', timeZone: 'Asia/Kolkata' })} IST.</p></div>
    </>}
  </section>;
}
