# Verification record · 8 October 2026

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
