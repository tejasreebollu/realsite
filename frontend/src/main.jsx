import React, { useEffect, useRef, useState, createContext, useContext, useCallback } from 'react';
import { createRoot } from 'react-dom/client';
import { Search, Heart, House, Mail, Bell, Check, ChevronDown, ChevronLeft, ChevronRight, X, SlidersHorizontal, ArrowDown, ArrowRight, MapPin, Menu, Plus, LogOut, BedDouble, Bath, Maximize, Share2, CheckCircle2, Building2, KeyRound, Landmark, ShieldCheck, Calculator, Send, Trash2, Pencil, Map as MapIcon, List, LoaderCircle, ExternalLink, RotateCcw, Home, UserRound } from 'lucide-react';
import { api, money, compactMoney, initialFilters, queryString, areaText } from './api';
import PropertyMap from './map';
import AdminPage from './admin';
import ListingFlow, { propertyTypes, commercialTypes } from './listing';
import PropertyFacts from './property-facts';
import './styles.css';
import './branding.css';

const Context = createContext();
const useApp = () => useContext(Context);
const cities = ['Hyderabad', 'Bengaluru', 'Mumbai', 'Pune', 'New Delhi'];
const cityCoords = { Hyderabad: [17.4401, 78.3910], Bengaluru: [12.9716, 77.5946], Mumbai: [19.0760, 72.8777], Pune: [18.5204, 73.8567], 'New Delhi': [28.6139, 77.2090] };
const amenities = ['Parking', 'Security', 'Power backup', 'Balcony', 'Swimming pool', 'Gym', 'Garden'];

function readRoute() {
  const params = Object.fromEntries(new URLSearchParams(location.search));
  const page = location.pathname.slice(1) || 'home';
  const filters = { ...initialFilters, ...Object.fromEntries(Object.entries(params).filter(([key]) => key in initialFilters)) };
  for (const key of ['min_price', 'beds', 'baths', 'min_sqft']) filters[key] = Number(filters[key]) || 0;
  if (filters.max_price) filters.max_price = Number(filters.max_price);
  return { page, filters, propertyId: Number(params.property) || null };
}

function App() {
  const [route, setRoute] = useState(readRoute);
  const [user, setUser] = useState(null);
  const [authReady, setAuthReady] = useState(false);
  const [authModal, setAuthModal] = useState(false);
  const [favorites, setFavorites] = useState([]);
  const [toast, setToast] = useState('');
  const [info, setInfo] = useState(null);
  const [selected, setSelected] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const toastTimer = useRef();
  const pendingAction = useRef();
  const notify = useCallback(text => { setToast(text); clearTimeout(toastTimer.current); toastTimer.current = setTimeout(() => setToast(''), 5000); }, []);
  const navigate = useCallback((page, filters = initialFilters) => {
    const path = page === 'home' ? '/' : '/' + page;
    history.pushState({}, '', path + (page === 'homes' ? '?' + queryString(filters) : ''));
    setRoute({ page, filters, propertyId: null }); setSelected(null); window.scrollTo(0, 0);
  }, []);
  useEffect(() => {
    const listener = () => { setRoute(readRoute()); setSelected(null); };
    window.addEventListener('popstate', listener);
    api('/auth/me').then(setUser).catch(e => { if (e.status !== 401) notify(e.message); }).finally(() => setAuthReady(true));
    return () => { window.removeEventListener('popstate', listener); clearTimeout(toastTimer.current); };
  }, [notify]);
  useEffect(() => {
    let active = true;
    if (user) api('/favorites').then(items => {
      if (!active) return;
      setFavorites(items);
      // Load the account's saved homes before completing an action from sign-in.
      // Otherwise this response can overwrite a favourite just added by that action.
      if (pendingAction.current) {
        const action = pendingAction.current;
        pendingAction.current = null;
        action();
      }
    }).catch(e => { if (active) notify(e.message); });
    else setFavorites([]);
    return () => { active = false; };
  }, [user, refreshKey, notify]);
  useEffect(() => {
    if (route.propertyId) api('/properties/' + route.propertyId).then(setSelected).catch(e => notify(e.message));
  }, [route.propertyId, notify]);
  const requireAuth = action => { if (user) action(); else { pendingAction.current = action; setAuthModal(true); } };
  const onAuth = loggedIn => { setUser(loggedIn); setAuthModal(false); notify('Welcome, ' + loggedIn.name.split(' ')[0] + '!'); if (!pendingAction.current && loggedIn.role === 'admin') navigate('admin'); };
  const toggleFavorite = async item => {
    const saved = favorites.some(p => p.id === item.id);
    try { await api('/favorites/' + item.id, { method: saved ? 'DELETE' : 'PUT' }); setFavorites(prev => saved ? prev.filter(p => p.id !== item.id) : prev.some(p => p.id === item.id) ? prev : [...prev, item]); notify(saved ? 'Home removed from favourites' : 'Home saved to favourites'); } catch (e) { notify(e.message); }
  };
  const openProperty = item => {
    setSelected(item);
    const url = new URL(location.href); url.searchParams.set('property', item.id); history.pushState({}, '', url.pathname + url.search);
    setRoute(prev => ({ ...prev, propertyId: item.id }));
    try { const recent = JSON.parse(localStorage.getItem('recent-homes') || '[]'); localStorage.setItem('recent-homes', JSON.stringify([item.id, ...recent.filter(id => id !== item.id)].slice(0, 8))); } catch { /* browsing remains available without local storage */ }
  };
  const closeProperty = () => { setSelected(null); const url = new URL(location.href); url.searchParams.delete('property'); history.replaceState({}, '', url.pathname + url.search); setRoute(prev => ({ ...prev, propertyId: null })); };
  const logout = async () => { try { await api('/auth/logout', { method: 'POST' }); setUser(null); navigate('home'); notify('You have signed out'); } catch (e) { notify(e.message); } };
  const value = { user, authReady, favorites, navigate, notify, requireAuth, openProperty, toggleFavorite, setInfo, refreshKey, refresh: () => setRefreshKey(k => k + 1) };
  return <Context.Provider value={value}>
    <a className="skip-link" href="#main">Skip to content</a>
    <Header route={route} logout={logout} signIn={() => setAuthModal(true)} />
    <Sidebar page={route.page} />
    <main id="main" className={'main ' + (route.page === 'homes' ? 'search-main' : '')}>
      {route.page === 'home' ? <HomePage /> : route.page === 'homes' ? <SearchPage route={route} /> : route.page === 'favorites' ? <FavoritesPage /> : route.page === 'updates' ? <SavedSearchesPage /> : route.page === 'plan' || route.page === 'mortgage' ? <MortgagePage /> : route.page === 'inbox' ? <InboxPage /> : route.page === 'sell' || route.page === 'manage' ? <ManagePage /> : route.page === 'agents' ? <AgentsPage /> : route.page === 'admin' ? <AdminPage user={user} ready={authReady} signIn={() => requireAuth(() => {})} notify={notify} cities={cities} openProperty={openProperty} /> : <NotFound />}
    </main>
    {selected && <PropertyDetail item={selected} close={closeProperty} />}
    {authModal && <AuthModal close={() => { setAuthModal(false); pendingAction.current = null; }} onAuth={onAuth} />}
    {info && <Modal title={info.title} close={() => setInfo(null)}><div className="info-copy">{info.content}</div></Modal>}
    {toast && <div className="toast" role="status"><CheckCircle2 size={20} /><span>{toast}</span><button aria-label="Dismiss notification" onClick={() => setToast('')}><X size={16} /></button></div>}
  </Context.Provider>;
}

