# Verification record · release 13 October 2026

## Azure PostgreSQL bootstrap — 13 October 2026

Created `data/azure-postgres-bootstrap.sql`, a standalone PostgreSQL schema-and-data file generated from the tracked 100-property synthetic export. It defines all ten application tables and inserts the 100 fictional listings with stable seed keys; it contains no accounts, password hashes, sessions, enquiries, saved searches, uploads or private local data. It is designed for a new/dedicated Azure demo database and uses `ON CONFLICT DO NOTHING` for repeated execution.

An isolated PostgreSQL 16 check loaded the file twice. Both loads succeeded, leaving exactly 100 synthetic listings. Sale minima/maxima were verified as Hyderabad ₹2–10 crore, Mumbai ₹5–20 crore, Pune ₹3–12 crore, and Bengaluru/New Delhi ₹3–15 crore. The generated file reports ten table definitions and 100 stable property rows. PowerShell parsing of `infra/deploy.ps1`, Azure Compose syntax with a placeholder domain, Markdown links and whitespace checks passed. No Azure resource, managed database or cloud email service was created or contacted.

`infra/deploy.ps1` now packages the bootstrap file, disables startup demo seeding and imports the file after the Azure VM database starts. This is source/configuration validation only; an Azure deployment and Azure Database for PostgreSQL runtime remain unverified.

## Requested sale ranges — 12 October 2026

Applied the user-selected synthetic sale ranges: Hyderabad ₹2–10 crore, Mumbai ₹5–20 crore, Pune ₹3–12 crore and Bengaluru/New Delhi ₹3–15 crore. Each city's 12 sale homes spans both endpoints. All 60 eligible sale homes changed; all 40 synthetic rentals retain their exact stored amounts. Fresh seeding uses the same model; normal startup preserves existing edits. Repricing recognises original/prior-model prices and matching core facts, excludes rentals/manual/customised rows, adjusts existing previous prices and invalidates listing caches.

A PostgreSQL backup and business-data fingerprints preceded application. All 142 properties retain identical non-price fields; all other business tables and the 82 unplanned property price pairs are unchanged. The 100-property export matches live inventory. A repeat preview finds zero changes. The API-only build and deployment are healthy; PostgreSQL/Redis/photo volumes were retained and frontend assets did not change.

The isolated backend run passed 171 cases with one failure caused by the search test's old ₹2 crore budget. After adapting that fixture to ₹6 crore, its targeted rerun passed: all 172 cases are validated across the two runs, including six new range/upgrade cases. Four focused public-pricing browser checks passed with no JavaScript errors. Earlier homepage/admin/hover browser reports are prior evidence. Documentation links and Git whitespace were checked.

Evidence is ignored under `artifacts/city-ranges-*-2026-10-12.json`, `before-city-ranges-2026-10-12.sql` and `city-ranges-public-results-2026-10-12.json`. These ranges are synthetic presentation assumptions, not verified market valuations. This pricing update is prepared for publication on main; Git history identifies the published revision. Private backups and local evidence remain excluded.

## Final documentation and homepage release — 11 October 2026

All **16 Markdown documents** are synchronised, including handoff, setup/Azure, architecture, scope, demo, account, listing, map and filter guides. No maintained Word editions exist. The homepage displays **Find your space. Build your future.**; the compact admin dashboard retains four KPIs, nine charts, sticky management tabs, toolbar actions, light hover feedback and the full-width third-row activity plot. The period menu remains 30/90/365 days.

The final combined browser workflow passed **17 checks** (three homepage and 14 admin checks), with no JavaScript errors. It covers exact headline/search, responsive hero bounds, all chart/control/export workflows, API-proportional bars, available-width sizing, management navigation, error recovery and empty data. It creates an authentication session without inserting business records. Current local assets: `index-C3ZRAcB0.css` / `index-OwmaSPV4.js`.

The **166 isolated backend cases**, four public-pricing checks and three hover checks below are implementation evidence for this release, not fresh runs for documentation-only edits. Backend source was unchanged during final release preparation. Readiness, local/Azure Compose syntax, all documentation links, the 100-property public snapshot and Git whitespace are checked before publication. Azure runtime and SMTP delivery remain unverified.

Final browser reports/screenshots remain under ignored `artifacts/analytics-*` and `hero-headline-*`. The final release check report is `artifacts/release-2026-10-11-analytics.json`. Backups, credentials, uploads and local tools are excluded from Git. Earlier entries below record intermediate releases and their then-current assets/test counts.

## Full-width activity row — 11 October 2026

Listing & enquiry activity now occupies a full-width third chart row after the inventory/account chart rows. Its compact 180px SVG plot measures the available width; bars remain distinct and text proportions stay unchanged. All nine charts remain. The existing 30/90/365-day menu uses daily/7-day/30-day totals respectively, with a shorter final group when needed; no 120-day option was added.

The frontend build/deployment and **14 analytics browser checks** passed, including full-width placement, plot resizing, proportional heights, time-bucket counts, keyboard/hover details and desktop/mobile layouts down to 320px. No JavaScript errors occurred. Assets: `index-C3ZRAcB0.css` / `index-DiqGdVjZ.js`. Backend code/data are unchanged; the earlier 166 backend cases are prior evidence. Refreshed screenshots/results are ignored under `artifacts/analytics-*`.

## Grouped activity bars and Indian demo prices — 11 October 2026

