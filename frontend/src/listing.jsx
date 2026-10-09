import React, { useEffect, useRef, useState } from 'react';
import { MapContainer, TileLayer, Marker, useMap, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import { Building2, MapPin, KeyRound, Upload, ImagePlus, X, Check, ChevronLeft, ArrowRight, LoaderCircle, LocateFixed, MoveUp, MoveDown, MoveLeft, MoveRight } from 'lucide-react';
import { api, money, areaText } from './api';
import 'leaflet/dist/leaflet.css';
import './listing.css';

export const propertyTypes = ['Apartment', 'Villa', 'House', 'Building', 'Commercial Building', 'Office', 'Shop'];
export const commercialTypes = ['Commercial Building', 'Office', 'Shop'];
const cityInfo = {
  Hyderabad: ['Telangana', 17.4401, 78.3910], Bengaluru: ['Karnataka', 12.9716, 77.5946],
  Mumbai: ['Maharashtra', 19.0760, 72.8777], Pune: ['Maharashtra', 18.5204, 73.8567],
  'New Delhi': ['Delhi', 28.6139, 77.2090],
};
const homeAmenities = ['Parking', 'Security', 'Power backup', 'Balcony', 'Swimming pool', 'Gym', 'Garden'];
const plotAmenities = ['Water supply', 'Electricity', 'Boundary wall', 'Gated community', 'Security'];
const choices = [
  { mode: 'sale', title: 'Sell a property', text: 'Apartments, villas, houses, buildings and commercial spaces.', icon: Building2 },
  { mode: 'plot', title: 'Sell an open plot', text: 'Residential, commercial or agricultural land.', icon: MapPin },
  { mode: 'rent', title: 'Rent a property', text: 'Homes, buildings, offices and shops available for rent.', icon: KeyRound },
];
const stages = ['Details', 'Location', 'Photos', 'Review'];
const pinIcon = L.divIcon({ className: 'listing-pin-icon', html: '<span class="listing-pin-dot"></span>', iconSize: [32, 42], iconAnchor: [16, 42] });

function Field({ label, name, form, change, options, ...props }) {
  return <label>{label}{options ? <select aria-label={label} name={name} value={form[name] ?? ''} onChange={e => change(name, e.target.value)} {...props}>{options.map(option => {
    const [value, text] = Array.isArray(option) ? option : [option, option];
    return <option key={value} value={value}>{text}</option>;
  })}</select> : <input aria-label={label} name={name} value={form[name] ?? ''} onChange={e => change(name, e.target.value)} {...props} />}</label>;
}

function PickerEvents({ onSelect, onCenter, selected }) {
  const map = useMapEvents({
    click: e => onSelect({ lat: e.latlng.lat, lng: e.latlng.lng }),
    moveend: () => onCenter(map.getCenter()),
  });
  useEffect(() => { map.invalidateSize(); onCenter(map.getCenter()); }, []);
  useEffect(() => { if (selected) map.panTo([selected.lat, selected.lng]); }, [selected?.lat, selected?.lng]);
  return null;
}

export function LocationPicker({ city, selected, onChange }) {
  const initial = cityInfo[city]?.slice(1) || [20.6, 78.9];
  const [center, setCenter] = useState({ lat: selected?.lat ?? initial[0], lng: selected?.lng ?? initial[1] });
  const [error, setError] = useState('');
  const [locating, setLocating] = useState(false);
  const [tilesUnavailable, setTilesUnavailable] = useState(false);
  const select = value => {
    if (value.lat < 6 || value.lat > 38 || value.lng < 68 || value.lng > 98) {
      setError('Choose a location in India.'); return;
    }
    setError(''); onChange({ lat: value.lat, lng: value.lng });
  };
  const locate = () => {
    if (!navigator.geolocation) { setError('Location access is unavailable. Select a point on the map.'); return; }
    setLocating(true);
    navigator.geolocation.getCurrentPosition(position => {
      select({ lat: position.coords.latitude, lng: position.coords.longitude }); setLocating(false);
    }, () => { setError('Unable to get your location. You can select it on the map.'); setLocating(false); }, { enableHighAccuracy: true, timeout: 10000 });
  };
  return <section className="listing-location-picker" aria-label="Select property location">
    <div className="listing-section-heading"><div><h3>Pin your property on the map</h3><p>Click the map or drag the pin to the entrance of your property.</p></div></div>
    <div className="listing-location-map">
      <MapContainer center={[center.lat, center.lng]} zoom={selected ? 15 : cityInfo[city] ? 13 : 5} scrollWheelZoom={false}>
        <TileLayer url="https://tile.openstreetmap.org/{z}/{x}/{y}.png" attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' eventHandlers={{ tileerror: () => setTilesUnavailable(true) }} />
        <PickerEvents onSelect={select} onCenter={setCenter} selected={selected} />
        {selected && <Marker position={[selected.lat, selected.lng]} icon={pinIcon} draggable eventHandlers={{ dragend: e => { const point = e.target.getLatLng(); select(point); } }} />}
      </MapContainer>
    </div>
    <div className="location-picker-actions"><button type="button" className="outline" onClick={() => select(center)}><MapPin size={16} />Place pin at map centre</button><button type="button" className="text-button" onClick={locate} disabled={locating}>{locating ? <LoaderCircle className="spin" size={16} /> : <LocateFixed size={16} />}Use my location</button></div>
    {selected && <div className="pin-adjustment"><span>Fine-tune your pin</span>{[[MoveUp, 'north', .0005, 0], [MoveDown, 'south', -.0005, 0], [MoveLeft, 'west', 0, -.0005], [MoveRight, 'east', 0, .0005]].map(([Icon, direction, lat, lng]) => <button key={direction} type="button" className="outline" aria-label={'Move pin ' + direction} onClick={() => select({ lat: selected.lat + lat, lng: selected.lng + lng })}><Icon size={16} /></button>)}</div>}
    <p className={'location-selection-status ' + (selected ? 'selected' : '')} role="status">{selected ? <><Check size={16} />Location selected. You can move the pin anytime.</> : 'Select a location to continue.'}</p>
    {tilesUnavailable && <p className="fine-print">Map tiles are unavailable. You can still place the pin or use your location.</p>}
    {error && <p className="form-error" role="alert">{error}</p>}
  </section>;
}

function PhotoUpload({ images, onChange, onBusy }) {
  const [busy, setBusy] = useState(false), [error, setError] = useState(''), [progress, setProgress] = useState('');
  const controller = useRef(null);
  useEffect(() => () => controller.current?.abort(), []);
  const upload = async files => {
    const selected = Array.from(files);
    if (!selected.length || busy) return;
    setError('');
    if (images.length + selected.length > 10) { setError('You can add up to 10 photos. Choose fewer files or remove a photo.'); return; }
    if (selected.some(file => !['image/jpeg', 'image/png', 'image/webp'].includes(file.type) || file.size > 5 * 1024 * 1024)) {
      setError('Choose JPEG, PNG or WebP photos, each 5 MB or smaller.'); return;
    }
    setBusy(true); onBusy(true); controller.current = new AbortController();
    const updated = [...images];
    try {
      for (let i = 0; i < selected.length; i++) {
        setProgress('Uploading photo ' + (i + 1) + ' of ' + selected.length);
        const body = new FormData(); body.append('file', selected[i]);
        const result = await api('/uploads', { method: 'POST', body, signal: controller.current.signal });
        updated.push(result.url); onChange([...updated]);
      }
      setProgress(selected.length + (selected.length === 1 ? ' photo added' : ' photos added'));
    } catch (e) { if (e.name !== 'AbortError') setError(e.message); }
    finally { setBusy(false); onBusy(false); }
  };
  return <section className="photo-upload-section" aria-label="Property photos">
    <h3>Make a great first impression</h3><p>Add clear photos of your property. Your first photo is the cover.</p>
    <div className={'photo-dropzone ' + (busy ? 'uploading' : '')} onDragOver={e => e.preventDefault()} onDrop={e => { e.preventDefault(); upload(e.dataTransfer.files); }}>
      <label className="photo-upload-label">{busy ? <LoaderCircle className="spin" size={32} /> : <ImagePlus size={36} />}<strong>{busy ? 'Adding your photos…' : 'Choose photos or drag them here'}</strong><span>JPEG, PNG or WebP · Up to 5 MB each · Maximum 10 photos</span><input type="file" aria-label="Upload property photos" accept="image/jpeg,image/png,image/webp" multiple disabled={busy || images.length >= 10} onChange={e => { upload(e.target.files); e.target.value = ''; }} /></label>
    </div>
    <div className="upload-progress" role="status">{progress || images.length + ' of 10 photos added'}</div>
    {error && <p className="form-error" role="alert">{error}</p>}
    <div className="listing-photo-grid">{images.map((url, index) => <figure key={url}><img src={url} alt={'Property photo ' + (index + 1)} /><span className="cover-label">{index === 0 ? 'Cover photo' : 'Photo ' + (index + 1)}</span><button type="button" className="photo-remove" aria-label={'Remove photo ' + (index + 1)} disabled={busy} onClick={() => onChange(images.filter((_, i) => i !== index))}><X size={16} /></button>{index > 0 && <button type="button" className="make-cover" disabled={busy} aria-label={'Set photo ' + (index + 1) + ' as cover'} onClick={() => onChange([url, ...images.filter((_, i) => i !== index)])}>Make cover</button>}</figure>)}</div>
    <p className="fine-print">Use photos you own or have permission to use. Avoid including personal documents or phone numbers.</p>
  </section>;
}

function ListingWizard({ mode, item, close, saved, Modal, changeType }) {
  const plot = mode === 'plot', rental = mode === 'rent';
  const [step, setStep] = useState(0), [busy, setBusy] = useState(false), [uploading, setUploading] = useState(false), [error, setError] = useState('');
  const [location, setLocation] = useState(item.id ? { lat: item.lat, lng: item.lng } : null);
  const [form, setForm] = useState(() => ({
    title: item.title || '', kind: plot ? 'Open Plot' : item.kind || 'Apartment',
    price: item.price ?? '', beds: item.beds ?? 3, baths: item.baths ?? 2,
    sqft: item.sqft ?? '', area_unit: item.area_unit || (plot ? 'sqyd' : 'sqft'),
    area_value: item.area_value ?? (plot ? item.sqft ?? '' : ''),
    city: item.city || 'Hyderabad', state: item.state || 'Telangana', address: item.address || '', pincode: item.pincode || '',
    description: item.description || '', images: item.images || [], amenities: item.amenities || (plot ? [] : ['Parking', 'Security']),
    plot_use: item.plot_use || 'Residential', plot_facing: item.plot_facing || '', road_width_ft: item.road_width_ft ?? '', plot_approval: item.plot_approval || '',
    deposit: item.deposit ?? '', furnishing: item.furnishing || 'Unfurnished', available_from: item.available_from || '',
  }));
  const commercial = commercialTypes.includes(form.kind);
  const change = (name, value) => {
    setError('');
    setForm(previous => ({ ...previous, [name]: value,
      ...(name === 'city' ? { state: cityInfo[value]?.[0] || '' } : {}),
      ...(name === 'kind' ? { beds: commercialTypes.includes(value) ? 0 : 3, baths: commercialTypes.includes(value) ? 0 : 2 } : {}),
    }));
    if (name === 'city') setLocation(null);
  };
  const area = plot ? Math.round(Number(form.area_value) * ({ sqft: 1, sqyd: 9, acre: 43560 }[form.area_unit])) : Number(form.sqft);
  const title = item.id ? 'Edit your listing' : choices.find(choice => choice.mode === mode).title;
  const submit = async e => {
    e.preventDefault(); setError('');
    if (step === 0 && plot && (!area || area > 10000000)) { setError('Enter a plot area between 1 and 10,000,000 square feet.'); return; }
    if (step === 1 && !location) { setError('Please select your property location on the map.'); return; }
    if (step === 2 && !form.images.length) { setError('Add at least one property photo to continue.'); return; }
    if (step < 3) { setStep(step + 1); return; }
    const body = {
      title: form.title.trim(), address: form.address.trim(), city: form.city.trim(), state: form.state.trim(), pincode: form.pincode,
      price: Number(form.price), sqft: area, kind: form.kind, purpose: rental ? 'rent' : 'sale',
      beds: plot || commercial ? 0 : Number(form.beds), baths: plot ? 0 : Number(form.baths),
      lat: location.lat, lng: location.lng, images: form.images, amenities: form.amenities, description: form.description.trim(),
      area_unit: plot ? form.area_unit : 'sqft', area_value: plot ? Number(form.area_value) : null,
      plot_use: plot ? form.plot_use : '', plot_facing: plot ? form.plot_facing : '',
      road_width_ft: plot && form.road_width_ft ? Number(form.road_width_ft) : null, plot_approval: plot ? form.plot_approval.trim() : '',
      deposit: rental ? Number(form.deposit || 0) : 0, furnishing: rental ? form.furnishing : 'Unfurnished',
      available_from: rental && form.available_from ? form.available_from : null,
    };
    setBusy(true);
    try { const result = await api('/properties' + (item.id ? '/' + item.id : ''), { method: item.id ? 'PUT' : 'POST', body: JSON.stringify(body) }); saved(result); }
    catch (e) { setError(e.message); } finally { setBusy(false); }
  };
  const typeLabel = plot ? 'Open plot for sale' : rental ? 'Property for rent' : 'Property for sale';
  return <Modal title={title} close={close} wide><div className="listing-wizard">
    <div className="listing-wizard-intro"><span className="eyebrow">{typeLabel}</span><p>A few simple steps, and your property is ready for its next chapter.</p>{!item.id && step === 0 && <button type="button" className="text-button" onClick={changeType}>Change listing type</button>}</div>
    <ol className="listing-steps" aria-label="Listing steps">{stages.map((label, i) => <li key={label} className={i === step ? 'current' : i < step ? 'complete' : ''} aria-current={i === step ? 'step' : undefined}><span>{i < step ? <Check size={14} /> : i + 1}</span>{label}</li>)}</ol>
    <form className="listing-guided-form stack-form" onSubmit={submit}>
      {step === 0 && <div className="listing-step" key="details"><h3>{plot ? 'Tell us about your plot' : rental ? 'Tell us about your rental' : 'Tell us about your property'}</h3>
        <Field label="Listing title" name="title" form={form} change={change} minLength={5} maxLength={160} required placeholder={plot ? 'Corner plot in a peaceful gated layout' : 'A bright apartment, villa, building or commercial space'} />
        <div className="form-grid">{!plot && <Field label="Property type" name="kind" form={form} change={change} options={propertyTypes} />}
          <Field label={rental ? 'Monthly rent (₹)' : 'Selling price (₹)'} name="price" form={form} change={change} type="number" min="1" max="2000000000" required placeholder={rental ? '25000' : '8500000'} />
          {plot ? <><Field label="Plot area" name="area_value" form={form} change={change} type="number" min=".0001" step="any" max="10000000" required placeholder="200" /><Field label="Area unit" name="area_unit" form={form} change={change} options={[['sqyd', 'Square yards'], ['sqft', 'Square feet'], ['acre', 'Acres']]} /><Field label="Land use" name="plot_use" form={form} change={change} options={['Residential', 'Commercial', 'Agricultural']} /><Field label="Facing (optional)" name="plot_facing" form={form} change={change} options={[['', 'Select facing'], 'North', 'South', 'East', 'West', 'North-East', 'North-West', 'South-East', 'South-West']} /><Field label="Road width in feet (optional)" name="road_width_ft" form={form} change={change} type="number" min="1" max="300" /><Field label="Layout / authority approval (optional)" name="plot_approval" form={form} change={change} maxLength={100} placeholder="e.g. HMDA or DTCP; details supplied by owner" /></> : <><Field label="Built-up area (sqft)" name="sqft" form={form} change={change} type="number" min="1" max="10000000" required placeholder="1600" />{!commercial && <Field label="Bedrooms" name="beds" form={form} change={change} type="number" min="0" max="20" required />}<Field label={commercial ? 'Bathrooms (optional)' : 'Bathrooms'} name="baths" form={form} change={change} type="number" min={commercial ? 0 : 1} max="20" required={!commercial} /></>}
          {rental && <><Field label="Security deposit (₹)" name="deposit" form={form} change={change} type="number" min="0" max="2000000000" placeholder="0" /><Field label="Furnishing" name="furnishing" form={form} change={change} options={['Unfurnished', 'Semi-furnished', 'Furnished']} /><Field label="Available from (optional)" name="available_from" form={form} change={change} type="date" /></>}
        </div>
        <label>What makes this property special?<textarea aria-label="What makes this property special?" name="description" value={form.description} onChange={e => change('description', e.target.value)} minLength={30} maxLength={5000} rows={4} required placeholder={plot ? 'Describe road access, surroundings, boundaries and any layout information.' : 'Describe the property, its surroundings and what buyers or tenants will love.'} /></label>
        <fieldset className="listing-amenities"><legend>{plot ? 'Plot facilities' : 'Amenities'}</legend><div className="amenity-checkboxes">{(plot ? plotAmenities : homeAmenities).map(amenity => <label key={amenity}><input type="checkbox" checked={form.amenities.includes(amenity)} onChange={() => change('amenities', form.amenities.includes(amenity) ? form.amenities.filter(value => value !== amenity) : [...form.amenities, amenity])} />{amenity}</label>)}</div></fieldset>
      </div>}
      {step === 1 && <div className="listing-step" key="location"><h3>Where is your property?</h3><div className="form-grid"><label>City<input name="city" list="listing-cities" value={form.city} onChange={e => change('city', e.target.value)} minLength={2} maxLength={100} required /><datalist id="listing-cities">{Object.keys(cityInfo).map(city => <option key={city} value={city} />)}</datalist></label><Field label="State" name="state" form={form} change={change} minLength={2} maxLength={100} required /></div>
        <Field label="Address" name="address" form={form} change={change} minLength={5} maxLength={250} required placeholder={plot ? 'Plot number, layout, road and locality' : 'Unit, building, road and locality'} />
        <Field label="PIN code" name="pincode" form={form} change={change} pattern="[1-9][0-9]{5}" maxLength={6} required placeholder="500032" />
        <LocationPicker key={form.city} city={form.city} selected={location} onChange={setLocation} />
      </div>}
      {step === 2 && <div className="listing-step" key="photos"><PhotoUpload images={form.images} onChange={images => change('images', images)} onBusy={setUploading} /></div>}
      {step === 3 && <section className="listing-review listing-step" key="review" aria-label="Review your listing"><h3>Looking good. Ready to go live?</h3><div className="listing-review-card"><img src={form.images[0]} alt="Listing cover preview" /><div><span className="eyebrow">{typeLabel}</span><h3>{form.title}</h3><strong>{money(Number(form.price))}{rental && <small>/month</small>}</strong><p>{form.address}, {form.city}, {form.state} {form.pincode}</p><p>{plot ? areaText({ kind: 'Open Plot', area_unit: form.area_unit, area_value: form.area_value, sqft: area }) : Number(form.sqft).toLocaleString('en-IN') + ' sqft · ' + form.kind}{!plot && !commercial && ' · ' + form.beds + ' bedrooms'}</p><p><Check size={15} /> Location selected on map · {form.images.length} {form.images.length === 1 ? 'photo' : 'photos'}</p>{rental && <p>{form.furnishing} · Deposit {money(Number(form.deposit || 0))}{form.available_from && ' · Available ' + form.available_from}</p>}{plot && <p>{form.plot_use}{form.plot_facing && ' · ' + form.plot_facing + ' facing'}{form.road_width_ft && ' · ' + form.road_width_ft + ' ft road'}</p>}</div></div><p className="description">{form.description}</p><p className="fine-print">Check your price, address and photos. You can edit or archive the listing later from Your listings.</p></section>}
      {error && <p className="form-error" role="alert">{error}</p>}
      <div className="listing-wizard-actions"><button type="button" className="outline" disabled={busy || uploading} onClick={() => { setError(''); step ? setStep(step - 1) : close(); }}><ChevronLeft size={17} />{step ? 'Back' : 'Cancel'}</button><button className="primary" disabled={busy || uploading}>{busy ? <LoaderCircle className="spin" size={18} /> : step === 3 ? <Check size={18} /> : <ArrowRight size={18} />}{busy ? 'Saving your listing…' : step === 3 ? item.id ? 'Save changes' : 'Publish listing' : 'Next: ' + stages[step + 1].toLowerCase()}</button></div>
    </form>
  </div></Modal>;
}

function PropertySaleForm(props) { return <ListingWizard {...props} mode="sale" />; }
function PlotSaleForm(props) { return <ListingWizard {...props} mode="plot" />; }
function RentalForm(props) { return <ListingWizard {...props} mode="rent" />; }

export default function ListingFlow({ item, close, saved, Modal }) {
  const [mode, setMode] = useState(item.id ? item.kind === 'Open Plot' ? 'plot' : item.purpose === 'rent' ? 'rent' : 'sale' : '');
  const props = { item, close, saved, Modal, changeType: () => setMode('') };
  if (mode === 'plot') return <PlotSaleForm {...props} />;
  if (mode === 'rent') return <RentalForm {...props} />;
  if (mode === 'sale') return <PropertySaleForm {...props} />;
  return <Modal title="Add a listing" close={close} wide><div className="listing-type-selection"><span className="eyebrow">Start your next chapter</span><h2>What would you like to list?</h2><p>Choose an option. We'll guide you through the rest.</p><div className="listing-type-cards">{choices.map(({ mode, title, text, icon: Icon }) => <button className="listing-type-card" key={mode} aria-label={title} onClick={() => setMode(mode)}><span className="listing-type-icon"><Icon size={30} /></span><strong>{title}</strong><span>{text}</span><span className="listing-type-arrow">Get started <ArrowRight size={16} /></span></button>)}</div></div></Modal>;
}