function Logo() { return <span className="logo"><img className="logo-image" src="/realsite-logo.svg" alt="RealSite" width="190" height="48" /></span>; }

function Header({ route, logout, signIn }) {
  const { user, navigate, setInfo } = useApp();
  const [menu, setMenu] = useState(false);
  const go = (page, filters) => { setMenu(false); navigate(page, filters); };
  return <header className="header">
    <button className="brand-button" aria-label="RealSite home" onClick={() => go('home')}><Logo /></button>
    <nav className={'header-left ' + (menu ? 'menu-open' : '')} aria-label="Main navigation">
      <button className={route.page === 'homes' && route.filters.purpose === 'sale' && route.filters.kind !== 'Open Plot' ? 'nav-active' : ''} onClick={() => go('homes', { ...initialFilters, purpose: 'sale' })}>Buy</button>
      <button className={route.page === 'homes' && route.filters.kind === 'Open Plot' ? 'nav-active' : ''} onClick={() => go('homes', { ...initialFilters, kind: 'Open Plot' })}>Open plots</button>
      <button className={route.page === 'homes' && route.filters.purpose === 'rent' ? 'nav-active' : ''} onClick={() => go('homes', { ...initialFilters, purpose: 'rent' })}>Rent</button>
      <button onClick={() => go('sell')}>Sell</button><button onClick={() => go('mortgage')}>Get a home loan</button><button onClick={() => go('agents')}>Find an agent</button>
    </nav>
    <nav className="header-right" aria-label="Account navigation">{user?.role === 'admin' && <button onClick={() => go('admin')}>Admin</button>}<button className="optional-nav" onClick={() => go('manage')}>Manage listings</button><button className="optional-nav" onClick={() => setInfo({ title: 'Reach your next buyer', content: <><p>Publish your home or rental to make it discoverable in city searches and on the map. Property owners can review buyer and tenant enquiries from their inbox.</p><button className="primary" onClick={() => { setInfo(null); go('sell'); }}>Create a listing</button><p className="muted">Paid advertising and promoted listings are planned integrations.</p></> })}>Advertise</button><button className="help-nav" onClick={() => setInfo({ title: 'How can we help?', content: <><h3>Find your next home</h3><p>Search a city, neighbourhood, or PIN code. Filter by budget, bedrooms, property type, and amenities. Switch between map and list on mobile.</p><h3>Save and connect</h3><p>Create an account to save homes, save searches, and send enquiries. Your saved searches and enquiry history are available from the left navigation.</p><h3>List your property</h3><p>Use Sell or Manage listings to publish, edit, and archive your properties.</p><p className="notice">Sample listings are fictional. Enquiries on sample listings are recorded for demonstration and do not contact an agent.</p></> })}>Get help</button>{user ? <div className="account"><span className="avatar">{user.name.charAt(0).toUpperCase()}</span><span className="account-name">{user.name.split(' ')[0]}</span><span className="role-badge">{user.role}</span><button className="icon-button" onClick={logout} aria-label="Sign out"><LogOut size={18} /></button></div> : <button className="primary sign-in" onClick={signIn}>Sign in</button>}</nav>
    <button className="mobile-menu icon-button" aria-label={menu ? 'Close navigation' : 'Open navigation'} aria-expanded={menu} onClick={() => setMenu(!menu)}>{menu ? <X /> : <Menu />}</button>
  </header>;
}

function Sidebar({ page }) {
  const { navigate, user } = useApp();
  const tabs = [{ page: 'homes', text: 'Search', icon: Search }, { page: 'updates', text: 'Updates', icon: Bell }, { page: 'favorites', text: 'Favourites', icon: Heart }, { page: 'plan', text: 'Plan', icon: House }, { page: 'inbox', text: 'Inbox', icon: Mail }];
  if (user?.role === 'admin') tabs.push({ page: 'admin', text: 'Admin', icon: ShieldCheck });
  return <aside className="sidebar" aria-label="Your home search">{tabs.map(tab => <button key={tab.page} className={(page === tab.page ? 'active' : '')} onClick={() => navigate(tab.page)} aria-label={tab.text} aria-current={page === tab.page ? 'page' : undefined}><span><tab.icon size={23} strokeWidth={2.7} fill={['Heart', 'House'].includes(tab.icon.displayName) ? 'currentColor' : 'none'} /></span><small>{tab.text}</small></button>)}<div className="sidebar-bottom"><span>IN</span></div></aside>;
}

function SearchInput({ value, setValue, onSubmit, hero = false }) {
  const [focused, setFocused] = useState(false);
  const matches = cities.filter(c => c.toLowerCase().includes(value.toLowerCase()));
  return <div className={'search-input-wrap ' + (hero ? 'hero-input' : '')}>
    <form className="search-input" onSubmit={e => { e.preventDefault(); setFocused(false); onSubmit(value); }}>
      <input aria-label="Search city, neighbourhood, or PIN code" placeholder="Enter an address, neighbourhood, city, or PIN code" value={value} onChange={e => setValue(e.target.value)} onFocus={() => setFocused(true)} onBlur={() => setTimeout(() => setFocused(false), 150)} autoComplete="off" />
      {value && !hero && <button type="button" className="clear-search" aria-label="Clear search" onClick={() => setValue('')}><X size={15} /></button>}
      <button aria-label="Search homes" type="submit"><Search size={hero ? 25 : 20} strokeWidth={2.7} /></button>
    </form>
    {focused && matches.length > 0 && <div className="suggestions">{matches.map(city => <button key={city} onMouseDown={e => e.preventDefault()} onClick={() => { setValue(city); setFocused(false); onSubmit(city); }}><MapPin size={18} /><span>{city}<small>Explore homes in {city}</small></span><ArrowRight size={16} /></button>)}</div>}
  </div>;
}

