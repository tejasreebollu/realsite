import React, { useEffect, useState } from 'react';
import { Calculator, LoaderCircle } from 'lucide-react';
import { api, compactMoney, money, queryString } from './api';
import './price-filter.css';

export const demoRates = { none: 8.5, '800plus': 8.25, '750799': 8.5, '700749': 9, '650699': 9.5, below650: 10.5 };
export function priceSummary(filters) {
  const payment = filters.price_mode === 'payment';
  const low = payment ? filters.min_payment : filters.min_price;
  const high = payment ? filters.max_payment : filters.max_price;
  if (!low && (high === '' || high == null)) return payment ? 'Estimated monthly loan payments' : '';
  const range = low && high != null && high !== '' ? `${compactMoney(low)}–${compactMoney(high)}` : low ? `${compactMoney(low)}+` : `Up to ${compactMoney(high)}`;
  return payment ? `Est. EMI ${range}/mo` : filters.purpose === 'rent' ? `Rent ${range}/mo` : `Price ${range}`;
}

export default function PriceFilter({ filters, bounds, draft, setDraft, apply, calculate, close }) {
  const [distribution, setDistribution] = useState(null);
  const [chartError, setChartError] = useState('');
  const [error, setError] = useState('');
  const rental = filters.purpose === 'rent';
  const monthly = !rental && draft.price_mode === 'payment';
  const context = queryString({ ...filters, ...bounds, price_mode: 'price', min_price: 0, max_price: '', min_payment: 0, max_payment: '' });
  useEffect(() => {
    const controller = new AbortController();
    setDistribution(null); setChartError('');
    api('/properties/price-distribution?' + context, { signal: controller.signal }).then(setDistribution).catch(e => { if (e.name !== 'AbortError') setChartError('Price distribution is unavailable. You can still enter a range.'); });
    return () => controller.abort();
  }, [context]);
  const minKey = monthly ? 'min_payment' : 'min_price';
  const maxKey = monthly ? 'max_payment' : 'max_price';
  const low = Number(draft[minKey] || 0);
  const high = draft[maxKey] === '' || draft[maxKey] == null ? null : Number(draft[maxKey]);
  const limit = monthly ? 20000000 : 2000000000;
  const domain = distribution?.domain_max || (rental ? 100000 : 50000000);
  const sliderLow = Math.min(domain, Math.max(0, low));
  const sliderHigh = Math.min(domain, Math.max(0, high ?? domain));
  const bars = distribution?.counts || [];
  const tallest = Math.max(1, ...bars);
  const update = change => { setError(''); setDraft(current => ({ ...current, ...change })); };
  const switchMode = mode => update({ price_mode: mode });
  const submit = e => {
    e.preventDefault();
    if (!Number.isInteger(low) || low < 0 || low > limit || (high != null && (!Number.isInteger(high) || high < 0 || high > limit))) { setError('Enter whole rupee amounts within the allowed range.'); return; }
    if (high != null && high < low) { setError('Maximum must be greater than or equal to minimum.'); return; }
    apply({ price_mode: monthly ? 'payment' : 'price', min_price: monthly ? 0 : low, max_price: monthly ? '' : high ?? '', min_payment: monthly ? low : 0, max_payment: monthly ? high ?? '' : '', down_pct: draft.down_pct, annual_rate: draft.annual_rate, loan_years: draft.loan_years, credit_band: draft.credit_band });
  };
  return <form className="filter-popover price-filter-popover" role="dialog" aria-label="Price range" onSubmit={submit} onKeyDown={e => { if (e.key === 'Escape') { e.stopPropagation(); close(); } }}>
    <div className="price-filter-heading">Price Range{rental && <small> / month</small>}</div>
    <div className="price-mode-tabs" role="tablist" aria-label="Price filter mode">{(rental ? [['price', 'Monthly Rent']] : [['price', 'List Price'], ['payment', 'Monthly Payment']]).map(([mode, title]) => <button type="button" role="tab" id={'price-' + mode + '-tab'} aria-controls="price-filter-controls" aria-selected={draft.price_mode === mode || rental} tabIndex={draft.price_mode === mode || rental ? 0 : -1} key={mode} onClick={() => switchMode(mode)} onKeyDown={e => { if (!rental && ['ArrowLeft', 'ArrowRight'].includes(e.key)) { e.preventDefault(); const next = mode === 'price' ? 'payment' : 'price'; switchMode(next); e.currentTarget.parentElement.querySelector('#price-' + next + '-tab')?.focus(); } }}>{title}</button>)}</div>
    {!rental && <button className="price-budget-link" type="button" onClick={calculate}><Calculator size={17} />Calculate your budget</button>}
    <div id="price-filter-controls" role="tabpanel" aria-labelledby={'price-' + (monthly ? 'payment' : 'price') + '-tab'}>
      {!monthly && <div className="price-distribution">
        <div className="price-bars" role="img" aria-label={distribution ? `Price distribution of ${distribution.total} matching properties` : 'Loading price distribution'}>{distribution?.total > 0 ? bars.map((count, i) => <span key={i} title={`${count} properties: ${compactMoney(i * domain / bars.length)}–${compactMoney((i + 1) * domain / bars.length)}`} style={{ height: count ? Math.max(5, count / tallest * 100) + '%' : 0 }} className={(i + 1) * domain / bars.length >= low && (high == null || i * domain / bars.length <= high) ? 'in-range' : ''} />) : <p className="price-chart-message">{chartError || (distribution ? 'No matching properties in this search.' : <><LoaderCircle size={15} className="spin" />Loading price distribution</>)}</p>}</div>
        <div className="price-slider-track"><span style={{ left: sliderLow / domain * 100 + '%', right: 100 - sliderHigh / domain * 100 + '%' }} /></div>
        <div className="price-slider-inputs"><input type="range" aria-label="Minimum price slider" min="0" max={domain} step={Math.max(1, Math.round(domain / 100))} value={sliderLow} onChange={e => update({ min_price: Math.min(Number(e.target.value), sliderHigh) })} /><input type="range" aria-label="Maximum price slider" min="0" max={domain} step={Math.max(1, Math.round(domain / 100))} value={sliderHigh} onChange={e => { const value = Math.max(Number(e.target.value), sliderLow); update({ max_price: value === domain ? '' : value }); }} /></div>
        <div className="price-axis"><span>₹0</span><span>{compactMoney(domain)}+</span></div>
        {distribution && <p className="price-chart-caption">Based on {distribution.total} matching {distribution.total === 1 ? 'property' : 'properties'}</p>}
      </div>}
      <div className="price-range-fields"><label>Min<div className="price-rupee-input"><span>₹</span><input aria-label={monthly ? 'Minimum monthly payment (₹)' : 'Minimum price (₹)'} type="number" inputMode="numeric" min="0" max={limit} step="1" placeholder="No min" value={draft[minKey] || ''} onChange={e => update({ [minKey]: e.target.value === '' ? 0 : Number(e.target.value) })} /></div></label><span className="price-range-dash">–</span><label>Max<div className="price-rupee-input"><span>₹</span><input aria-label={monthly ? 'Maximum monthly payment (₹)' : 'Maximum price (₹)'} type="number" inputMode="numeric" min="0" max={limit} step="1" placeholder="No max" value={draft[maxKey] ?? ''} onChange={e => update({ [maxKey]: e.target.value === '' ? '' : Number(e.target.value) })} /></div></label></div>
      {monthly && <><div className="price-finance-fields"><label><span>Down Payment</span><select aria-label="Down payment" value={draft.down_pct} onChange={e => update({ down_pct: Number(e.target.value) })}>{[...new Set([0, 10, 20, 25, 30, 40, 50, 75, 90, Number(draft.down_pct)])].sort((a, b) => a - b).map(n => <option key={n} value={n}>{n ? n + '% of price' : 'No down payment'}</option>)}</select></label><label><span>Credit Score <small title="Demo planning scenarios; your credit score is not checked and these rates are not lender quotes.">demo scenario</small></span><select aria-label="Credit score" value={draft.credit_band} onChange={e => update({ credit_band: e.target.value, annual_rate: demoRates[e.target.value] })}><option value="none">No selection</option><option value="800plus">800–900</option><option value="750799">750–799</option><option value="700749">700–749</option><option value="650699">650–699</option><option value="below650">300–649</option></select></label></div><p className="price-estimate-note">Estimated loan EMI only. {draft.annual_rate}% p.a. · {draft.loan_years} years. Taxes, insurance, maintenance and fees are extra.</p><details className="price-assumptions"><summary>Edit rate &amp; tenure</summary><div className="price-finance-fields"><label>Annual rate (%)<input aria-label="Assumed annual interest rate" type="number" min="0" max="25" step="0.05" value={draft.annual_rate} onChange={e => update({ annual_rate: Number(e.target.value) })} /></label><label>Loan tenure<select aria-label="Assumed loan tenure" value={draft.loan_years} onChange={e => update({ loan_years: Number(e.target.value) })}>{[...new Set([5, 10, 15, 20, 25, 30, Number(draft.loan_years)])].sort((a, b) => a - b).map(y => <option key={y} value={y}>{y} years</option>)}</select></label></div></details></>}
      {error && <p className="price-error" role="alert">{error}</p>}
    </div>
    <div className="price-filter-actions"><button type="button" className="outline" onClick={() => update({ min_price: 0, max_price: '', min_payment: 0, max_payment: '' })}>Clear</button><button type="submit" className="primary">Apply</button></div>
  </form>;
}
