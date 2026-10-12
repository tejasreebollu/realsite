# RealSite project handoff

Updated: 12 October 2026.

RealSite is an India real estate portal built with React, FastAPI, PostgreSQL, Redis and local Docker, with Azure evaluation templates. The accepted release includes the **Find your space. Build your future.** homepage, compact admin analytics, direct-INR synthetic pricing, editable profiles and agent review, India listing/filter workflows, pen drawing and cyan marker hover. The reference screenshots guide the layout; inventory and financing examples remain illustrative.

## Repository and local access

| Item | Value |
| --- | --- |
| Repository | https://github.com/nagaraju-ssa/realsite-repo |
| Branch | `main` |
| Current local checkout | `C:\RealSite-Workspace\realsite-repo` |
| Portal | http://localhost:8090 |
| API docs / readiness | http://localhost:8090/api/docs / http://localhost:8090/api/health |
| Compose project | `realsite-india` |
| Services | `web`, `api`, `db`, `redis` |
| Persistent volumes | `postgres_data`, `redis_data`, `property_images` under the Compose project |

The workspace was renamed from the original project name. Run commands from the actual `realsite-repo` checkout. Git's commit history identifies the source revision; deployment assets and test records are in [verification](VERIFICATION.md).

## Accounts and inventory

| Account | Email | Local demo password |
| --- | --- | --- |
| Generic public user | `demouser@demo.example.com` | `DemoUser@2026` |
| Administrator | `admin@demo.example.com` | `AdminDemo@2026` |

A single public account buys, sells and rents. Owners manage their own listings; administrators use `/admin`. Separate buyer/seller demo logins were consolidated into demouser. The fixed seed contains 100 fictional homes across Hyderabad, Bengaluru, Mumbai, Pune and New Delhi: 12 sale and 8 rental homes per city. Additional owner/test records can increase live totals. Presentation edits and archives persist. The sample photographs, agents, locations, prices and 3D model are illustrative. See [client demo](DEMO.md).

## Profile and account workflows

Click the header avatar or open `/profile`: My Profile edits photo/name/mobile/city/biography; Account Settings changes password/email; Agent Profile submits professional details for admin review. An approved agent keeps the same login and public user permissions. Admin has Accounts, Agent reviews and Account activity tabs. Suspension revokes all sessions and hides the public agent; existing listings require separate archival. Demouser/admin credentials remain fixed; register a separate account for credential-change demonstrations. Local email verification displays a clearly labelled unsent demo code; Azure forces configured SMTP. See [user management](USER-MANAGEMENT.md) for API, privacy, configuration and limitations.

## Start and update locally

Docker Desktop must run Linux containers. Host Node/PostgreSQL are unnecessary. On a fresh checkout:

```powershell
python scripts/prepare_local.py
docker compose up -d --build --wait
docker compose ps
Invoke-RestMethod http://localhost:8090/api/health
```

The preparation script creates `.env` only when missing. Keep the existing `.env`: it holds local database credentials and is ignored by Git. Readiness requires database and Redis connectivity.

After pulling this release into an existing local stack, back up first, then rebuild web/API without replacing data services:

```powershell
git pull --ff-only
docker compose build api web
docker compose up -d --no-deps --wait api web
```

For a frontend-only change, use `docker compose up -d --build --no-deps --wait web`. Refresh the browser with Ctrl+F5. `docker compose down` retains volumes; do not use `down -v` for an upgrade. No Azure resources were provisioned by this work.

## Preserve data before an upgrade

Back up PostgreSQL and uploaded photos together, retaining the matching source revision and `.env` securely. From this checkout:

```powershell
$backupTag = Get-Date -Format 'yyyyMMdd-HHmmss'
New-Item -ItemType Directory -Path artifacts -Force | Out-Null
docker compose exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --file=/tmp/realsite-backup.sql'
docker compose cp db:/tmp/realsite-backup.sql "artifacts/realsite-$backupTag.sql"
docker compose cp api:/app/uploads "artifacts/uploads-$backupTag"
```

Pause listing/account writes during a backup intended as a consistent restore pair. Verify the dump and photo copy completed before updating. Restore to a separate evaluation stack and validate records/photos before switching users to it. The repository's public demo JSON is not a database backup. Backups, screenshots, local credentials and browser tooling are ignored and excluded from the release.

Compatibility startup upgrades are additive and repeatable. This release adds compatible user profile/active columns and agent_profiles/email_changes/account_audit tables, alongside nullable property `features` JSON and `previous_price`; it preserves existing fields and enriches missing synthetic metadata once. Polygon and original-city context are stored in existing saved-search JSON, requiring no additional schema change. Prefer fixing forward over rolling an older application onto a newer schema without validation.

## Demonstrate the latest workflows