function HomePage() {
  const { navigate, refreshKey, notify } = useApp();
  const [search, setSearch] = useState('');
  const [sections, setSections] = useState(null);
  const [error, setError] = useState('');
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    let cancelled = false;
    Promise.all([api('/properties?q=Hyderabad&purpose=sale&page_size=8'), api('/properties?q=Bengaluru&purpose=sale&page_size=8'), api('/properties?q=Mumbai&purpose=rent&page_size=8')]).then(data => { if (!cancelled) { setSections(data); setError(''); } }).catch(e => { if (!cancelled) setError(e.message); });
    return () => { cancelled = true; };
  }, [refreshKey, retry]);
  return <>
    <section className="hero" aria-label="Find your next home"><div className="hero-shade" /><div className="hero-content"><h1>Rentals. Homes.<br />Agents. Loans.</h1><SearchInput hero value={search} setValue={setSearch} onSubmit={q => navigate('homes', { ...initialFilters, q: q || 'Hyderabad' })} /><span className="hero-subtitle">Your next chapter starts with a place to call home.</span></div><div className="hero-location"><MapPin size={14} /> Find your place in India</div></section>
    <div className="home-content"><div className="market-line"><span><span className="live-dot" /> A home for every next chapter</span><span>Explore India <span aria-hidden="true">↗</span></span></div>
      {error ? <ErrorState message={error} retry={() => setRetry(r => r + 1)} /> : !sections ? <Loading text="Finding homes for you…" /> : <><PropertyCarousel title="Continue searching: Hyderabad, For Sale" subtitle={`${sections[0].total} homes to explore`} items={sections[0].items} /><Buyability /><PropertyCarousel title="Homes for you in Bengaluru" subtitle="A fresh perspective on your next move" items={sections[1].items} /><PropertyCarousel title="Find your next rental in Mumbai" subtitle="Homes and spaces that fit your next chapter" items={sections[2].items} /><RecentHomes /></>}
      <button className="more-homes" onClick={() => navigate('homes')}><ArrowDown size={18} /> More homes to discover</button>
    </div>
    <section className="services"><div className="service-grid"><ServiceCard type="buy" title="Buy a property" text="Explore apartments, villas, buildings, commercial spaces and open plots." button="Browse homes" onClick={() => navigate('homes')} /><ServiceCard type="rent" title="Rent a home" text="Discover a space that fits your life. Explore apartments, villas, and houses across India." button="Find rentals" onClick={() => navigate('homes', { ...initialFilters, purpose: 'rent' })} /><ServiceCard type="sell" title="Sell a property" text="Whatever your next chapter looks like, we’ll help you put your property in front of the right people." button="See your options" onClick={() => navigate('sell')} /></div></section>
    <section className="city-section"><h2>Find a home in a city you love</h2><div className="city-grid">{cities.map((city, index) => <button key={city} onClick={() => navigate('homes', { ...initialFilters, q: city })}><img src={'/images/home-' + (index + 4) + '.jpg'} alt="" loading="lazy" /><span>{city}<small>Discover homes <ArrowRight size={13} /></small></span></button>)}</div></section>
    <Footer />
  </>;
}

function PropertyCard({ item, rental = false, onHover }) {
  const { favorites, requireAuth, toggleFavorite, openProperty } = useApp();
  const [photo, setPhoto] = useState(0);
  useEffect(() => { setPhoto(0); }, [item.id, item.images.join('|')]);
  const saved = favorites.some(p => p.id === item.id);
  return <article className="property-card" data-property-id={item.id} onMouseEnter={() => onHover?.(item.id)} onMouseLeave={() => onHover?.(null)}>
    <div className="property-image"><button className="image-open" aria-label={'View ' + item.title} onClick={() => openProperty(item)}><img src={item.images[photo]} alt={item.title + ' — ' + (item.demo ? 'illustrative sample photo' : 'property photo')} loading="lazy" onError={e => { if (!e.currentTarget.src.endsWith('/images/unavailable.svg')) e.currentTarget.src = '/images/unavailable.svg'; }} /></button><span className="property-badge">{item.badge}</span><button className={'favorite-button ' + (saved ? 'saved' : '')} aria-label={saved ? 'Remove from favourites' : 'Save to favourites'} aria-pressed={saved} onClick={() => requireAuth(() => toggleFavorite(item))}><Heart size={29} strokeWidth={2.5} fill={saved ? 'currentColor' : 'rgba(0,0,0,.16)'} /></button>
      <button className="photo-arrow photo-prev" aria-label="Previous photo" onClick={() => setPhoto((photo + item.images.length - 1) % item.images.length)}><ChevronLeft size={19} /></button><button className="photo-arrow photo-next" aria-label="Next photo" onClick={() => setPhoto((photo + 1) % item.images.length)}><ChevronRight size={19} /></button>
      <div className="photo-dots">{item.images.map((_, i) => <button key={i} className={i === photo ? 'current' : ''} aria-label={'Photo ' + (i + 1)} onClick={() => setPhoto(i)} />)}</div><span className="listing-photo-label">{item.demo ? item.kind === 'Open Plot' ? 'SAMPLE PLOT' : 'SAMPLE PROPERTY' : 'OWNER LISTING'}</span>
    </div>
    <button className="property-copy" onClick={() => openProperty(item)}><div className="price-row"><strong>{money(item.price)}{item.purpose === 'rent' && <small>/mo</small>}</strong>{item.purpose === 'rent' && rental && <span className="verified"><CheckCircle2 size={13} /> Monthly rent</span>}</div><div className="property-spec">{item.kind !== 'Open Plot' && !commercialTypes.includes(item.kind) && <><span><b>{item.beds}</b> bds</span><i /><span><b>{item.baths}</b> ba</span><i /></>}<span><b>{areaText(item)}</b></span><i /><span>{item.kind}</span></div><p className="property-address">{item.address}, {item.city}, {item.pincode}</p><p className="property-agent">{item.demo ? 'DEMO LISTING' : 'LISTED BY OWNER'} · {item.agent.toUpperCase()}</p></button>
    {rental && item.purpose === 'rent' && <div className="rental-action"><span><ShieldCheck size={14} /> {item.amenities.slice(0, 2).join(' · ')}</span><button className="primary" onClick={() => openProperty(item)}>Check availability</button></div>}
  </article>;
}

function PropertyCarousel({ title, subtitle, items }) {
  const ref = useRef();
  return <section className="carousel-section"><div className="section-header"><div><h2>{title}</h2><p>{subtitle}</p></div><div className="carousel-controls"><button className="round-button" aria-label={'Previous homes in ' + title} onClick={() => ref.current.scrollBy({ left: -700, behavior: 'smooth' })}><ChevronLeft size={21} /></button><button className="round-button" aria-label={'Next homes in ' + title} onClick={() => ref.current.scrollBy({ left: 700, behavior: 'smooth' })}><ChevronRight size={21} /></button></div></div><div className="property-carousel" ref={ref}>{items.map(item => <PropertyCard key={item.id} item={item} />)}</div></section>;
}

function RecentHomes() {
  const [items, setItems] = useState([]);
  useEffect(() => { try { const ids = JSON.parse(localStorage.getItem('recent-homes') || '[]'); Promise.allSettled(ids.map(id => api('/properties/' + id))).then(results => setItems(results.filter(r => r.status === 'fulfilled').map(r => r.value))); } catch { /* storage may be disabled */ } }, []);
  return items.length ? <PropertyCarousel title="Recently viewed" subtitle="Pick up where you left off" items={items} /> : null;
}

function Buyability() {
  const { navigate } = useApp();
  return <section className="buyability"><div className="buyability-illustration"><Calculator size={40} /><span><House size={65} /></span><div className="illustration-spark">✦</div></div><div><span className="eyebrow">A little clarity goes a long way</span><h2>Find your home. Know your budget.</h2><p>Explore what a monthly payment could look like before you make your next move.</p></div><button className="outline" onClick={() => navigate('plan')}>Calculate your budget <ArrowRight size={17} /></button></section>;
}

