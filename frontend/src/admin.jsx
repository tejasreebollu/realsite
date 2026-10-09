import React, { useEffect, useState } from 'react';
import { ShieldCheck, LoaderCircle, ChevronLeft, ChevronRight } from 'lucide-react';
import { api, money } from './api';
import './admin.css';

export default function AdminPage({ user, ready, signIn, notify, cities, openProperty }) {
  if (!ready) return <div className="loading"><LoaderCircle className="spin" />Loading your account…</div>;
  if (!user) return <div className="page-container"><h1>Administration</h1><p>Sign in with your administrator account to continue.</p><button className="primary" onClick={signIn}>Sign in</button></div>;
  if (user.role !== 'admin') return <div className="page-container"><h1>Administrator access required</h1><p>Your {user.role} account does not have permission to open this dashboard.</p></div>;
  return <Dashboard notify={notify} cities={cities} openProperty={openProperty} />;
}

function Dashboard({ notify, cities, openProperty }) {
  const [tab, setTab] = useState('properties');
  const [city, setCity] = useState('');
  const [status, setStatus] = useState('active');
  const [page, setPage] = useState(1);
  const [revision, setRevision] = useState(0);
  const [summary, setSummary] = useState(null);
  const [rows, setRows] = useState(null);
  const [error, setError] = useState('');
  const [confirm, setConfirm] = useState(null);
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    let cancelled = false;
    setRows(null); setError('');
    const params = new URLSearchParams({ page, page_size: 20, ...(tab === 'properties' ? { city, status } : {}) });
    Promise.all([api('/admin/summary'), api(`/admin/${tab}?${params}`)]).then(([stats, result]) => {
      if (!cancelled) { setSummary(stats); setRows({ ...result, section: tab }); }
    }).catch(e => { if (!cancelled) setError(e.message); });
    return () => { cancelled = true; };
  }, [tab, city, status, page, revision]);
  const moderate = async () => {
    setBusy(true);
    try {
      await api('/admin/properties/' + confirm.id, { method: 'PATCH', body: JSON.stringify({ active: !confirm.active }) });
      notify(confirm.active ? 'Listing archived' : 'Listing restored'); setConfirm(null); setRevision(v => v + 1);
    } catch (e) { notify(e.message); }
    finally { setBusy(false); }
  };
  return <div className="page-container admin-page">
    <span className="eyebrow"><ShieldCheck size={16} /> Administrator workspace</span>
    <h1>Portal overview</h1><p className="page-intro">Review inventory, accounts, and buyer enquiries across India.</p>
    {summary && <><div className="admin-metrics">{[['Active properties', summary.active_properties], ['Synthetic homes', summary.synthetic_properties], ['For sale', summary.sale], ['For rent', summary.rent], ['Accounts', summary.users], ['Enquiries', summary.inquiries]].map(([label, value]) => <article key={label}><span>{label}</span><strong>{value}</strong></article>)}</div>
      <div className="admin-city-counts">{summary.cities.map(c => <span key={c.city}>{c.city}<b>{c.properties}</b></span>)}</div></>}
    <div className="auth-tabs" aria-label="Administration sections">{[['properties', 'Listings'], ['users', 'Accounts'], ['inquiries', 'Enquiries']].map(([key, title]) => <button key={key} className={tab === key ? 'active' : ''} onClick={() => { setRows(null); setTab(key); setPage(1); }}>{title}</button>)}</div>
    {tab === 'properties' && <div className="admin-filters"><label>City<select aria-label="City" value={city} onChange={e => { setCity(e.target.value); setPage(1); }}><option value="">All cities</option>{cities.map(c => <option key={c}>{c}</option>)}</select></label><label>Listing status<select aria-label="Listing status" value={status} onChange={e => { setStatus(e.target.value); setPage(1); }}><option value="active">Active</option><option value="archived">Archived</option><option value="all">All listings</option></select></label></div>}
    {error ? <div role="alert"><p>{error}</p><button className="outline" onClick={() => setRevision(v => v + 1)}>Try again</button></div> : !rows || rows.section !== tab ? <div className="loading"><LoaderCircle className="spin" />Loading records…</div> : <>
      <p className="muted">{rows.total} records · page {page}</p>
      {rows.items.length === 0 ? <p>No records match this selection.</p> : tab === 'properties' ? <div className="admin-table-wrap"><table className="admin-table"><thead><tr><th>Property</th><th>City</th><th>Price</th><th>Status</th><th>Action</th></tr></thead><tbody>{rows.items.map(p => <tr key={p.id}><td><div className="admin-property"><img src={p.images[0]} alt="" loading="lazy" /><div><button className="text-button" disabled={!p.active} onClick={() => openProperty(p)}>{p.title}</button><small>IN-{String(p.id).padStart(5, '0')} · {p.demo ? 'Synthetic' : 'Owner listing'}</small></div></div></td><td>{p.city}</td><td>{money(p.price)}{p.purpose === 'rent' && <small>/month</small>}</td><td><span className={'admin-status ' + (p.active ? '' : 'inactive')}>{p.active ? 'Active' : 'Archived'}</span></td><td><button className="outline" onClick={() => setConfirm(p)}>{p.active ? 'Archive' : 'Restore'}</button></td></tr>)}</tbody></table></div> : tab === 'users' ? <div className="admin-table-wrap"><table className="admin-table"><thead><tr><th>Name</th><th>Email</th><th>Role</th><th>Account</th></tr></thead><tbody>{rows.items.map(u => <tr key={u.id}><td>{u.name}</td><td>{u.email}</td><td><span className="role-badge">{u.role}</span></td><td>{u.demo ? 'Demo account' : 'Registered account'}</td></tr>)}</tbody></table></div> : <div className="admin-enquiries">{rows.items.map(i => <article key={i.id}><h3>{i.sender_name} · {i.property.city}</h3><p className="muted">{i.property.title} · {i.phone}</p><p>{i.message}</p><small>{new Date(i.created_at).toLocaleDateString('en-IN')}{i.visit_date && ` · Visit requested: ${i.visit_date}`}</small></article>)}</div>}
      <div className="admin-pagination"><button className="outline" disabled={page === 1} onClick={() => setPage(p => p - 1)}><ChevronLeft size={16} />Previous</button><button className="outline" disabled={page * 20 >= rows.total} onClick={() => setPage(p => p + 1)}>Next<ChevronRight size={16} /></button></div>
    </>}
    {confirm && <div className="admin-confirm" role="region" aria-label="Confirm listing moderation"><strong>{confirm.active ? 'Archive' : 'Restore'} “{confirm.title}”?</strong><p>{confirm.active ? 'It will disappear from public searches. Its enquiries will remain available.' : 'It will become visible in public searches again.'}</p><div><button className="outline" disabled={busy} onClick={() => setConfirm(null)}>Cancel</button><button className="primary" disabled={busy} onClick={moderate}>{busy ? 'Saving…' : confirm.active ? 'Confirm archive' : 'Confirm restore'}</button></div></div>}
  </div>;
}
