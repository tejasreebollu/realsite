import React from 'react';
import { areaText, money } from './api';

export default function PropertyFacts({ item }) {
  const plot = item.kind === 'Open Plot';
  const commercial = ['Commercial Building', 'Office', 'Shop'].includes(item.kind);
  const priceUnit = plot ? {sqft: 'sq ft', sqyd: 'sq yd', acre: 'acre'}[item.area_unit || 'sqft'] : 'sqft';
  return <><h3>{plot ? 'Plot details' : 'Property details'}</h3><dl className="facts">
    <dt>Property type</dt><dd>{item.kind}</dd>
    {!plot && !commercial && <><dt>Bedrooms</dt><dd>{item.beds}</dd><dt>Bathrooms</dt><dd>{item.baths}</dd></>}
    {commercial && item.baths > 0 && <><dt>Bathrooms</dt><dd>{item.baths}</dd></>}
    <dt>{plot ? 'Plot area' : 'Built-up area'}</dt><dd>{areaText(item)}</dd>
    <dt>Price per {priceUnit}</dt><dd>{money(Math.round(item.price / (plot ? item.area_value || item.sqft : item.sqft)))}{item.purpose === 'rent' ? '/mo' : ''}</dd>
    {plot && <><dt>Land use</dt><dd>{item.plot_use || 'Not specified'}</dd>{item.plot_facing && <><dt>Facing</dt><dd>{item.plot_facing}</dd></>}{item.road_width_ft && <><dt>Road width</dt><dd>{item.road_width_ft} ft</dd></>}{item.plot_approval && <><dt>Approval (owner supplied)</dt><dd>{item.plot_approval}</dd></>}</>}
    {item.purpose === 'rent' && <><dt>Security deposit</dt><dd>{money(item.deposit || 0)}</dd><dt>Furnishing</dt><dd>{item.furnishing || 'Unfurnished'}</dd>{item.available_from && <><dt>Available from</dt><dd>{new Date(item.available_from + 'T12:00:00').toLocaleDateString('en-IN')}</dd></>}</>}
    <dt>Listing reference</dt><dd>IN-{String(item.id).padStart(5, '0')}</dd>
  </dl></>;
}