function ServiceIllustration({ type }) {
  return <svg className="service-art" viewBox="0 0 180 140" aria-hidden="true"><path d="M38 112C4 87 26 33 62 22c40-21 100-3 104 40 9 47-31 70-76 69z" fill="#fff0e2" />{type === 'buy' ? <><path d="M39 82 91 39l52 43v44H39z" fill="#007c68" /><path d="M27 83 91 29l64 54" stroke="#082e75" strokeWidth="11" fill="none" /><path d="M70 83h34v43H70z" fill="#ffab67" /><path d="M112 82h17v20h-17z" fill="#d9f4ff" /><circle cx="143" cy="49" r="21" fill="#0344da" /><path d="m132 49 8 8 13-15" stroke="white" strokeWidth="5" fill="none" /></> : type === 'rent' ? <><path d="M48 31h70v96H48z" fill="#ff744d" /><path d="M43 27h81v9H43z" fill="#182c43" />{[0, 1, 2].map(row => [0, 1].map(col => <path key={row + '-' + col} d={`M${60 + col * 28} ${45 + row * 24}h16v17h-16z`} fill="#fff" />))}<path d="M77 109h18v18H77z" fill="#ffbc3f" /><path d="m118 78 27-12v61h-27z" fill="#0041d9" /><path d="M23 113q-2-30 21-30v44H23z" fill="#008675" /></> : <><path d="M44 30h9v96h-9zM47 30h90v8H47z" fill="#d58d00" /><path d="M72 47h67v57H72z" fill="#0041d9" /><path d="M67 49h8v59h-8z" fill="#ffbb20" /><path d="m84 76 15-13 18 13v19H84z" fill="#70d7ef" /><path d="M101 82c-12-12-18 5 0 12 18-7 12-24 0-12" fill="white" /><path d="m119 111 24-19 21 19v16h-45z" fill="#fb713d" /><path d="M17 127q3-21 20-15 7-17 27 2 20-4 27 13" fill="#008675" /></>}</svg>;
}
function ServiceCard({ type, title, text, button, onClick }) { return <article className="service-card"><ServiceIllustration type={type} /><h2>{title}</h2><p>{text}</p><button className="outline" onClick={onClick}>{button}</button></article>; }

