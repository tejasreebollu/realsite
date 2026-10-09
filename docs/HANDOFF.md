# RealSite project handoff

Updated: 10 October 2026.

RealSite is an India real estate portal built with React, FastAPI, PostgreSQL, Redis and local Docker, with Azure evaluation templates. This release includes the latest room/price/India filters, optional listing metadata, pen drawing, closing-overlap repair, original-city restoration, compact pen cursor and the approved live-text RealSite.in identity. The reference screenshots guide the layout; this is a functional demo with synthetic inventory.

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

Compatibility startup upgrades are additive and repeatable. This release adds nullable property `features` JSON and `previous_price`; it preserves existing fields and enriches missing synthetic metadata once. Polygon and original-city context are stored in existing saved-search JSON, requiring no additional schema change. Prefer fixing forward over rolling an older application onto a newer schema without validation.

## Demonstrate the latest workflows

- Rooms: select 2+ beds/baths and enable each Use exact match checkbox for exactly two of each. Leave unchecked for minimum counts.
- Price: List Price has the inventory histogram, range handles and INR inputs. Monthly Payment uses editable demo loan assumptions. Rent uses monthly asking rent.
- India Filters: source/status, maintenance, furnishing, parking, area, amenities, views, tours, plot requirements, nearby radius and listing updates. Apply commits a draft; Reset all filters clears criteria and returns to the original city if removing an area.
- Listings: separate property sale, plot sale and rental forms; Details, Location, Photos, Review. Images upload, locations use a map pin, and optional details power filters.
- Draw: press/hold, trace an area and release. A thin 24px pen cursor marks the nib; Move map and finished-area editing use a hand. Redraw retries; white corners refine; Apply filters real result counts and markers. Small closing overlaps are repaired, while substantial crossed shapes remain invalid.
- Boundary removal: Hyderabad -> Draw -> Apply -> refresh -> Remove Boundary restores Hyderabad and keeps other filters. All-India searches return to all India. Older links without original-location context keep the all-India fallback.

The polygon and `boundary_q` survive URL navigation and saved searches. One simple polygon of up to 64 vertices is supported, including concavity and edge points. Multiple regions and holes remain future work. See [drawing instructions](DRAW-SEARCH.md).

## Verification and known limits

See [testing](TESTING.md) for commands and [verification](VERIFICATION.md) for dated results and local evidence. Backend checks must use isolated SQLite; fixtures reject PostgreSQL table resets. Live browser scripts can create test accounts and records. The prior search/filter release passed 131 backend cases, geometry/location logic and browser drawing/filter flows. The branding release validates the frontend build, font loading, responsive layout and shared logo placements; it does not rerun backend regressions.

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
| Shared API predicates | `backend/app/main.py`, `advanced_filters.py`, `map_boundary.py` |
| Persistence / demo / uploads | `models.py`, `migrations.py`, `seed.py`, `uploads.py` |
| Validation | `backend/tests/`, `frontend/scripts/`, `scripts/verify_*.py` |
| Infrastructure | `compose.yml`, `infra/` |
