import React from 'react';
import { directions, postedOptions, saleOptions, statusOptions, viewOptions } from './filter-options';
import './more-filters.css';
function FeatureField({ name, label, value, change, options, numeric, ...props }) {
  const update = v => change(name, numeric ? v === '' ? null : Number(v) : v);
  return <label>{label}{options ? <select aria-label={label} value={value ?? ''} onChange={e => update(e.target.value)}><option value="">Not specified</option>{options.map(option => <option key={option}>{option}</option>)}</select> : <input aria-label={label} value={value ?? ''} onChange={e => update(e.target.value)} type={numeric ? 'number' : 'text'} {...props} />}</label>;
}
export default function ListingFeatures({ value = {}, onChange, plot, rental }) {
  const change = (key, val) => onChange({ ...value, [key]: val });
  const select = (key, label, options) => <FeatureField key={key} name={key} label={label} options={options} value={value[key]} change={change} />;
  const number = (key, label, min, max) => <FeatureField key={key} name={key} label={label} numeric min={min} max={max} step="1" value={value[key]} change={change} />;
  const yesNo = (key, label) => <label key={key}>{label}<select aria-label={label} value={value[key] == null ? '' : String(value[key])} onChange={e => change(key, e.target.value === '' ? null : e.target.value === 'true')}><option value="">Not specified</option><option value="true">Yes</option><option value="false">No</option></select></label>;
  return <details className="listing-extra-details"><summary>More property details (optional)</summary><p>Help buyers and tenants find your listing through the filters.</p><div className="extra-fields">
    {select('posted_by','Listed by',postedOptions)}{select('listing_status','Listing status',statusOptions)}{!rental && select('sale_type','Sale type',saleOptions)}{select('ownership','Ownership', ['Freehold','Leasehold'])}
    {number('maintenance','Monthly maintenance (₹)',0,1000000)}{!plot && select('facing','Property facing',directions)}
    {!plot && <>{select('possession','Possession status',['Ready to move','Under construction'])}{number('carpet_sqft','Carpet area (sqft)',1,10000000)}{number('plot_sqft','Attached plot area (sqft)',1,10000000)}{number('parking','Parking spaces',0,20)}{yesNo('covered_parking','Covered parking')}{number('year_built','Year built',1800,2100)}{number('floors','Building storeys',1,100)}{yesNo('basement','Basement')}{yesNo('senior_living','Senior living community')}</>}
    {yesNo('site_visit','Site visit available')}
    {!rental && <FeatureField name="rera_id" label="RERA number (owner supplied)" maxLength={100} value={value.rera_id} change={change} />}
    {!plot && <><FeatureField name="tour_3d_url" label="3D tour link (HTTPS)" maxLength={2000} value={value.tour_3d_url} change={change} placeholder="https://…" /><FeatureField name="video_url" label="Video tour link (HTTPS)" maxLength={2000} value={value.video_url} change={change} placeholder="https://…" /></>}
  </div><fieldset className="listing-amenities extra-checks"><legend>View</legend><div className="amenity-checkboxes">{viewOptions.map(view => <label key={view}><input type="checkbox" checked={(value.views || []).includes(view)} onChange={e => change('views',e.target.checked ? [...(value.views || []),view] : value.views.filter(v => v !== view))} />{view}</label>)}</div></fieldset><p>Provide details you know. A supplied registration number does not mean RealSite has verified it.</p></details>;
}