function SearchPage({ route }) {
  const { navigate, requireAuth, notify, refreshKey } = useApp();
  const filters = route.filters;
  const [search, setSearch] = useState(filters.q);
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [retry, setRetry] = useState(0);
  const [bounds, setBounds] = useState(null);
  const [mapItems, setMapItems] = useState([]);
  const [hovered, setHovered] = useState(null);
  const [mobileView, setMobileView] = useState('list');
  const [popup, setPopup] = useState('');
  const [draft, setDraft] = useState(filters);
  const key = queryString(filters);
  useEffect(() => { setSearch(filters.q); setDraft(filters); setPage(1); setBounds(null); }, [key]);
  useEffect(() => {
    const controller = new AbortController(); setLoading(true); setError('');
    const params = queryString({ ...filters, ...bounds, page, page_size: 24 });
    api('/properties?' + params, { signal: controller.signal }).then(result => { setData(result); setLoading(false); }).catch(e => { if (e.name !== 'AbortError') { setError(e.message); setLoading(false); } });
    return () => controller.abort();
  }, [key, page, JSON.stringify(bounds), refreshKey, retry]);
  useEffect(() => {
    const controller = new AbortController();
    api('/properties?' + queryString({ ...filters, ...bounds, page_size: 100 }), { signal: controller.signal }).then(d => setMapItems(d.items)).catch(e => { if (e.name !== 'AbortError') setMapItems([]); });
    return () => controller.abort();
  }, [key, JSON.stringify(bounds), refreshKey, retry]);
  const update = change => { navigate('homes', { ...filters, ...change }); setPopup(''); };
  const save = () => requireAuth(async () => { try { await api('/saved-searches', { method: 'POST', body: JSON.stringify({ name: `${filters.q || 'India'} · ${filters.purpose === 'sale' ? 'For sale' : 'For rent'}`, filters: Object.fromEntries(Object.entries(filters).filter(([, v]) => v !== '')) }) }); notify('Search saved. Find it in Updates.'); } catch (e) { notify(e.message); } });
  const showFilter = name => { setPopup(popup === name ? '' : name); setDraft(filters); };
  const applied = filters.min_price > 0 || filters.max_price || filters.beds > 0 || filters.baths > 0 || filters.kind || filters.min_sqft > 0 || filters.amenity;
  return <>
    <div className="filter-bar"><SearchInput value={search} setValue={setSearch} onSubmit={q => update({ q })} /><div className="filters-container">
      <div className="filter-wrap"><button className="filter-button selected" onClick={() => showFilter('purpose')} aria-expanded={popup === 'purpose'}>{filters.purpose === 'sale' ? 'For sale' : 'For rent'}<ChevronDown size={18} /></button>{popup === 'purpose' && <div className="filter-popover small-popover">{['sale', 'rent'].map(purpose => <button className="option-button" key={purpose} onClick={() => update({ purpose, kind: purpose === 'rent' && filters.kind === 'Open Plot' ? '' : filters.kind, min_price: 0, max_price: '' })}>{purpose === 'sale' ? 'For sale' : 'For rent'}{filters.purpose === purpose && <Check size={16} />}</button>)}</div>}</div>
      <div className="filter-wrap"><button className={'filter-button ' + (filters.min_price || filters.max_price ? 'selected' : '')} onClick={() => showFilter('price')} aria-expanded={popup === 'price'}>Price<ChevronDown size={18} /></button>{popup === 'price' && <div className="filter-popover"><h3>Price range {filters.purpose === 'rent' && '(monthly)'}</h3><div className="form-grid"><label>Minimum (₹)<input type="number" min="0" value={draft.min_price || ''} placeholder="No minimum" onChange={e => setDraft({ ...draft, min_price: Number(e.target.value) })} /></label><label>Maximum (₹)<input type="number" min={draft.min_price || 0} value={draft.max_price} placeholder="No maximum" onChange={e => setDraft({ ...draft, max_price: e.target.value ? Number(e.target.value) : '' })} /></label></div><button className="primary full" onClick={() => { if (draft.max_price && draft.max_price < draft.min_price) { notify('Maximum price must be higher than the minimum'); return; } update({ min_price: draft.min_price, max_price: draft.max_price }); }}>Apply</button></div>}</div>
      {filters.kind !== 'Open Plot' && !commercialTypes.includes(filters.kind) && <div className="filter-wrap"><button className={'filter-button ' + (filters.beds || filters.baths ? 'selected' : '')} onClick={() => showFilter('beds')} aria-expanded={popup === 'beds'}>Beds & baths<ChevronDown size={18} /></button>{popup === 'beds' && <div className="filter-popover"><h3>Bedrooms</h3><div className="segment">{[0, 1, 2, 3, 4, 5].map(n => <button key={n} className={draft.beds === n ? 'active' : ''} onClick={() => setDraft({ ...draft, beds: n })}>{n ? n + '+' : 'Any'}</button>)}</div><h3>Bathrooms</h3><div className="segment">{[0, 1, 2, 3, 4].map(n => <button key={n} className={draft.baths === n ? 'active' : ''} onClick={() => setDraft({ ...draft, baths: n })}>{n ? n + '+' : 'Any'}</button>)}</div><button className="primary full" onClick={() => update({ beds: draft.beds, baths: draft.baths })}>Apply</button></div>}</div>}
      <div className="filter-wrap"><button className={'filter-button ' + (filters.kind ? 'selected' : '')} onClick={() => showFilter('kind')} aria-expanded={popup === 'kind'}>Property type<ChevronDown size={18} /></button>{popup === 'kind' && <div className="filter-popover small-popover">{['', ...propertyTypes, 'Open Plot'].map(kind => <button className="option-button" key={kind} onClick={() => update({ kind, beds: 0, baths: 0 })}>{kind || 'All types'}{filters.kind === kind && <Check size={16} />}</button>)}</div>}</div>
      <div className="filter-wrap"><button className={'filter-button ' + (filters.amenity || filters.min_sqft || filters.kind ? 'selected' : '')} onClick={() => showFilter('more')} aria-expanded={popup === 'more'}><SlidersHorizontal size={17} />Filters<ChevronDown size={18} /></button>{popup === 'more' && <div className="filter-popover more-popover"><h3>More ways to find your home</h3><label>Property type<select aria-label="Property type" value={draft.kind} onChange={e => setDraft({ ...draft, kind: e.target.value })}>{['', ...propertyTypes, 'Open Plot'].map(kind => <option value={kind} key={kind}>{kind || 'All types'}</option>)}</select></label><label>Minimum area (sqft)<input type="number" min="0" value={draft.min_sqft || ''} onChange={e => setDraft({ ...draft, min_sqft: Number(e.target.value) })} placeholder="Any size" /></label><label>Amenities<select value={draft.amenity} onChange={e => setDraft({ ...draft, amenity: e.target.value })}>{['', 'Parking', 'Swimming pool', 'Gym', 'Garden', 'Balcony'].map(a => <option value={a} key={a}>{a || 'Any amenity'}</option>)}</select></label><button className="primary full" onClick={() => update({ ...(draft.kind === 'Open Plot' || commercialTypes.includes(draft.kind) ? { beds: 0, baths: 0 } : {}), kind: draft.kind, min_sqft: draft.min_sqft, amenity: draft.amenity })}>Apply filters</button></div>}</div>
      <button className="primary save-search" aria-label="Save search" onClick={save}>Save search</button>
    </div></div>
    {popup && <button className="popover-backdrop" aria-label="Close filters" onClick={() => setPopup('')} />}
    <div className={'search-layout view-' + mobileView}>
      <div className="map-pane"><PropertyMap items={mapItems} city={filters.q} hovered={hovered} rental={filters.purpose === 'rent'} total={data?.total || 0} onBounds={value => { setBounds(value); setPage(1); }} hasBounds={!!bounds} /></div>
      <section className="results-pane" aria-label="Property search results"><div className="results-heading"><h1>{filters.q || 'India'} {filters.kind === 'Open Plot' ? 'Open Plots For Sale' : filters.purpose === 'rent' ? 'Rental Listings' : 'Real Estate & Properties For Sale'}</h1><div className="results-meta"><span>{loading ? 'Searching…' : `${data?.total || 0} results`}</span><label className="sort">Sort: <select aria-label="Sort homes" value={filters.sort} onChange={e => update({ sort: e.target.value })}><option value="recommended">Homes for you</option><option value="price_asc">Price (low to high)</option><option value="price_desc">Price (high to low)</option><option value="newest">Newest</option><option value="sqft">Largest area</option></select></label></div>{applied && <div className="applied-filters"><span>Filters applied</span><button onClick={() => update({ ...initialFilters, q: filters.q, purpose: filters.purpose })}><X size={13} /> Reset</button></div>}</div>
        {error ? <ErrorState message={error} retry={() => setRetry(r => r + 1)} /> : loading ? <Loading text="Finding your next home…" /> : data?.items.length ? <><div className="results-grid">{data.items.map(item => <PropertyCard key={item.id} item={item} rental onHover={setHovered} />)}</div><div className="pagination"><button className="outline" disabled={page === 1} onClick={() => { setPage(p => p - 1); document.querySelector('.results-pane')?.scrollTo(0, 0); }}><ChevronLeft size={16} /> Previous</button><span>Page {page} of {Math.ceil(data.total / 24)}</span><button className="outline" disabled={page * 24 >= data.total} onClick={() => { setPage(p => p + 1); document.querySelector('.results-pane')?.scrollTo(0, 0); }}>Next <ChevronRight size={16} /></button></div><p className="results-note">Sample homes use illustrative photography. All prices are in Indian rupees.</p></> : <Empty icon={Search} title="Let’s widen the search" text="No homes match these filters. Try a different area, a higher budget, or fewer filters." button="Reset filters" onClick={() => update({ ...initialFilters, q: filters.q, purpose: filters.purpose })} />}
      </section>
    </div><button className="mobile-view-toggle primary" onClick={() => setMobileView(mobileView === 'map' ? 'list' : 'map')}>{mobileView === 'map' ? <List size={19} /> : <MapIcon size={19} />}{mobileView === 'map' ? 'List' : 'Map'}</button>
  </>;
}

function Modal({ title, close, children, wide = false }) {
  const ref = useRef();
  const closeRef = useRef(close); closeRef.current = close;
  useEffect(() => {
    const previous = document.activeElement;
    const original = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    const focus = () => ref.current?.querySelector('input, button, select, textarea, a[href]')?.focus(); focus();
    const listener = e => {
      if (Array.from(document.querySelectorAll('.modal')).at(-1) !== ref.current) return;
      if (e.key === 'Escape') closeRef.current();
      if (e.key === 'Tab') {
        const controls = Array.from(ref.current.querySelectorAll('input, button, select, textarea, a[href], [tabindex="0"]')).filter(el => !el.disabled && el.offsetParent !== null);
        if (!controls.length) return;
        const first = controls[0], last = controls.at(-1);
        if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
        else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
      }
    };
    window.addEventListener('keydown', listener);
    return () => { document.body.style.overflow = original; window.removeEventListener('keydown', listener); previous?.focus(); };
  }, []);
  return <div className="modal-backdrop" onMouseDown={e => { if (e.target === e.currentTarget) close(); }}><section ref={ref} role="dialog" aria-modal="true" aria-label={title} className={'modal ' + (wide ? 'wide-modal' : '')}><div className="modal-header"><h2>{title}</h2><button className="icon-button" aria-label="Close dialog" onClick={close}><X size={24} /></button></div>{children}</section></div>;
}

