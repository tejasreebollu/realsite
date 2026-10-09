# RealSite Real Estate Portal · India

RealSite is a working real estate portal for India, with a React interface based on the supplied layout references, a FastAPI API, PostgreSQL persistence, Redis search caching and rate limits, and Docker Compose.

## Open the application

- **Portal:** http://localhost:8090
- **API documentation:** http://localhost:8090/api/docs
- **Readiness:** http://localhost:8090/api/health

Use these local client-demo accounts from **Sign in**:

| Role | Email | Password |
| --- | --- | --- |
| User (buy and sell) | `demouser@demo.example.com` | `DemoUser@2026` |
| Admin | `admin@demo.example.com` | `AdminDemo@2026` |

Admin opens `/admin`. See the [client demo guide](docs/DEMO.md) for capabilities and a walkthrough. New accounts can buy, rent, and sell using **Sign in → Create account**. Local database credentials are randomly generated in the ignored `.env` file.

## Start locally

Docker Desktop must be running in Linux container mode. Host Node.js and PostgreSQL are not required.

From the workspace directory, enter the project folder:

```powershell
cd .\realsite-repo
python scripts/prepare_local.py
docker compose up -d --build
```

The preparation script creates `.env` only if missing and downloads illustrative photographs only if missing. Photos are included in this workspace. To configure manually, copy `.env.example` to `.env` and replace `POSTGRES_PASSWORD` with a random password containing only URL-safe characters.

```powershell
docker compose ps
docker compose logs --tail 50 api
docker compose down
```

`down` preserves PostgreSQL and Redis volumes. Do not add `-v` unless you intend to delete the stored accounts, listings, favourites, and enquiries. The stack uses its own Compose project and exposes only the web application on loopback port 8090.

## What works

- India homepage with photographic hero, city search suggestions, listing carousels, recent views, and buy/rent/sell actions.
- Sale and rental search by city, address, neighbourhood, state, or PIN code.
- Budget, bedrooms, bathrooms, property type, area, amenities, and sorting filters; server-side pagination.
- Interactive OpenStreetMap with actual listing coordinates, INR price markers, map popups, re-centre, and optional viewport searching. Mobile map/list switch.
- **Map Options** button at the map's bottom right: Automatic, Satellite, Street view, and Climate Risk choices. Satellite loads Esri imagery; Street view opens the current map centre in Google Maps. Climate-risk data is currently unavailable and no risk overlays are rendered. See [map options](docs/MAP-OPTIONS.md).
- Property galleries, facts, amenities, location, saved-home actions, and shareable property URLs.
- Single-account registration, sign-in, sign-out, database-backed expiring sessions, and password hashing; administrator access is provisioned separately.
- Persistent private favourites and saved searches; saved searches restore their filters.
- Enquiries with Indian mobile numbers and optional visit dates; owners see received enquiries, buyers see sent enquiries.
- Guided residential/commercial sale, plot sale and rental forms with photo uploads and a map location picker; listing creation, editing, and archival. Archived listings disappear from searches; enquiry history remains.
- Admin dashboard with inventory metrics, city/status filters, paginated account and enquiry review, and listing archival/restoration.
- Home loan EMI calculator with configurable price, down payment, rate, and tenure.
- Responsive layout, keyboard navigation, modal focus handling, and reduced-motion support.
- Azure VM infrastructure template, HTTPS Compose overlay, and deployment script.

## Demo data and remaining parity

The demo seeds **100 fictional listings**, 20 in each of Hyderabad, Bengaluru, Mumbai, Pune, and New Delhi. Each city has 12 sale and 8 rental listings, all owned by `demouser`. This same account starts with five favourites, saved searches and enquiries. Prices and locations are illustrative. Photographs are from Unsplash and do not depict the listed addresses. Sample agents are fictional. Enquiries reach the property owner's inbox without sending external messages. A JSON snapshot is available in [data/demo-properties.json](data/demo-properties.json).

RealSite is a functional first version. The reference layouts and core search workflows are implemented; valuations, live listing feeds, verified agent onboarding, lender services, rental applications/payments, notification delivery, advanced moderation, and production operations remain separate work. See [feature scope](docs/SCOPE.md) for the exact boundary.

Set `SEED_DEMO=false` and `DEMO_ACCOUNTS_ENABLED=false` on a fresh database to start without sample inventory or accounts. Disabling demo accounts also rejects their existing sessions. The Azure overlay disables demo logins. Startup preserves edits and archives; the old 120-home seed is upgraded by archiving 20 surplus rows without deleting history.

## Verify

```powershell
docker compose run --rm --no-deps api python -m pytest -q -p no:cacheprovider
```

The regression suite uses an isolated SQLite database inside a disposable container and a Redis test adapter. It checks authentication, privacy, filter results, cache invalidation, listing ownership, archival, and enquiry routing. Live browser verification additionally exercises the real PostgreSQL and Redis stack.

Optional browser checks use installed Chrome and a project-local Playwright package:

```powershell
python -m pip install --target .tools playwright==1.55.0
python scripts/verify_browser.py
```

Browser checks create a test account, a sample enquiry, a saved search, and an archived test listing in the local database. Screenshots and results are saved under ignored `artifacts/`.

## Technical documents

- [Listing forms, photos and map picker](docs/LISTING-FORMS.md)
- [Architecture and API](docs/ARCHITECTURE.md)
- [Client demo accounts and walkthrough](docs/DEMO.md)
- [Implemented scope and parity roadmap](docs/SCOPE.md)
- [Azure evaluation deployment](docs/AZURE.md)
- [Asset sources](docs/ASSETS.md)
- [Verification record](docs/VERIFICATION.md)

The supplied screenshots are the visual layout references. Map usage follows the [OpenStreetMap tile policy](https://operations.osmfoundation.org/policies/tiles/). Replace the tile provider with an appropriate commercial or self-hosted service before significant public traffic.
