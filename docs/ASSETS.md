# Assets and visual references

Updated: 11 October 2026.

## Homepage and dashboard presentation

The approved homepage headline is **Find your space. Build your future.**, rendered as live white text with a line break between the sentences. It keeps the existing bold Inter treatment, hero photograph, subtitle and search control. This release adds no new photograph or bitmap wordmark.

Admin charts use native SVG and CSS in `frontend/src/analytics.jsx` and `analytics.css`, without a chart-library dependency. The activity plot measures its container width to keep labels and grouped bars legible. See [analytics](ADMIN-ANALYTICS.md) and [current verification](VERIFICATION.md) for the compact layout and deployed assets.

The five screenshots supplied on 8 October 2026 are layout references for the homepage and sale/rental split map/list views. RealSite uses its own portal identity with these layouts.

The current logo uses live HTML text reading **RealSite.in** (with the .in suffix at 80% of the main lettering size), in the same Inter family as the homepage headline, with weight 900, a blue gradient, 0.15px letter spacing and a light shadow. Lettering is upright and uses the user's requested mixed case. It is rendered by the browser rather than downscaled from a generated bitmap. Inter weights 400-900 are requested through the existing Google Fonts stylesheet; Arial remains the fallback.

A compact blue SVG map pin with a small white house precedes the text. Its shape and vertical gradient mirror across the centre line. It is editable in `frontend/public/realsite-emblem.svg`; the favicon uses the same symbol. Header, sign-in, footer and illustrative 3D model share the live-text identity, with smaller text on phones and no subtitle.

Earlier generated wordmark PNG drafts are archived locally under ignored `artifacts/branding-designs/`. They are excluded from the released frontend and Git commit. The superseded `realsite-logo.svg` is removed; active lettering is live text. Service illustrations remain original SVG code. No proprietary valuation, listing feed or map dataset has been downloaded.

Illustrative sample photos are fetched from `images.unsplash.com` by `scripts/prepare_local.py`. They are not verified Indian property photographs or pictures of the seeded addresses. The local source mapping is:

| Local file | Unsplash image ID |
| --- | --- |
| home-1.jpg | photo-1600596542815-ffad4c1539a9 |
| home-2.jpg | photo-1600585154340-be6161a56a0c |
| home-3.jpg | photo-1600047509807-ba8f99d2cdde |
| home-4.jpg | photo-1600566753086-00f18fb6b3ea |
| home-5.jpg | photo-1600607687939-ce8a6c25118c |
| home-6.jpg | photo-1600607687920-4e2a09cf159d |
| home-7.jpg | photo-1600047509782-20d39509f26d |
| home-8.jpg | photo-1600585154526-990dced4db0d |
| home-9.jpg | photo-1570129477492-45c003edd2be |
| home-10.jpg | photo-1564013799919-ab600027ffc6 |
| home-11.jpg | photo-1512917774080-9991f1c4c750 |
| home-12.jpg | photo-1600566753190-17f0baa2a6c3 |
| hero.jpg | photo-1600585154340-be6161a56a0c |
| interior.jpg | photo-1600210492486-724fe5c67fb0 |

Example source: https://images.unsplash.com/photo-1600596542815-ffad4c1539a9. Replace sample images with authorised property photographs for a real inventory.

Map tiles: © OpenStreetMap contributors, https://www.openstreetmap.org/copyright. Default tile endpoint: https://tile.openstreetmap.org. The [tile usage policy](https://operations.osmfoundation.org/policies/tiles/) applies; public-scale usage needs an appropriate provider. Inter is loaded from Google Fonts with an Arial fallback. Icons use Lucide.

The Satellite option loads Esri World Imagery from `https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}` and displays Esri/source credits on the map. Street View links open Google Maps at the current map centre. No Google imagery is copied into the portal, and no climate-risk imagery is included. See [map options](MAP-OPTIONS.md).

## Drawing and tour assets

`frontend/public/cursors/pen.svg` is an original compact 24x24 vector cursor with a 1.25px outline. The drawing hotspot is its nib at (3,21); CSS uses a versioned asset URL so the compact revision replaces cached cursor imagery. Move map and corner editing use the native hand cursor. No cursor image service is required.

`frontend/public/tours/demo-3d.html` is an original interactive canvas sample with rotate, look-inside and reset controls, plus keyboard navigation. It is labelled synthetic and is not a scan or measured tour of any listed address. It reuses the illustrative interior photo above. Owner-supplied HTTPS tour links are separate content.

## Map highlights and profile photos

Property price pins are rendered as Leaflet div icons. `frontend/src/styles.css` keeps the existing 1px border and changes it to cyan (`#22d3ee`) with a soft layered glow on the hovered property's pin. The effect clears on mouse leave. `map-draw.css` keeps pins visible during drawing and disables their pointer events; corner handles remain interactive.

Profile photos reuse the owner-scoped JPEG/PNG/WebP upload pipeline and persistent image volume described in [listing forms](LISTING-FORMS.md). Uploaded photo URLs are publicly served assets, while account email and private profile fields are excluded from the public agent directory. See [user management](USER-MANAGEMENT.md) for profile visibility and consent.
