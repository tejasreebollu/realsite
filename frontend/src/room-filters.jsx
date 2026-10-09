import React from 'react';

export const roomSummary = (value, match, label) => !value ? '' : match === 'exact' ? `Exactly ${value} ${label}` : match === 'max' ? `Up to ${value} ${label}` : `${value}+ ${label}`;

export default function RoomChoices({ label, value, match, onChange }) {
  const exact = match === 'exact';
  return <section className="room-choice-section">
    <div className="room-choice-heading"><h3>{label}</h3><label className="room-exact-toggle"><input type="checkbox" aria-label={'Use exact match for ' + label.toLowerCase()} checked={exact} onChange={e => onChange(value, e.target.checked ? 'exact' : 'min')} />Use exact match</label></div>
    <div className="segment" role="group" aria-label={label + ' count'}>{[0, 1, 2, 3, 4, 5].map(n => <button type="button" key={n} aria-pressed={value === n} className={value === n ? 'active' : ''} onClick={() => onChange(n, exact ? 'exact' : 'min')}>{n ? n + (exact ? '' : '+') : 'Any'}</button>)}</div>
  </section>;
}