function AuthModal({ close, onAuth }) {
  const [tab, setTab] = useState('login');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const submit = async e => {
    e.preventDefault(); setBusy(true); setError(''); const body = Object.fromEntries(new FormData(e.currentTarget));
    try { const user = await api('/auth/' + tab, { method: 'POST', body: JSON.stringify(body) }); onAuth(user); } catch (e) { setError(e.message); } finally { setBusy(false); }
  };
  return <Modal title="Welcome home" close={close}><div className="auth-logo"><Logo /></div><p className="modal-intro">Buy, rent, and sell homes with one account.</p><div className="auth-tabs"><button className={tab === 'login' ? 'active' : ''} onClick={() => { setTab('login'); setError(''); }}>Sign in</button><button className={tab === 'register' ? 'active' : ''} onClick={() => { setTab('register'); setError(''); }}>Create account</button></div><form className="stack-form" onSubmit={submit}>{tab === 'register' && <label>Your name<input name="name" autoComplete="name" minLength={2} maxLength={100} required placeholder="Full name" /></label>}<label>Email address<input name="email" type="email" autoComplete="email" required placeholder="you@example.com" /></label><label>Password<input name="password" type="password" autoComplete={tab === 'register' ? 'new-password' : 'current-password'} minLength={tab === 'register' ? 10 : 1} maxLength={128} required placeholder={tab === 'register' ? 'At least 10 characters' : 'Enter your password'} /></label>{error && <p className="form-error" role="alert">{error}</p>}<button className="primary full" disabled={busy}>{busy ? <LoaderCircle className="spin" size={18} /> : null}{tab === 'register' ? 'Create your account' : 'Sign in'}</button></form><p className="fine-print">Your account saves favourites, searches, and enquiries. Welcome to RealSite. Sample properties are fictional and provided for demonstration.</p></Modal>;
}

function PropertyDetail({ item, close }) {
  const { favorites, requireAuth, toggleFavorite, notify } = useApp();
  const [photo, setPhoto] = useState(0);
  useEffect(() => { setPhoto(0); }, [item.id, item.images.join('|')]);
  const [tab, setTab] = useState('overview');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [sent, setSent] = useState(false);
  const saved = favorites.some(p => p.id === item.id);
  const submit = e => {
    e.preventDefault(); const form = Object.fromEntries(new FormData(e.currentTarget));
    if (!form.visit_date) delete form.visit_date;
    requireAuth(async () => { setBusy(true); setError(''); try { await api('/inquiries', { method: 'POST', body: JSON.stringify({ property_id: item.id, ...form }) }); setSent(true); notify(item.demo ? 'Demo enquiry recorded in your inbox' : 'Enquiry sent to the owner’s inbox'); } catch (e) { setError(e.message); } finally { setBusy(false); } });
  };
  return <Modal title={item.title} close={close} wide><div className="detail-gallery"><img src={item.images[photo]} alt={item.title + ' photo ' + (photo + 1)} onError={e => { if (!e.currentTarget.src.endsWith('/images/unavailable.svg')) e.currentTarget.src = '/images/unavailable.svg'; }} /><button className="gallery-nav left" aria-label="Previous property photo" onClick={() => setPhoto((photo + item.images.length - 1) % item.images.length)}><ChevronLeft /></button><button className="gallery-nav right" aria-label="Next property photo" onClick={() => setPhoto((photo + 1) % item.images.length)}><ChevronRight /></button><span className="gallery-count">{photo + 1} / {item.images.length} photos</span><div className="detail-actions"><button className={'outline ' + (saved ? 'saved' : '')} onClick={() => requireAuth(() => toggleFavorite(item))}><Heart size={17} fill={saved ? 'currentColor' : 'none'} />{saved ? 'Saved' : 'Save'}</button><button className="outline" onClick={async () => { try { await navigator.clipboard.writeText(location.href); notify('Property link copied'); } catch { notify('Copy the property link from your browser address bar'); } }}><Share2 size={17} />Share</button></div></div>
    <div className="detail-layout"><div className="detail-main"><div className="detail-price">{money(item.price)}{item.purpose === 'rent' && <small>/month</small>}<span className="status-dot">For {item.purpose === 'sale' ? 'sale' : 'rent'}</span></div><div className="detail-specs">{item.kind !== 'Open Plot' && !commercialTypes.includes(item.kind) && <><span><BedDouble size={22} /><b>{item.beds}</b> beds</span><span><Bath size={22} /><b>{item.baths}</b> baths</span></>}<span><Maximize size={21} /><b>{areaText(item)}</b></span>{(item.kind === 'Open Plot' || commercialTypes.includes(item.kind)) && <span>{item.kind}</span>}</div><p className="detail-address"><MapPin size={18} />{item.address}, {item.city}, {item.state} {item.pincode}</p><div className="detail-tabs"><button className={tab === 'overview' ? 'active' : ''} onClick={() => setTab('overview')}>Overview</button><button className={tab === 'features' ? 'active' : ''} onClick={() => setTab('features')}>Facts & features</button><button className={tab === 'location' ? 'active' : ''} onClick={() => setTab('location')}>Location</button></div>{tab === 'overview' ? <><h3>What’s special</h3><div className="amenity-tags"><span>{item.badge}</span>{item.amenities.slice(0, 3).map(a => <span key={a}>{a}</span>)}</div><p className="description">{item.description}</p><div className="agent-line"><span className="avatar">{item.agent[0]}</span><div><b>{item.agent}</b><small>{item.demo ? 'Sample agent profile' : 'Property owner'}</small></div></div></> : tab === 'features' ? <><PropertyFacts item={item} /><h3>Amenities</h3><div className="amenity-tags">{item.amenities.map(a => <span key={a}><Check size={14} />{a}</span>)}</div></> : <><h3>Your neighbourhood</h3><div className="detail-map"><PropertyMap items={[item]} city={item.city} total={1} small /></div><p className="muted">{item.demo ? 'Illustrative sample location. Check the exact address with the owner for real listings.' : 'Location supplied by the owner. Verify it before visiting.'}</p></>}{item.demo && <p className="notice"><ShieldCheck size={18} /> Fictional sample listing with illustrative photography. Not an actual offer for sale or rent.</p>}</div>
    <aside className="contact-card">{sent ? <div className="enquiry-success"><CheckCircle2 size={44} /><h3>{item.demo ? 'Demo enquiry recorded' : 'Enquiry sent'}</h3><p>{item.demo ? 'Your enquiry is saved in your inbox and the property owner’s inbox. No external messages are sent.' : 'The owner can view your message in their inbox.'}</p><button className="outline" onClick={() => setSent(false)}>Send another enquiry</button></div> : <><h3>{item.purpose === 'rent' ? 'Check availability' : 'Make this your next move'}</h3><p>Ask a question or request a visit.</p><form className="stack-form" onSubmit={submit}><label>Mobile number<input name="phone" type="tel" placeholder="9876543210" pattern="(\+91[ -]?)?[6-9][0-9]{9}" required /></label><label>Preferred visit date <small>(optional)</small><input name="visit_date" type="date" min={new Date().toLocaleDateString('en-CA')} /></label><label>Your message<textarea aria-label="Your message" name="message" minLength={10} maxLength={2000} rows={4} required defaultValue={`I’m interested in this ${item.kind === 'Open Plot' || commercialTypes.includes(item.kind) ? item.kind.toLowerCase() : item.beds + ' BHK ' + item.kind.toLowerCase()}. Please share more details.`} /></label>{error && <p className="form-error" role="alert">{error}</p>}<button className="primary full" disabled={busy}>{busy ? <LoaderCircle size={17} className="spin" /> : <Send size={16} />}{item.demo ? 'Record demo enquiry' : 'Contact owner'}</button></form><p className="fine-print">{item.demo ? 'Sample listings do not contact real agents.' : 'Your message and phone number will be visible to the property owner.'}</p></>}</aside></div>
  </Modal>;
}