- Rooms: select 2+ beds/baths and enable each Use exact match checkbox for exactly two of each. Leave unchecked for minimum counts.
- Price: List Price has the inventory histogram, range handles and INR inputs. Monthly Payment uses editable demo loan assumptions. Rent uses monthly asking rent.
- India Filters: source/status, maintenance, furnishing, parking, area, amenities, views, tours, plot requirements, nearby radius and listing updates. Apply commits a draft; Reset all filters clears criteria and returns to the original city if removing an area.
- Listings: separate property sale, plot sale and rental forms; Details, Location, Photos, Review. Images upload, locations use a map pin, and optional details power filters.
- Draw: filtered property markers stay visible while drawing and previewing; their clicks are disabled until drawing ends. Press/hold, trace an area and release. A thin 24px pen cursor marks the nib; Move map and finished-area editing use a hand. Redraw retries; white corners refine; Apply filters real result counts and markers. Small closing overlaps are repaired, while substantial crossed shapes remain invalid.
- Marker hover: hovering a result card highlights the matching pin with a 1px cyan border and soft glow. Mouse leave clears it; sale and rental cards use the same behaviour.
- Boundary removal: Hyderabad -> Draw -> Apply -> refresh -> Remove Boundary restores Hyderabad and keeps other filters. All-India searches return to all India. Older links without original-location context keep the all-India fallback.

The polygon and `boundary_q` survive URL navigation and saved searches. One simple polygon of up to 64 vertices is supported, including concavity and edge points. Multiple regions and holes remain future work. See [drawing instructions](DRAW-SEARCH.md).

## Verification and known limits

See [testing](TESTING.md) for commands and [verification](VERIFICATION.md) for dated evidence. The 11 October release's isolated backend suite passed 166 cases. The 12 October price update validated 172 cases across the full run (171 passed) and the one budget-adjusted search case rerun. The final combined homepage/admin workflow passes 17 checks; four public-pricing and three card-hover checks are separate implementation evidence. Earlier account/filter/drawing runs remain historical records, not claims of rerunning those suites for a headline change. Backend tests must use isolated SQLite; live workflow scripts can leave test history, while the combined homepage/admin script only creates a login session.

Current local frontend assets are `index-C3ZRAcB0.css` / `index-OwmaSPV4.js`. Use Ctrl+F5 after deployment and check readiness. All 16 Markdown documents are synchronised; there are no maintained Word editions. Local backups, screenshots, browser tooling and private records remain ignored.

External map tiles need internet access. Satellite uses Esri; Street View opens an external Google Maps link. Climate-risk data is unavailable. Nearby radius is straight-line distance. RERA/approval fields are owner supplied. EMI/credit presets are illustrative and do not connect to lenders. No real listing feed, valuation, payment, rental application, external notification or verified-agent service is connected. The built-in 3D model is a synthetic canvas demonstration.

Local volumes preserve photos; Azure Blob/CDN, managed databases, versioned migrations, verified onboarding, moderation, password recovery, monitoring, CI/CD and production recovery drills remain future work. The Azure VM templates are an evaluation path; cloud runtime is unverified. See [scope](SCOPE.md) and [Azure deployment](AZURE.md).

## Brand identity

The current identity displays **RealSite.in** (with the .in suffix at 80% of the main lettering size) as live HTML text in Inter, the same family as the homepage headline, using weight 900, a blue gradient, 0.15px letter spacing and a light shadow. It uses the requested mixed case and upright lettering. There is no wordmark image or subtitle. `frontend/public/realsite-emblem.svg` provides a blue map pin with a small white house at revision 4; the favicon reuses it at revision 9. The shared Logo component covers the left header, sign-in and footer; the illustrative 3D model uses the same text and emblem. The existing Google Fonts import includes Inter 900, with Arial fallback. Responsive text sizes are 26/25/22/20px. Earlier PNG design drafts are archived under ignored `artifacts/branding-designs/` and excluded from the published frontend. See [asset notes](ASSETS.md).

## Source navigation

