import { moreDefaults } from './filter-options';
export async function api(path, options = {}) {
  const headers = { ...(options.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }), ...options.headers };
  const response = await fetch('/api' + path, { credentials: 'same-origin', ...options, headers });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    const message = Array.isArray(error.detail) ? error.detail.map(e => `${e.loc.at(-1)}: ${e.msg}`).join('; ') : error.detail;
    const failure = new Error(message || 'Unable to connect. Please try again.');
    failure.status = response.status;
    throw failure;
  }
  return response.status === 204 ? null : response.json();
}
export const money = value => '₹' + Number(value).toLocaleString('en-IN');
export const compactMoney = value => '₹' + (value >= 10000000 ? `${Number((value / 10000000).toFixed(2))} Cr` : value >= 100000 ? `${Number((value / 100000).toFixed(1))} L` : `${Number((value / 1000).toFixed(1))}K`);
export const initialFilters = { ...moreDefaults, q: 'Hyderabad', polygon: '', boundary_q: '', agent: '', agent_id: '', purpose: 'sale', min_price: 0, max_price: '', price_mode: 'price', min_payment: 0, max_payment: '', down_pct: 20, annual_rate: 8.5, loan_years: 20, credit_band: 'none', beds: 0, baths: 0, beds_match: 'min', baths_match: 'min', kind: '', min_sqft: 0, amenity: '', sort: 'recommended' };
export function queryString(filters) {
  return new URLSearchParams(Object.entries(filters).filter(([key, v]) => (v !== '' || key === 'q') && v !== null && v !== undefined)).toString();
}

export const areaText = item => {
  if (item.kind !== 'Open Plot') return item.sqft.toLocaleString('en-IN') + ' sqft';
  const unit = item.area_unit || 'sqft';
  const value = item.area_value ?? item.sqft;
  return Number(value).toLocaleString('en-IN', { maximumFractionDigits: 2 }) + ' ' + ({sqft: 'sq ft', sqyd: 'sq yd', acre: 'acres'}[unit] || 'sq ft');
};