function AuthGate({ children, title }) {
  const { user, authReady, requireAuth } = useApp();
  if (!authReady) return <Loading text="Loading your account…" />;
  if (!user) return <div className="page-container"><Empty icon={KeyRound} title={title || 'Your home search, together'} text="Sign in to keep your saved homes, searches, and conversations in one place." button="Sign in or create an account" onClick={() => requireAuth(() => {})} /></div>;
  return children;
}
function FavoritesPage() { return <AuthGate title="Make room for your favourites"><FavoritesContent /></AuthGate>; }
function FavoritesContent() {
  const { favorites, navigate } = useApp();
  return <div className="page-container"><span className="eyebrow">Your shortlist</span><h1>Saved homes</h1><p className="page-intro">{favorites.length ? `${favorites.length} ${favorites.length === 1 ? 'place' : 'places'} you could call home.` : 'A little heart, a lot of possibilities.'}</p>{favorites.length ? <div className="standalone-grid">{favorites.map(p => <PropertyCard key={p.id} item={p} />)}</div> : <Empty icon={Heart} title="Your favourites start here" text="Tap the heart on any listing to save it. Your favourite homes will be waiting here." button="Explore homes" onClick={() => navigate('homes')} />}</div>;
}

function SavedSearchesPage() { return <AuthGate title="Keep your search close"><SavedSearchesContent /></AuthGate>; }
function SavedSearchesContent() {
  const { navigate, notify } = useApp();
  const [items, setItems] = useState(null);
  const [error, setError] = useState('');
  const load = () => api('/saved-searches').then(d => { setItems(d); setError(''); }).catch(e => setError(e.message));
  useEffect(() => { load(); }, []);
  const remove = async id => { try { await api('/saved-searches/' + id, { method: 'DELETE' }); setItems(items.filter(s => s.id !== id)); notify('Search removed'); } catch (e) { notify(e.message); } };
  return <div className="page-container"><span className="eyebrow">Pick up where you left off</span><h1>Saved searches</h1><p className="page-intro">Your preferred areas and filters, ready whenever you are. Email alerts are not enabled.</p>{error ? <ErrorState message={error} retry={load} /> : items === null ? <Loading /> : !items.length ? <Empty icon={Bell} title="Keep a good search going" text="Use Save search on the search page to keep your city and filters here." button="Find a home" onClick={() => navigate('homes')} /> : <div className="saved-search-list">{items.map(s => <article key={s.id}><div className="search-symbol"><Search size={25} /></div><div><h2>{s.name}</h2><p>{s.filters.beds ? s.filters.beds + '+ bedrooms · ' : ''}{s.filters.kind || 'All property types'}{s.filters.max_price ? ' · Up to ' + money(s.filters.max_price) : ''}</p><small>Saved {new Date(s.created_at).toLocaleDateString('en-IN')}</small></div><button className="outline" onClick={() => navigate('homes', { ...initialFilters, ...s.filters })}>View homes <ArrowRight size={16} /></button><button className="icon-button" aria-label={'Delete ' + s.name} onClick={() => remove(s.id)}><Trash2 size={19} /></button></article>)}</div>}</div>;
}

function InboxPage() { return <AuthGate title="Stay connected to your next move"><InboxContent /></AuthGate>; }
function InboxContent() {
  const { navigate, openProperty } = useApp();
  const [items, setItems] = useState(null);
  const [error, setError] = useState('');
  const load = () => api('/inquiries').then(d => { setItems(d); setError(''); }).catch(e => setError(e.message));
  useEffect(() => { load(); }, []);
  return <div className="page-container"><span className="eyebrow">Your conversations</span><h1>Inbox</h1><p className="page-intro">Enquiries you’ve sent and messages received for your listings.</p>{error ? <ErrorState message={error} retry={load} /> : items === null ? <Loading /> : !items.length ? <Empty icon={Mail} title="Every move starts with a conversation" text="Send an enquiry from any property to ask a question or request a visit." button="Browse homes" onClick={() => navigate('homes')} /> : <div className="inquiry-list">{items.map(i => <article key={i.id}><img src={i.property.images[0]} alt="Property" /><div><div className="inquiry-top"><span className="eyebrow">{i.direction === 'received' ? 'Received from ' + i.sender_name : 'Sent enquiry'}{i.property.demo ? ' · Demo' : ''}</span><small>{new Date(i.created_at).toLocaleDateString('en-IN')}</small></div><button className="text-button" onClick={() => i.property.active && openProperty(i.property)}>{i.property.title}{!i.property.active && ' (archived)'}</button><p>{i.message}</p><div className="inquiry-bottom"><span>{i.phone}</span>{i.visit_date && <span>Visit requested: {new Date(i.visit_date + 'T12:00:00').toLocaleDateString('en-IN')}</span>}</div>{i.property.demo && <small className="muted">Recorded for demonstration in the sender and property owner inboxes. No external messages are sent.</small>}</div></article>)}</div>}</div>;
}

function MortgagePage() {
  const { navigate } = useApp();
  const [price, setPrice] = useState(10000000);
  const [down, setDown] = useState(20);
  const [rate, setRate] = useState(8.5);
  const [years, setYears] = useState(20);
  const principal = Math.max(0, price * (1 - down / 100));
  const r = rate / 1200, n = years * 12;
  const emi = r ? principal * r * (1 + r) ** n / ((1 + r) ** n - 1) : principal / n;
  const interest = Math.max(0, emi * n - principal);
  return <div className="page-container mortgage-page"><span className="eyebrow">Plan your next chapter</span><h1>A clearer picture of home.</h1><p className="page-intro">Estimate your monthly home loan payment and explore homes within your budget.</p><div className="mortgage-layout"><section className="calculator-card"><h2>Home loan EMI calculator</h2><label>Home price <strong>{money(price)}</strong><input type="range" aria-label="Home price" min="1000000" max="100000000" step="100000" value={price} onChange={e => setPrice(Number(e.target.value))} /><input aria-label="Exact home price" type="number" min="100000" max="1000000000" value={price} onChange={e => setPrice(Math.min(1000000000, Math.max(0, Number(e.target.value))))} /></label><label>Down payment <strong>{down}% · {money(price * down / 100)}</strong><input type="range" aria-label="Down payment" min="0" max="90" value={down} onChange={e => setDown(Number(e.target.value))} /></label><div className="form-grid"><label>Interest rate (% p.a.)<input type="number" min="0" max="25" step="0.1" value={rate} onChange={e => setRate(Math.min(25, Math.max(0, Number(e.target.value))))} /></label><label>Loan tenure<select value={years} onChange={e => setYears(Number(e.target.value))}>{[5, 10, 15, 20, 25, 30].map(y => <option key={y} value={y}>{y} years</option>)}</select></label></div><p className="fine-print">Illustrative calculation. The default interest rate is an assumption, not a lender quote. Taxes, insurance, maintenance, stamp duty, registration fees, and other charges are excluded. Actual loan eligibility and rates depend on your lender.</p></section><section className="payment-card"><div className="payment-icon"><Landmark size={30} /></div><span>Estimated monthly payment</span><strong className="emi">{money(Math.round(emi))}<small>/mo</small></strong><div className="payment-chart" style={{ '--principal': `${principal / (principal + interest || 1) * 100}%` }}><div><Home size={29} /><span>Your home,<br />your future.</span></div></div><dl className="payment-facts"><dt><i className="legend blue" />Loan amount</dt><dd>{money(Math.round(principal))}</dd><dt><i className="legend pale" />Total interest</dt><dd>{money(Math.round(interest))}</dd><dt>Total repayment</dt><dd>{money(Math.round(emi * n))}</dd></dl><button className="primary full" onClick={() => navigate('homes', { ...initialFilters, max_price: price })}>Find homes in this budget <ArrowRight size={17} /></button></section></div></div>;
}