Converted Listing & enquiry activity to grouped blue/teal bars, retaining the reporting windows, real event counts and keyboard/hover readout. Account growth remains a line. The 100 synthetic homes now use direct INR assumptions by city, locality, floor area and property type. These are illustrative scenarios, not verified market valuations; [the demo guide](DEMO.md#indian-demo-pricing) records the formula, ranges and references.

Built and deployed API/web; readiness passed. Current assets: `index-CNkMfFb6.css` / `index-C4Ef93ox.js`. **166 isolated backend cases**, **13 analytics browser checks** and **four public-pricing checks** passed. The bar check compares actual SVG heights/counts with API data; the public checks cover every city/purpose, price sorting and bounds, Hyderabad cards/map prices and synthetic city medians. Desktop/mobile layouts down to 320px remain valid. No JavaScript errors occurred; one existing backend deprecation warning remains.

A PostgreSQL backup preceded the update. **98 synthetic price pairs changed; two already matched.** All **142 properties** have identical non-price fingerprints; the other 44 rows have unchanged prices. The eight other business tables are unchanged: 27 users, 40 account audit entries, three agent profiles, zero email changes, 10 saved searches, 26 uploaded images, eight favourites and nine enquiries. Authentication sessions are excluded from business-table comparisons. Manually entered/customised properties and archived surplus seed rows retain their amounts. The 100-home export has 12 sale/eight rental homes per city and matches live prices. A repeat preview finds zero changes.

Evidence stays local and ignored: `artifacts/before-india-pricing.sql`, `india-pricing-before.json`, `india-pricing-after.json`, `india-pricing-preview.json`, `india-pricing-applied.json`, `india-pricing-results.json`, `india-pricing-public-results.json`, sale/rent screenshots and refreshed `analytics-*` reports/screenshots. Backups are private and excluded from Git. Earlier entries below describe historical releases and their test scope.

## Dashboard card hover — 11 October 2026

The frontend-only update adds light card shadows, a thin blue hover border and a 2px KPI lift. Three focused browser checks passed: hover/reset without layout shift, stationary chart cards with border/shadow feedback, and reduced-motion suppression of the lift. A 390px width check found no page overflow; no JavaScript errors occurred. Backend tests and the full analytics workflow were not rerun for this CSS refinement.

The rebuilt frontend is healthy locally with `index-CNkMfFb6.css` / `index-P1oxzBnq.js`. Evidence is ignored under `artifacts/analytics-hover-results.json` and `analytics-kpi-hover.png`.

## Compact admin layout — 11 October 2026

The requested introductions and context banners were removed; refresh/export now share the filter toolbar. KPI height, panel padding and row gaps were reduced. Tabs now precede all section content and stay visible during scrolling, including Listings and Enquiries. All reporting controls and nine charts remain available.

The frontend build passed and is deployed as `index-CquUJYQi.css` / `index-Ba2WwjKn.js`. **12 browser checks passed**, with no JavaScript errors, covering all requested layout changes, sticky navigation across management tabs, chart controls, export, failure/retry, empty data and 1280/768/390/320px layouts. Screenshots/results were refreshed under ignored `artifacts/analytics-*`. The 162 backend cases below remain prior evidence; no backend code changed or backend suite rerun for this layout refinement.

## Admin analytics — 11 October 2026

The new default admin view provides nine charts, four KPIs, 30/90/365-day controls, all/owner/synthetic listing datasets, planning signals and city CSV export. It reads existing records through an administrator-only, private no-store endpoint. No migration, new dependency or fabricated history was added. See [analytics](ADMIN-ANALYTICS.md).

The full isolated backend suite passed **162 cases**, including 13 analytics cases; one existing Starlette/AnyIO deprecation warning remains. **11 analytics browser checks passed** with no JavaScript errors, including date/dataset totals, chart hover/focus, separate pricing modes, CSV export/formula escaping, management tabs, 1280/768/390/320px layouts, empty data and failure/retry. Prior account/drawing release evidence below remains historical; those browser workflows were not rerun for analytics.

Initial analytics build assets: `index-DohR1kCX.css` / `index-k7frlfsm.js`. API and web are healthy; PostgreSQL/Redis and image/data volumes were retained. Endpoint scope, metric formulas and load-testing limitations are documented. Evidence: ignored `artifacts/analytics-browser-results.json`, `analytics-desktop.png`, `analytics-mobile-viewport.png` and `analytics-city-report.csv`.

## Previous account and cyan highlight release

Updated: 11 October 2026.

The release combines self-service profiles, protected account settings, reviewed agent profiles and audited administration with visible pins during drawing and the accepted cyan hover treatment. All 15 Markdown documents have been reviewed and synchronised, including [handoff](HANDOFF.md), [user management](USER-MANAGEMENT.md), setup, demo, scope and feature guides. There are no maintained Word editions in this repository.

Release preparation validated all 15 Markdown documents and 83 local links, the public snapshot of 100 synthetic properties, the deployed account routes, readiness, local/Azure Compose syntax and Git diff whitespace. Final checks are recorded in ignored `artifacts/release-2026-10-11.json`. The remote branch was fetched before publication; use an ordinary push and confirm the working tree and `HEAD...origin/main` after it.

That release's web build was deployed locally as `index-CUesXYZG.css` / `index-aQK23O7b.js`. Two focused read-only Chrome checks confirmed that hovering sale and rental result cards highlights exactly the matching marker, keeps its border at 1px, uses cyan `#22d3ee` with a soft glow, and clears the highlight on mouse leave. No JavaScript errors occurred. Evidence is local in ignored `artifacts/cyan-hover-results.json` and `cyan-hover-sale.png` / `cyan-hover-rent.png`.

The account and drawing evidence below was collected during this implementation. The later hover change only modifies frontend CSS; the 149 backend cases and 11 account checks were not rerun for it. Fourteen drawing checks and the two hover checks are the subsequent focused validation. PostgreSQL, Redis, existing volumes and customer data were preserved. Real SMTP delivery and Azure runtime remain unverified.

## Drawing marker visibility - 11 October 2026

The drawing-mode CSS previously hid property price markers. They now remain visible throughout Pen, Move map, the live stroke, preview and Redraw. Pointer events are disabled on property markers during drawing so tracing across a pin does not open its popup. Applying updates the area search; cancelling retains the existing filters and restores marker interaction.

The frontend-only rebuild is deployed locally with `index-BDTiLFSx.css` / `index-CRBWwJse.js`. The expanded read-only drawing browser workflow passed **14 checks**, including filtered sale/rental markers, geometry/counts/histogram, mouse/finger input, phone layouts, Apply/Cancel, refresh and original-city restoration. No JavaScript page errors were recorded. Evidence: ignored `artifacts/pen-draw-results.json` and `draw-visible-markers-sale.png` / `draw-visible-markers-rent.png`. The account update's 149 backend cases below remain prior evidence; backend code and data were unchanged by this CSS fix.

## User management - 11 October 2026

Profile editing, account settings, reviewed agent profiles and audited account administration are implemented and deployed locally. Documentation includes [user management](USER-MANAGEMENT.md), SMTP/local-demo configuration, [handoff](HANDOFF.md) and [testing](TESTING.md). These source changes, tests and documentation form the current release. Use Git history for the published revision; local screenshots, tooling, backups and customer uploads are excluded from the commit.

| Check | Outcome |
| --- | --- |
| Complete isolated backend suite | 149 passed; one existing Starlette/AnyIO deprecation warning |
| Account browser workflow | 11 checks passed; no JavaScript page errors |
| Responsive profile/admin screens | No page overflow at 320px and 390px; admin tabs wrap |
| API/web production builds | Passed; deployed `index-B5yxdYDY.css`, `index-BxSJxX7n.js` |
| Local readiness | PostgreSQL and Redis connected |
| Original business records | All original fields preserved: 23 accounts, 139 properties, 21 upload records, 8 favourites, 10 saved searches, 9 enquiries |
| Original uploaded images | All 21 served photos match their pre-upgrade bytes |
| Documentation | 15 Markdown files / 73 local links validated; diff whitespace check passed |

The live browser check covers the login gate, registration, profile/photo persistence, password session revocation, labelled local email verification, agent application/approval/resubmission, owner-ID listing searches, suspension/reactivation, admin edit reasons and account activity. Test accounts are suspended, agent profiles rejected and their three test listings archived. Their records and audit history remain as additional data. Existing demo/customer records and volumes are preserved.

Backups and evidence are excluded from Git under `artifacts/`: `before-user-management.sql`, `before-user-management-uploads/`, `accounts-original-records.json`, `account-data-preservation.json`, `account-management-results.json` and account screenshots. The original-record snapshot contains private database values and must stay local. Backend fixtures use an explicit isolated SQLite database and never reset live PostgreSQL.

SMTP TLS transport and absence of verification codes in SMTP responses are covered with a mocked provider. No external email was sent; real provider delivery, Azure runtime, registration verification, password reset, MFA, independent agent credential verification and production certification remain outside these checks. All following release sections describe earlier validation, not this local feature release.

## Previous release - 10 October 2026

All maintained Markdown documents have been synchronised with the latest implementation. [Project handoff](HANDOFF.md) and [testing guide](TESTING.md) cover source navigation, local setup/update, demo accounts, backups, validation and remaining integrations. The reference-to-India scope identifies polygon search as implemented and reserves multiple regions/holes for future work. The 10 October update records the final approved RealSite.in identity; earlier backend/search results below belong to the preceding release.

| Current check | Outcome |
| --- | --- |
| Complete isolated backend suite | 131 passed; one existing Starlette/AnyIO deprecation warning |
| Pure Node drawing/location scripts | 2 passed |
| Pen drawing browser workflow | 12 checks passed |
| Price/EMI browser workflow | 12 checks passed |
| India More Filters/listing metadata/3D model | 14 checks passed |
| Compact pen cursor | 24x24 SVG decoded; nib hotspot (3,21), held drawing, Move map, preview and Redraw verified |
| Local readiness | PostgreSQL and Redis connected |
| Final brand identity | Live RealSite.in text, Inter 900, blue house/map-pin SVG, light shadow; .in at 80% with baseline alignment |
| Production frontend | Built and deployed; latest branding assets `index-BUXfXVy9.css`, `index-DejVZU8F.js` |

The latest browser drawing checks include Hyderabad and the other four demo cities, all-India searches, price/room retention, refresh, redraw, boundary removal, Back/Forward and phone touch input. A 24px thin pen cursor remains visible during drawing; Move map and finished-area editing use a hand. Local demo volumes were retained. Browser filter checks create their own accounts and archive their own temporary listings; these history rows can increase total record counts. Existing customer/demo listing edits are preserved.

Evidence remains local under ignored `artifacts/`: `pen-draw-results.json`, `price-filter-results.json`, `more-filters-results.json`, `pen-cursor-check.json` and `release-checks.json`. Public demo JSON contains only the 100 synthetic listings. Secrets, uploaded customer photographs, backups and screenshots are excluded from Git.

Earlier sections below are historical validation records. Their account roles, inventory totals and asset hashes describe that earlier stage, rather than the current release. The latest tests do not establish Azure runtime, live inventory accuracy, lender eligibility or production certification. No Azure resources were provisioned.

## Historical validation records


## Local stack

The React production build completed successfully in Docker. The FastAPI, nginx, PostgreSQL, and Redis services started. `/api/health` returned `status: ok`, with PostgreSQL and Redis connected. The homepage returned HTTP 200.

The application is bound to **127.0.0.1:8090**. Other existing Docker applications were left running and their ports were not changed.

## Backend regression suite

**10 passed.** The suite checks:

- Indian sale/rental search, budgets, bedroom filters, ordering, pagination, amenities, agents, and viewport bounds.
- Session creation/revocation, incorrect passwords, duplicate emails, password length.
- Private, idempotent favourites and account-owned saved searches.
- Owner-only listing updates/archival and search cache invalidation.
- Sender/owner-only enquiry visibility.
- PIN codes, image URL schemes, phone validation, and cross-origin write rejection.

The suite runs against isolated SQLite storage and a Redis adapter, not against the live user's database. A Starlette/AnyIO deprecation warning was emitted; the tests passed.

## Real browser flows

**19 checks passed** with installed Chrome using Playwright against the running PostgreSQL/Redis application:

- Homepage images and three listing carousels.
- Actual sale results and geographic markers.
- Bedroom filter results and reset.
- Registration, session creation, and deferred favourite action.
- Saved search persistence and restoration.
- Enquiry submission and inbox display.
- Favourite persistence across pages.
- Owner listing publication, editing, and archival.
- Expected EMI result for the illustrative default assumptions.
- Rental results and marker variant.
- Sign-out.
- Homepage/search layouts at desktop, 390px mobile, and 768px tablet widths.
- Mobile map/list switching.
- No browser JavaScript errors.

Visual inspection found a vertically stacked sort label and clipped phone/tablet filter controls. These were corrected, along with adding property type to the mobile-accessible Filters menu and an explicit accessible label for its selector.

**5 final layout checks passed** against the final frontend build: complete visible filter controls, no horizontal overflow, horizontal sort controls, and working property-type filtering at 1920px, 768px, 390px, and 360px; plus direct property-link opening/closing. Results are recorded in `artifacts/layout-results.json`. Final screenshots include `homepage-preview.png` and `final-search-*.png`. No browser JavaScript errors were reported during these checks. All four application containers were healthy at handover.

Browser checks leave one test account, a saved search, a demo enquiry, and an archived owner test listing in the local database. The 120 original demonstration listings remain available. No real agent messages, email, or SMS were sent.

## Dependencies and Azure

- Frontend dependency audit: **0 reported vulnerabilities** after updating Vite to 6.4.4. This statement applies to the npm audit result, not a complete infrastructure security audit.
- Azure Bicep template compiled to `artifacts/main.json`: 5 infrastructure resources.
- Azure Compose overlay passed configuration validation.
- Azure PowerShell deployment script passed syntax parsing.
- No Azure resources were provisioned. DNS, certificates, SSH, cloud-init, and cloud runtime have not been tested in Azure.

## Map Options update · 8 October 2026

Added the reference's bottom-right Map button, Map Options popover, Automatic/Satellite/Street view radios, and the six Climate Risk choices. Satellite tiles loaded successfully with HTTP 200 responses and the listing markers remained visible. Street view links target the current map centre in Google Maps. Risk selections explicitly report unavailable data and do not draw unverified overlays.

**8 focused browser checks passed** with no JavaScript errors. The checks cover defaults and focus, circular radio dimensions, actual satellite imagery/attribution, all climate choices/reset, Street View links, Escape/outside-click dismissal, automatic-map restoration, menu placement at 768px/390px/360px, and non-overlapping mobile controls. The 360px case uses a short 640px viewport to verify the menu remains usable by scrolling. Screenshots and results are in `artifacts/map-options-*.png` and `artifacts/map-options-results.json`. The frontend was rebuilt and its web container updated; backend and data services were left running.

## Client demo data and account roles · 8 October 2026

Prepared **100 active synthetic properties**: 20 per city across Hyderabad, Bengaluru, Mumbai, Pune and New Delhi; 12 for sale and 8 for rent per city. All 100 belong to the demo seller. The old seed's 20 surplus sale listings were archived without deleting existing references. Existing accounts and manually created properties were retained. The buyer starts with five saved homes, five saved searches and five enquiries routed to the demo seller. Public inventory was exported to `data/demo-properties.json`; its count and city/purpose distribution were checked.

**16 backend checks passed**, covering the existing portal workflows plus exact demo counts, buyer/seller/admin roles, admin access and moderation, disabled demo logins/sessions, idempotent seeding, preservation of edits/workspace choices/manual inventory, legacy sample-data adoption, and repeatable additive schema migration. The isolated suite reported one dependency deprecation warning; no failures.

**19 existing browser workflow checks passed** against the new roles and 12-sale/8-rent city distribution. **12 focused demo browser checks passed** against the final frontend, including all three logins, buyer favourites/searches/enquiries, seller ownership/edit forms/received enquiries, admin metrics, city filtering/pagination, archive/restore confirmation and public-search visibility, accounts/enquiry review, and tablet/mobile layouts at 768px, 390px and 360px. No JavaScript errors were reported by either successful browser run. Testing identified and corrected an admin section-switching data mismatch and improved accessible names for admin filter controls.

Screenshots are `artifacts/demo-buyer.png`, `demo-seller.png`, `demo-admin.png` and `demo-admin-{width}.png`; the focused results are `artifacts/demo-results.json`. Admin moderation checks restore the property before completing. Existing regression checks leave additional test accounts/enquiries and an archived test property; these are separate from the 100 active synthetic homes. Demo browser checks assume the prepared buyer workspace and inventory have not subsequently been changed during presentations.

Known demo accounts are enabled in local Compose and disabled by the Azure overlay. No cloud deployment was performed. Credentials and presentation steps are documented in [client demo](DEMO.md).

## RealSite branding · 8 October 2026

Updated the UI wordmark, R house monogram, favicon, browser metadata, API title, package identifiers, Compose project, Azure defaults and documentation. Identifier names use `realsite`; display branding uses `RealSite`. The repository directory is `realsite-repo`. No previous-brand text remains in project-owned source, configuration, documentation or filenames.

Built and started `realsite-india` containers using newly named PostgreSQL/Redis volumes copied after stopping the original stack. All six database table counts and full-row fingerprints matched before and after migration; evidence is in `artifacts/brand-data-check.json`. The pre-migration volumes were retained as rollback copies. Demo credentials are unchanged and 100 synthetic properties remain active.

**5 layout checks and 12 demo browser checks passed** after rebranding, including desktop/tablet/mobile layout, all three demo logins and admin moderation/restoration. No JavaScript errors were reported. Confirmed the live browser title and OpenAPI title display RealSite. Refreshed homepage, search and demo-account screenshots are under `artifacts/`.

## New RealSite logo and header · 8 October 2026

Created a standalone vector logo using a house inside a blue location pin with a teal accent and matching favicon. The shared logo component updates the header, sign-in form and footer; the subtitle is removed. The header places the logo first on the left, with 48px before desktop navigation (32px on narrower desktop screens). Tablet/phone navigation uses a menu containing all five primary links.

The frontend build succeeded and **5 existing layout checks passed**. Visual review covered guest and admin headers at 1920, 1440, 1280, 1101, 1100, 1024, 768, 390 and 360 pixels. There was no page overflow or logo subtitle in any view. Both mobile menus opened and Rent navigated to the eight rental results. No JavaScript errors were reported. Screenshots are `artifacts/new-logo-*.png` and observations are `artifacts/new-logo-layout.json`. The web container was rebuilt and updated.

## Evidence files

Ignored `artifacts/` contains browser results and screenshots. Reproduce with the commands in [README](../README.md). Browser checks verify workflow behaviour and layout; they do not establish pixel-perfect RealSite parity, live inventory accuracy, production performance, or a full accessibility audit.

## Unified public account - 9 October 2026

Public registration now creates a single user account for buying, renting and selling. The account-type selector and buyer-only listing restriction were removed. Ownership checks and administrator permissions remain enforced.

The local database upgrade renamed demo seller ID 3 to **demouser** (`demouser@demo.example.com` / `DemoUser@2026`) and merged demo buyer ID 2 into it before removing that row. Old buyer/seller logins no longer authenticate, and their existing sessions were revoked. Admin credentials and unrelated customer accounts were preserved.

Before and immediately after migration, the database retained 122 property rows (100 active synthetic homes, 20 legacy archives and two archived browser-test listings), nine favourites, seven saved searches and seven enquiries. All property fields had an identical fingerprint; enquiry and saved-search contents also matched after excluding their deliberately transferred sender/account IDs. The generic account retained seven favourites and five saved searches. A database backup is in ignored `artifacts/realsite-before-generic-account-2026-10-09.dump`.

**19 backend tests passed** in disposable SQLite storage, including legacy-account consolidation, overlapping favourites, ownership transfer, unchanged edits/archives, old-session revocation, retained administrator sessions, repeatable role conversion, password preservation and protection of non-demo accounts.

**12 demo browser checks passed** against the live PostgreSQL/Redis app: obsolete logins rejected, generic registration, combined saved workspace and 100 managed listings, denied user administration, admin login/moderation/account review, and responsive admin views.

A registration race that could overwrite a pending favourite save was fixed by loading existing favourites before executing the deferred action. **19 public browser checks passed**, including registration without an account-type selector and buying/selling actions with the same regular account. No JavaScript errors were reported. Evidence is in `artifacts/demo-results.json`, `artifacts/browser-results.json` and `artifacts/generic-account-migration.json`. Browser checks add test accounts and saved activity after the migration snapshot; the successful public flow also adds an archived test listing.

## Listing forms, photos and open plots - 9 October 2026

Added separate **Sell a property**, **Sell an open plot** and **Rent a property** forms. Sale and rental forms support apartments, villas, houses, buildings, commercial buildings, offices and shops. Commercial forms omit bedrooms and make bathrooms optional. Plots use land-specific fields and square feet, square yards or acres. Rental forms capture monthly rent, deposit, furnishing and availability.

All forms follow **Details > Location > Photos > Review**, retain entries when going back, and reopen existing photos and locations when editing. Location is selected through a map pin with click, drag, map-centre, device-location and keyboard controls. Photos support multiple file selection or drag/drop, previews, progress, removal and cover selection. Authenticated uploads validate actual JPEG/PNG/WebP content and ownership, limit size, apply camera orientation, strip metadata and resize. Files persist in the new `property_images` Docker volume; PostgreSQL stores ownership metadata. Existing database and Redis volumes are preserved.

**41 backend tests passed** in isolated disposable storage, including upload validation and ownership, all residential/commercial types for sale and rent, plot unit conversion and business validation. **12 new listing browser checks**, **19 public workflow checks** and **12 demo/admin checks passed** against the final local build: 43 browser checks with no JavaScript errors. These cover publication, discovery, enquiry, editing, archival, photo selection/removal, selected map location, all three forms, responsive layouts, account registration and existing admin behaviour.

Three uploaded covers survived forced API/web container recreation with identical SHA-256 hashes. All four Compose services are healthy. Results are in `artifacts/listing-results.json`, `browser-results.json`, `demo-results.json` and `listing-persistence.json`; screenshots include `listing-choices-{width}.png` and `listing-{sale,plot,rent}-review.png`.

The original 123 property rows retain an identical fingerprint excluding the nine new fields. The original 100 synthetic properties remain active and the generic demo user still owns exactly 100 listings. Browser fixtures belong to separate test accounts and were archived. Evidence is in `artifacts/listing-upgrade-data-check.json`; a pre-upgrade PostgreSQL backup is in `artifacts/realsite-before-listing-upgrade.dump`.

See [listing forms](LISTING-FORMS.md) for usage, limits and storage. The Azure VM overlay inherits the image volume; no Azure deployment was performed. Managed Blob storage and abandoned-image cleanup remain future work.

## Beds and baths selection feedback - 9 October 2026

Fixed missing styles on bedroom/bathroom choice buttons. Previously selections changed the search state but selected and unselected options looked identical, with small 22px-high click targets. Choices now have distinct blue selected states, 44px-high buttons, labelled groups and pressed-state accessibility attributes. Both minimum counts can be selected before Apply; reopening retains applied values and Any clears a constraint.

The frontend production build succeeded and the local web container was updated and is healthy. **9 focused browser checks passed**: sale and rental searches at 1920px, 768px, 390px and 360px plus no JavaScript errors. Checks exercise every choice, visible selection, keyboard/touch input, actual combined filter results, reopening, discarding unapplied changes, Any reset and no overflow. The checks are read-only and do not create accounts or listings.

Reproduce with `python scripts/verify_beds_baths.py` after installing the project-local Playwright dependency described in README. Evidence is in ignored `artifacts/beds-baths-results.json` and `artifacts/beds-baths-{sale,rent}-{width}.png`.

## Exact-match checkboxes and room upper limits - 9 October 2026

Retained the familiar **1+, 2+, 3+** defaults and added a separate **Use exact match** checkbox to bedrooms and bathrooms, using grouped count buttons and section bands from the supplied reference. Checking the box converts a minimum to exactly that count. When unchecked, **At least** or **At most** can be chosen independently. Any removes a count constraint; Clear resets both groups and their matching modes. Counts from 6 to 20 are also selectable. A preview and applied-filter summary show the criteria, and saved searches display and restore both room counts and modes.

The API validates `beds_match` and `baths_match` as `min`, `exact` or `max`, applies the corresponding SQL comparison and includes the modes in cache keys and saved-search validation. Missing modes keep previous minimum semantics for old links and saved searches. Room-constrained queries omit commercial properties and plots. No database schema migration was needed.

The backend suite passed **50 tests**, including nine new room-filter cases covering exact/maximum/minimum searches for sale and rent, mixed modes, pagination, cache separation, Any, invalid inputs, saved-search restoration and legacy defaults. The frontend production build succeeded. **11 focused browser checks passed** with no JavaScript errors: all three matching modes and default plus labels at 1920px, 768px, 390px and 360px, checkbox state, touch/keyboard choices, real result IDs, URL reload, cancelling draft changes, Clear, larger counts and saved-search display/restoration. The 360px layout uses a short 640px viewport. Testing caught and corrected the floating mobile Map control overlapping Apply; the background map/list control is hidden whenever a filter panel is open.

All four local services are healthy. Evidence is in `artifacts/beds-baths-results.json` and `artifacts/beds-baths-{sale,rent}-{width}.png`. The focused script now covers this expanded behaviour and supersedes the previous nine-check report. Saved-search browser checks create a separate test account and delete their saved searches after completing; original demo accounts and listings are not modified.

## Simplified room filter controls - 9 October 2026

Removed the **Match counts** dropdowns and the **At least / At most** choices from the public filter. Bedrooms and bathrooms retain **1+, 2+, 3+** choices and independent **Use exact match** checkboxes. Checking converts the selected count to exact matching; unchecking restores plus-count matching. Summaries use compact plus notation, for example **2+ beds**, or **Exactly 2 beds**. Current usage documentation is updated. Existing API maximum matching remains available for compatibility; the public UI does not offer it.

The frontend production build succeeded and the local web container was updated. **11 focused browser checks passed**, covering sale/rental searches at 1920px, 768px, 390px and 360px (including a short 640px viewport), absent matching dropdowns, exact-match checkboxes, plus counts, actual filtered result IDs, keyboard/touch selection, URL reload, Clear, cancelled draft changes, larger room counts, saved searches and no JavaScript errors. This supersedes the previous UI and focused report. Evidence is in `artifacts/beds-baths-results.json` and the corresponding screenshots. Backend behaviour was unchanged by this UI simplification.

## Remove More counts - 9 October 2026

Removed the **More counts (6-20)** dropdowns from both room groups and their unused styles. The filter now contains Any, 1+ through 5+, exact-match checkboxes, a summary, Clear and Apply. Updated the existing browser verification script to remove the larger-count flow and require no selects inside the room filter.

The frontend production build succeeded. Focused browser checks at 1920px, 390px and 360px verified absent dropdowns, converting 2+ to exactly 2 for each room group, applying both exact constraints to real results, no page overflow and no JavaScript errors. Screenshots are in `artifacts/room-counts-final-{width}.png`. The local web container was updated.

## Compact room-filter panel - 9 October 2026

Combined each room heading and exact-match checkbox in one row, removed the duplicate section banners, reduced padding and gaps, and compacted the summary/action area. Count buttons retain 44px-high touch targets. The content fits naturally; the scrollbar is not merely hidden.

The frontend build succeeded. Six focused browser layouts (1920x900, 1366x600, 768x700, 390x844, 360x640 and 360x568) verified that the panel is under 330px tall, every control fits, scroll dimensions do not exceed client dimensions, page width stays within the viewport, and exact 2-bed/2-bath filtering still works. No JavaScript errors occurred. Screenshots and metrics are in `artifacts/compact-room-filter-*`. The existing room-filter regression check now also asserts no internal scrolling. The local web container was updated.

## Price filter and monthly-payment search - 9 October 2026

Implemented the reference tabbed price layouts with INR amounts. List Price uses a 30-bin aggregation of actual filtered active inventory, two draggable/keyboard slider handles and synchronised Min/Max fields. Monthly Payment uses down payment, clearly marked demo credit scenarios and editable APR/tenure. The API applies estimated loan EMI bounds before totals and pagination; cards show estimated payments. URLs, cache keys and saved searches retain financing criteria. Rental searches use monthly rent without home-loan controls.

- Production API/frontend builds succeeded. Final frontend assets: `index-CnEisR0W.css` and `index-CLsEv7vg.js`.
- Isolated backend suite: **68 passed**, including 18 new price/distribution/payment cases. One existing Starlette/AnyIO deprecation warning; no failures.
- Final `python scripts/verify_price_filter.py`: **12 checks passed**, no JavaScript errors. Verified both mouse-drag slider handles, keyboard changes, reversed-range validation, actual INR and EMI result IDs, financing edits, reload, saved-search restoration, custom valid URL values, calculator navigation and rental switching/Clear.
- Six layouts: 1920x900, 1366x600, 768x700, 390x844, 360x640 and 320x568. The panel stays within the viewport; Apply is visible, and editable assumptions remain reachable on short screens. Short-screen panels can scroll while the action area remains available. Screenshots and dimensions: `artifacts/price-*` and `artifacts/price-filter-results.json`.
- Local API/web containers are healthy at http://localhost:8090; readiness reports PostgreSQL and Redis connected. Existing demo inventory is retained: 120 stored demo rows, 100 active. The tests use a separate browser test account and remove its temporary saved searches. Database and uploaded-image volumes were preserved.

Loan rates are planning assumptions, not lender quotes; no credit score is checked. No database schema change or Azure deployment was required. These results were recorded before the documentation release commit.

## India More Filters - 9 October 2026

Implemented the supplied scrollable filter references with fixed actions and India terminology. Connected maintenance, source/category/status, possession/furnishing/ownership, parking, area/year ranges, building features, senior living, multiple amenities/views, owner-supplied RERA/approval details, plot land use and road width, tours, distance, price reductions, listing age and keywords. Add/edit forms retain a collapsed optional details section. Added validated JSON metadata, prior asking price and a repeatable additive migration; refreshed the 100-property public synthetic snapshot.

Final validation:

- API and production frontend builds passed. Web assets: `index-DSaj3JeS.css` and `index-DVRt9sEQ.js`.
- **112 backend tests passed on isolated SQLite**, including 44 new advanced-filter cases. One existing Starlette/AnyIO deprecation warning.
- **14 More Filters browser checks passed** against the restored original portal. Covered combined predicates, actual PostgreSQL results, URL/reload/cancel, visible errors, saved searches, sale/rental/plot details editing, nearby map pin, synthetic 3D model, and six layouts from 1920x900 through 320x568. Apply and Reset stay visible; the scroll body reaches all sections.
- **12 existing price-filter browser checks passed** against the restored original inventory. No JavaScript errors in either browser run. Evidence: `artifacts/more-filters-results.json`, `artifacts/price-filter-results.json` and screenshots.
- Readiness is healthy with PostgreSQL and Redis connected. DB and image volumes were preserved. Browser checks archive their own temporary listings and remove their own saved searches; real customer and demo data remain separate.

### Test-isolation incident and recovery

The initial advanced test imported application models before the older fixture set DATABASE_URL, so its table-reset fixture affected the local PostgreSQL database. This was detected by comparing the original inventory snapshot. The pre-change `artifacts/before-more-filters.sql` backup was restored before continuing. A dump comparison confirmed every row/field in all seven tables matched the backup exactly: 14 users, 133 properties (101 active), 21 uploaded-image records, 19 auth sessions, 8 favourites, 9 enquiries and 10 saved searches.

`tests/conftest.py` now forces SQLite before any test import, the fixture refuses to reset a non-SQLite database, and all documented test commands explicitly set a SQLite DATABASE_URL. The full suite was rerun with that explicit override. The additive migration then preserved every original field/record; all 21 original uploaded images returned valid JPEG responses. Final preservation checks ran after protected tests and browser verification. Evidence: `artifacts/database-restore-verification.json` and `artifacts/more-filters-original-data-preserved.json`. Private backups remain ignored by Git.

The nearby filter is straight-line distance; traffic/travel-time routing remains an integration. Registration/approval details are owner supplied; no verification is implied. 3D demo geometry is illustrative, and video availability is not fabricated. These results were recorded before the documentation release commit.


## Drawn-area map search - 9 October 2026

Added Draw, freehand and clicked-corner drawing, a shaded preview, Undo/Draw again/Finish shape, Apply/Cancel and Remove Boundary. Keyboard users can add corners with Enter and move the centre with arrows. Applying clears the text location and temporary map viewport bounds, retains all property criteria, and stores the polygon in URLs and saved searches. Search totals, pagination, map markers, Redis keys and price distributions share a validated SQL polygon predicate. Edge points and concave polygons are supported. Crossing, degenerate and oversized shapes are rejected. One region with up to 64 corners is supported; no database schema change is required.

- API and production frontend builds passed. Final web assets: `index-DoylTq4G.css` and `index-Bkb79lN1.js`.
- **130 backend tests passed** in an explicitly isolated SQLite container, including 18 new polygon cases. The existing fixture refuses to reset PostgreSQL. One existing Starlette/AnyIO deprecation warning remains.
- **14 drawing browser checks passed** against PostgreSQL: clicked corners, freehand simplification, real result IDs/counts/markers, histogram, combined filters, reload, saved searches, cancel/Escape, browser Back, boundary removal, concavity, invalid shapes/Undo, keyboard drawing/navigation and city changes.
- Drawing was checked at 1366x600, 390x844 and 320x568 with mouse and genuine touch input. Phone toolbar controls remain inside the viewport and retain touch-sized actions. The keyboard hint allows gestures to pass through it.
- **12 existing price-filter browser checks passed**. A separate final-build smoke check confirmed proper INR text, Draw/Apply/reload and healthy database/Redis readiness after the UTF-8 text cleanup. No browser JavaScript errors occurred.
- A read-only PostgreSQL request also confirmed a maximum 64-corner polygon returns matching result and histogram totals.
- Every original account, property, favourite, enquiry, saved-search and uploaded-image record/field matches the original backup; all 21 uploaded JPEGs remain accessible. Transient login-session rows are excluded from this business-data comparison. No application data restore or schema change was needed for drawing.

Evidence: `artifacts/draw-search-results.json`, `artifacts/draw-search-final-smoke.json`, `artifacts/draw-search-data-preserved.json`, `artifacts/draw-search-final.png` and responsive drawing screenshots. See [drawing instructions](DRAW-SEARCH.md). These results were recorded before the documentation release commit.


## Pen drawing usability - 9 October 2026

Changed the default draw interaction to a continuous pen stroke: press/hold, draw and release to close the area automatically. Removed the separate Finish step from the normal pointer workflow. Added a compact Pen/Move map/Redraw/Apply/Cancel toolbar, draggable corner refinement and Edit area for applied boundaries. Stroke updates use animation frames, and no per-sample markers are created while drawing. Mouse, touch and coalesced pointer samples share the same flow.

- Production frontend build passed; deployed web assets: `index-CdDQ2Iqy.css`, `index-C1oAWpJY.js`.
- **9 focused pen browser checks passed**: live mouse stroke, automatic closure, adjustable corners, actual PostgreSQL IDs/counts/markers/histogram, reload/edit/cancel, Move map, Redraw/Escape, removal, accidental clicks, invalid crossed strokes and continuous finger input.
- Layouts at 1366x600, 390x844 and 320x568 keep the toolbar under 70px tall and within the viewport. No horizontal overflow or JavaScript errors.
- The change updates the frontend only. The previously validated backend polygon predicate and database remain unchanged; backend tests were not repeated for this interaction refinement.

Evidence: `artifacts/pen-draw-results.json`, `artifacts/pen-draw-preview.png` and `artifacts/pen-draw-{width}-{height}.png`. See [pen drawing instructions](DRAW-SEARCH.md). These results were recorded before the documentation release commit.


## Pen closing overlap repair - 9 October 2026

Added conservative screen-space stroke cleanup after simplification. Small accidental loops and overruns are split at their intersections and trimmed when the discarded area stays within 8 percent of the retained region. The actual traced outline and concavity remain; it is not replaced by a convex hull. Substantial crossed regions remain invalid and editable. The corrected error directs users to drag a white corner or select the available Redraw action.

- Pure Node geometry checks passed for exact closure, duplicate neighbours, overrunning the start, reverse winding, concave outlines, tiny joining loops and genuine figure-eight crossings. The source was mounted read-only in the cached Node 22 container.
- **10 pen browser checks passed**. A new regression draws back to the initial point and beyond it, verifies Apply is enabled, and compares the cleaned polygon's actual PostgreSQL result IDs with an independent point-in-polygon calculation. Existing mouse/finger strokes, drag editing, map movement, redraw/cancel/removal, histogram and 1366x600/390x844/320x568 layouts still pass. No JavaScript errors.
- Production frontend build and local deployment passed. Assets: `index-CdDQ2Iqy.css`, `index-dCQ0uqMK.js`.
- The fix changes the frontend only; the backend predicate and database were unchanged.

Evidence: `artifacts/pen-draw-results.json`, `artifacts/pen-closing-overlap-fixed.png`, and `frontend/scripts/verify-stroke-shape.mjs`. These results were recorded before the documentation release commit.


## Restore the city after boundary removal - 9 October 2026

Applying a drawn area now remembers the previous text location as `boundary_q` in the URL and saved-search JSON. Remove Boundary restores that location and its map view while retaining property criteria. Redraw/edit and browser navigation preserve the original location; Reset clears property criteria and the polygon while returning to that city. An all-India search still returns to all India. Older drawn links without return context keep their previous all-India fallback.

- Production web/API builds and local deployment passed. Web assets: `index-CdDQ2Iqy.css`, `index-2g9QhHv0.js`. Existing database and upload volumes were retained; no schema migration is required.
- Pure Node transition checks passed for apply/remove, redraw, changed room/rental criteria, new-location search, reset, all-India and legacy links.
- **19 focused API tests passed** in isolated SQLite, including saved return-location persistence, context length validation and confirming the original city does not constrain drawn-area results or histograms. One existing Starlette/AnyIO deprecation warning remains.
- **12 browser checks passed** against the deployed PostgreSQL portal. The reported Hyderabad flow restores the city search, result IDs, markers and map after drawing and reload. All five demo cities and a location-free search retain price/room criteria through removal and Back/Forward. Existing pen drawing, corner adjustment, loop repair, mouse/touch and three responsive layouts pass without JavaScript errors.

Evidence: `artifacts/pen-draw-results.json`, `artifacts/boundary-hyderabad-restored.png` and `frontend/scripts/verify-boundary-search.mjs`. These results were recorded before the documentation release commit.

## Approved RealSite.in identity - 10 October 2026

The final identity uses live HTML text reading **RealSite.in**, matching the homepage's Inter family at weight 900. Blue gradient faces, +0.15px letter spacing and a light 1px-offset/2px-blur shadow replace the generated bitmap lettering. The .in suffix is 80% of the main text size on the same baseline. The emblem is a blue SVG map pin containing a small white house, shared with the favicon. Header, sign-in, footer and illustrative tour use the same identity with responsive sizing and no subtitle.

- Production frontend build and web-only deployment passed. Final assets: `index-BUXfXVy9.css`, `index-DejVZU8F.js`.
- Eight standard/high-density layouts at 1920, 1440, 390 and 320px confirmed exact live text, Inter 900 loading, spacing/shadow, non-overlapping header groups, mobile navigation and no page overflow or JavaScript errors. The final suffix adjustment then passed four desktop/phone layouts, confirming the 0.8 size ratio, baseline alignment and shared placements. Visual inspection confirmed crisp text and the smaller suffix.
- Unused PNG design drafts are archived under ignored `artifacts/branding-designs/`, excluded from the frontend and commit. The superseded wordmark SVG is removed. Emblem revision 4 and favicon revision 9 refresh cached artwork.
- Backend code and database/upload volumes were retained. Backend/filter regression results above are from the prior release and were not rerun for this branding update. This release requires no schema migration or new account setup.

Evidence remains local: `artifacts/live-brand-results.json`, `smaller-domain-results.json`, `logo-smaller-domain.png` and `live-brand-{ratio}-{width}.png`. Git history identifies the released source revision.
