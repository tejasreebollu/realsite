# RealSite feature scope

Updated: 10 October 2026.

RealSite is a real estate portal for **India** using React, FastAPI, PostgreSQL, Azure, Redis, and local Docker. The supplied screenshots are visual references, not application specifications or instructions to scrape third-party data.

## Implemented first version

| Experience | Current implementation |
| --- | --- |
| Homepage | Header, left rail, photographic hero, search, card carousels, service cards, city links |
| Buy/rent results | Split map/list, sale/rental variants, INR price cards, photo paging, favourites |
| Search | City/address/PIN search, suggestions, filters including plus-count room choices and exact-match checkboxes, India More Filters, multi-amenity/area/status/source/tour criteria, sorting, pagination, viewport, drawn-polygon and nearby-distance filtering |
| Map Options | Automatic map, satellite imagery, external Street View access; climate-risk selectors with an explicit unavailable-data status |
| Property details | Gallery, facts, amenities, location, enquiry form, share link |
| Accounts | Single public-account registration, login, logout, expiring private sessions, provisioned admin role |
| Personal workspace | Favourites, saved searches, recent views, enquiry inbox |
| Sellers/owners | Separate property sale, plot sale and rental forms, optional India search attributes, map picker, photo uploads, edit/archive and enquiries |
| Administration | Inventory metrics, city/status filters, paginated listings/accounts/enquiries, archive and restore; admin-only API and UI |
| Client demo | 100 synthetic properties across five cities, generic user and admin logins, saved homes/searches/enquiries and JSON snapshot |
| Finance | Adjustable home loan EMI calculator, INR price histogram/slider and estimated monthly-payment filtering with demo financing assumptions |
| Agents | Fictional sample agent cards with filtered sample listings |
| Platform | Four-service Docker stack, readiness, Redis caching/rate limits, Azure evaluation deployment |

The approved identity uses live **RealSite.in** text in Inter 900, a smaller .in suffix and a blue SVG map pin containing a white house. It is shared across the header, sign-in, footer and synthetic tour, with responsive sizing and a light shadow.

The implementation retains the reference's blue/white palette and key desktop layouts. Indian addresses, INR amounts, RealSite branding, illustrative photography, and OpenStreetMap replace the US content and proprietary reference integrations. Full feature parity with the reference platform remains separate work.

## Work required for a full product

| Area | Remaining work / required input |
| --- | --- |
| Real inventory | Licensed Indian listing feeds or authorised owner/broker uploads; deduplication and refresh jobs |
| Trust | Owner/agent identity checks, listing review, independent verification of supplied RERA/approval details, reporting and moderation |
| Photos | Managed Azure Blob storage/CDN, malware scanning, quotas and orphan cleanup; local uploads, ownership checks and resizing are implemented |
| Maps | Address geocoding, official city boundaries, multiple drawn regions/holes, clustered pins, neighbourhood data, contracted tile service |
| Communication | Two-way messaging, email/SMS/WhatsApp delivery, consent/preferences, notification jobs |
| Accounts | Email verification, password reset, optional MFA, social login, account export/deletion |
| Rentals | Applications, documents, background-check provider, lease workflow, rent/payment integrations |
| Finance | Lender-approved rates/eligibility, applications, comparisons, qualified affordability advice |
| Valuation | Licensed transaction/comparable data and a separately validated Indian valuation model |
| Agent marketplace | Real onboarding, verified profiles, service areas, reviews, contact routing |
| Advertising | Promoted inventory, campaign controls, billing, analytics |
| Administration | Moderation reasons/review queues, account lifecycle controls, immutable audit log, operational metrics |
| Operations | Managed PostgreSQL/Redis, secret store, migrations, backups with restore drills, monitoring, CI/CD, load tests, recovery procedures |
| Discovery | SEO routes, server-rendered metadata, sitemaps, accessibility audit and automated performance budgets |

The next release should prioritise real inventory, verified owner onboarding, managed photo storage and moderation. Actual inventory providers and account verification methods must be selected before those integrations can be completed. Proprietary third-party algorithms and data are not included.

Drawn-area search supports one simple map polygon, pen-first mouse/touch drawing, draggable corner refinement, keyboard input, preview and Apply/Cancel, Edit area, Redraw and boundary removal. A compact 24px pen cursor marks the nib while drawing; a hand indicates map movement or corner editing. Small closing overlaps are trimmed conservatively. Server counts, pagination, map results and price histograms share the area predicate. URLs and saved searches preserve the boundary and original city; removal restores that city with other filters intact. Concave shapes and boundary points are supported; multiple regions and polygon holes are not currently supported.