function ManagePage() {
  const { user, navigate, requireAuth } = useApp();
  return user ? <ManageContent /> : <div className="seller-page"><div className="seller-copy"><span className="eyebrow">A new chapter for your home</span><h1>Let’s find its<br />next people.</h1><p>List your property for sale or rent. Add the details that make it special, reach people looking in your area, and manage enquiries in one place.</p><button className="primary" onClick={() => requireAuth(() => {})}>Get started <ArrowRight size={18} /></button><div className="seller-benefits"><span><CheckCircle2 size={18} />Free listing</span><span><CheckCircle2 size={18} />Your details, your control</span><span><CheckCircle2 size={18} />Direct enquiries</span></div></div><img className="seller-image" src="/images/home-5.jpg" alt="A welcoming home with a garden" /></div>;
}

function ManageContent() {
  const { notify, refresh, refreshKey } = useApp();
  const [items, setItems] = useState(null);
  const [edit, setEdit] = useState(null);
  const [error, setError] = useState('');
  const [archive, setArchive] = useState(null);
  const load = () => api('/me/listings').then(d => { setItems(d); setError(''); }).catch(e => setError(e.message));
  useEffect(() => { load(); }, [refreshKey]);
  const remove = async () => { try { await api('/properties/' + archive.id, { method: 'DELETE' }); setArchive(null); refresh(); notify('Listing archived'); } catch (e) { notify(e.message); } };
  return <div className="page-container"><div className="page-heading"><div><span className="eyebrow">Make your property’s next move</span><h1>Your listings</h1><p className="page-intro">Publish a property and manage buyer or tenant enquiries from your inbox.</p></div><button className="primary" onClick={() => setEdit({})}><Plus size={18} /> Add a listing</button></div>{error ? <ErrorState message={error} retry={load} /> : items === null ? <Loading /> : !items.length ? <Empty icon={Building2} title="Every property has a story" text="Tell yours. Add photos, a price, and the details that make your property special." button="Create your first listing" onClick={() => setEdit({})} /> : <div className="standalone-grid">{items.map(item => <div className={'managed-property ' + (!item.active ? 'archived' : '')} key={item.id}><PropertyCard item={item} /><div className="manage-actions">{item.active ? <><button className="text-button" onClick={() => setEdit(item)}><Pencil size={15} />Edit listing</button><button className="text-button danger" onClick={() => setArchive(item)}><Trash2 size={15} />Archive</button></> : <span>Archived · hidden from searches</span>}</div></div>)}</div>}{edit && <ListingForm item={edit} close={() => setEdit(null)} saved={() => { setEdit(null); refresh(); notify(edit.id ? 'Your changes are saved' : 'Your listing is live!'); }} />}{archive && <Modal title="Archive this listing?" close={() => setArchive(null)}><p className="modal-intro">{archive.title} will be removed from public searches. Existing enquiries remain in your inbox.</p><div className="confirm-actions"><button className="outline" onClick={() => setArchive(null)}>Keep listing</button><button className="primary" onClick={remove}>Archive listing</button></div></Modal>}</div>;
}

function ListingForm(props) { return <ListingFlow {...props} Modal={Modal} />; }

function AgentsPage() {
  const { navigate } = useApp();
  const [city, setCity] = useState('Hyderabad');
  return <div className="page-container"><span className="eyebrow">People who know the neighbourhood</span><h1>Find your local expert.</h1><p className="page-intro">Explore sample agent profiles and their properties. Real agent onboarding and verification are planned.</p><label className="agent-city">Explore agents in<select value={city} onChange={e => setCity(e.target.value)}>{cities.map(c => <option key={c}>{c}</option>)}</select></label><div className="agents-grid">{['Ananya Sharma', 'Arjun Reddy', 'Priya Mehta', 'Vikram Rao'].map((name, i) => <article className="agent-card" key={name}><div className={'agent-avatar agent-' + i}><UserRound size={55} strokeWidth={1.4} /></div><h2>{name}</h2><p><MapPin size={15} /> {city}</p><span className="sample-tag">Sample profile</span><p className="agent-bio">Explore a selection of demonstration homes and discover what’s possible in your next neighbourhood.</p><button className="outline" onClick={() => navigate('homes', { ...initialFilters, q: city, agent: name })}>View sample listings <ArrowRight size={16} /></button></article>)}</div></div>;
}

function Loading({ text = 'Loading…' }) { return <div className="loading" role="status"><LoaderCircle className="spin" size={24} /><p>{text}</p></div>; }
function ErrorState({ message, retry }) { return <div className="error-state" role="alert"><h2>We couldn’t load this right now</h2><p>{message}</p><button className="outline" onClick={retry}><RotateCcw size={16} />Try again</button></div>; }
function Empty({ icon: Icon, title, text, button, onClick }) { return <div className="empty-state"><span className="empty-icon"><Icon size={42} strokeWidth={1.5} /></span><h2>{title}</h2><p>{text}</p>{button && <button className="primary" onClick={onClick}>{button}<ArrowRight size={17} /></button>}</div>; }
function NotFound() { const { navigate } = useApp(); return <Empty icon={House} title="Let’s get you back home" text="This page isn’t available." button="Go to homepage" onClick={() => navigate('home')} />; }
function Footer() {
  const { navigate, setInfo } = useApp();
  return <footer className="footer"><div className="footer-links">{cities.map(city => <button key={city} onClick={() => navigate('homes', { ...initialFilters, q: city })}>{city} real estate</button>)}<button onClick={() => setInfo({ title: 'About this portal', content: <><p>RealSite helps buyers, tenants and property owners find their next home across India.</p><p>Fictional sample listings and illustrative Unsplash photographs are provided for evaluation. One public account can buy, rent and sell properties or plots. Administrators have a separate workspace.</p><p>Live property feeds, verified agents, lender integrations, notification delivery, and paid services require separate integrations.</p></> })}>About</button><a href="/api/docs" target="_blank" rel="noreferrer">API documentation</a></div><p>Find the place where your next chapter begins.</p><p className="fine-print">RealSite · Homes across India · Prices in INR · Sample listings are fictional.<br />Illustrative photography from Unsplash. Maps © OpenStreetMap contributors.</p><button className="brand-button" onClick={() => navigate('home')}><Logo /></button><div className="footer-skyline" aria-hidden="true"><span /><span /><span /><span /><span /><span /><span /><span /><span /></div></footer>;
}

createRoot(document.getElementById('root')).render(<App />);