| Area | Main source |
| --- | --- |
| Search/filter UI and routes | `frontend/src/main.jsx`, `api.js`, `room-filters.jsx`, `price-filter.jsx`, `more-filters.jsx` |
| Map drawing and location return | `map.jsx`, `map-draw.jsx`, `stroke-shape.js`, `boundary-search.js`, `map-draw.css` |
| Brand identity | `frontend/src/branding.css`, shared Logo in `main.jsx`, `frontend/public/realsite-emblem.svg`, `favicon.svg` |
| Cursor / illustrative model | `frontend/public/cursors/pen.svg`, `frontend/public/tours/demo-3d.html` |
| Listing workflow and facts | `listing.jsx`, `listing-features.jsx`, `property-facts.jsx` |
| Profiles, agent review, account security | `backend/app/accounts.py`, `frontend/src/profile.jsx`, `account-admin.jsx`, `profile.css` |
| Admin analytics | `backend/app/analytics.py`, `frontend/src/analytics.jsx`, `analytics.css`, integration in `admin.jsx` |
| Shared API predicates | `backend/app/main.py`, `advanced_filters.py`, `map_boundary.py` |
| Persistence / demo / uploads | `models.py`, `migrations.py`, `seed.py`, `demo_pricing.py`, `uploads.py` |
| Validation | `backend/tests/`, `frontend/scripts/`, `scripts/verify_*.py` |
| Infrastructure | `compose.yml`, `infra/` |

## Accepted homepage and admin analytics

The homepage uses **Find your space. Build your future.** as live white bold text, with a line break between the sentences. The existing photograph, subtitle and search remain available.

Admin opens Analytics by default: four compact KPIs and nine charts, light card shadows, a thin hover border and a 2px KPI lift with reduced-motion support. Refresh and Export city report sit on the filter toolbar's right. Tabs remain above every management section and sticky while scrolling, including Listings and Enquiries. Repeated intros/context banners have been removed.

The full-width **Listing & enquiry activity** plot is the third chart row, below the inventory/account overviews. Blue/teal grouped bars show actual new-listing/enquiry totals; account growth stays a line. The protected, read-only `/api/admin/analytics` supports 30/90/365 India calendar days and all/owner/synthetic listing datasets. These yield 30 daily, 13 seven-day or 13 thirty-day groups respectively; final groups can be shorter. There is no 120-day option.

Inventory is a current snapshot; enquiries and listing additions are period events. Accounts/agents cover the whole portal regardless of listing dataset. Medians separate sale prices and monthly rents; enquiry intensity is not conversion rate. See [admin analytics](ADMIN-ANALYTICS.md) for formulas, export and limitations. Analytics/pricing need no new migration or dependency. Rebuild API/web while retaining data volumes; run `python scripts/verify_admin_analytics.py` for the final 17-check presentation workflow.

## Indian demo price update — 11 October 2026

Fresh seeds use `app/demo_pricing.py` with the requested city sale ranges and unchanged rental model. Sale scores reflect locality, area and type. See [demo assumptions and medians](DEMO.md#indian-demo-pricing). Startup preserves existing price edits; repricing an older local demo is an explicit operation:

```powershell
docker compose run --rm --no-deps api python -m app.demo_pricing
docker compose run --rm --no-deps api python -m app.demo_pricing --apply
python scripts/export_demo.py
```

Take a database backup before applying an inventory update and review the preview. Only recognised synthetic sale seed rows with matching core facts, an original or prior-model amount and compatible previous price qualify. Rentals are excluded. Updated/customised rows are skipped, and manually entered properties are excluded. The command changes only `price` and `previous_price`, then invalidates Redis listing caches. The preview's `city_after` summarises planned changes only; it is not an aggregate of the entire city inventory. Repeating after this release finds zero changes. Deploy only API/web and retain existing volumes.

The 11 October implementation repriced 98 seed homes; two already matched that earlier model. All 142 properties retain identical non-price fields; the other eight business tables have identical fingerprints. The 100-property JSON export is refreshed. The pricing implementation passed 166 isolated backend cases and four focused public-pricing checks. Final homepage/admin verification and current assets are recorded above. The listing/enquiry chart is grouped bars; account growth remains a line. Backup and preservation evidence remain in ignored `artifacts/before-india-pricing.sql` and `artifacts/india-pricing-*`.

## Requested sale ranges — 12 October 2026

The local portal and fresh seed now use Hyderabad ₹2–10 crore, Mumbai ₹5–20 crore, Pune ₹3–12 crore and Bengaluru/New Delhi ₹3–15 crore. Each city's 12 synthetic sale homes includes both endpoints. All 60 sale homes were updated; all 40 rentals are unchanged. Existing previous-price fields are adjusted to retain the demo reduction. See [current pricing and medians](DEMO.md#indian-demo-pricing).

The API was rebuilt/deployed without replacing database, Redis or photo volumes. A database backup preceded the explicit apply. All 142 property records keep identical non-price fingerprints; all other business tables are unchanged. A repeat preview produces zero changes. The 100-home export is refreshed. Backend validation covered 172 cases across the full run and the corrected search-case rerun; four focused public-pricing checks cover live prices, filters, map markers and admin medians. Evidence stays private and ignored under `artifacts/city-ranges-*-2026-10-12.json` and `before-city-ranges-2026-10-12.sql`. Frontend assets are unchanged. Use Git history for the published source revision; database backups and local verification evidence are excluded from the release.
