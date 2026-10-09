# RealSite testing and release checks

Updated: 9 October 2026. Run from the repository root. See [verification](VERIFICATION.md) for dated outcomes and [handoff](HANDOFF.md) for setup and data preservation.

## Backend isolation

Build the API image when tests or backend code change, then run the suite in a disposable container with an explicit SQLite override:

```powershell
docker compose build api
docker compose run --rm --no-deps -e DATABASE_URL=sqlite:////tmp/portal-tests.db api python -m pytest -q -p no:cacheprovider
```

`tests/conftest.py` sets SQLite before app imports, and the shared fixture refuses to drop tables on another dialect. The suite uses a Redis adapter and does not reset live PostgreSQL. Current coverage includes auth/privacy, ownership, demo seeding, uploads/listing types, room modes, price/EMI, advanced attributes, polygon geometry/counts/pagination and saved return-location context. Do not bypass the fixture's isolation checks.

## Pure drawing logic

No host npm is required. In PowerShell, mount the frontend read-only in Node:

```powershell
$frontendPath = (Resolve-Path .\frontend).Path
docker run --rm --mount "type=bind,source=$frontendPath,target=/work,readonly" -w /work node:22-alpine node --test scripts/verify-stroke-shape.mjs scripts/verify-boundary-search.mjs
```

These scripts check exact closure, small-loop cleanup, winding, concavity, genuine crossings and original-location restoration through apply/remove/redraw/reset/new searches. They do not replace PostgreSQL/browser verification.

## Browser checks

Start the portal and check `/api/health`. Install project-local Playwright if needed; the scripts launch installed Chrome at `C:\Program Files\Google\Chrome\Application\chrome.exe`:

```powershell
python -m pip install --target .tools playwright==1.55.0
python scripts/verify_draw_search.py
python scripts/verify_beds_baths.py
python scripts/verify_price_filter.py
python scripts/verify_more_filters.py
```

Run the browser scripts sequentially against a local/demo stack. Drawing verification is read-only. Room/price checks register disposable accounts and clean their temporary saved searches; account rows remain. More Filters also creates its own listings, archives them and cleans temporary searches. Existing demo edits may change expected fixture results. Tests check real server IDs/counts, URL/reload/saved state, keyboard/pointer/touch behavior and compact layouts; some create persistent test history.

Other focused workflows are `verify_browser.py`, `verify_demo.py`, `verify_listing_flows.py`, `verify_map_options.py` and `verify_layout.py`. They are historical/reproducible checks rather than a claim that every script ran for every release. General/listing workflows can leave accounts, enquiries and archived listings. Demo checks need the prepared seed workspace. Results and screenshots live in ignored `artifacts/`.

## Manual presentation check

1. Open the home page, Buy, Rent and Open plots; check INR prices and images.
2. Select 2+ beds/baths, enable exact match and confirm every residential result matches. Clear the controls and confirm minimum-count behavior.
3. Exercise List Price, Monthly Payment and rental rent filters; validate reversed ranges and saved searches.
4. Apply India Filters and inspect corresponding listing facts. Check plots/commercial units omit room controls.
5. Search Hyderabad, Draw with a continuous mouse stroke, release and adjust a white corner. The compact pen stays visible during drawing; its tip is the drawing point. Move map and the finished preview show a hand.
6. Apply, refresh, Edit area/Redraw/Cancel and Remove Boundary. Hyderabad and other selected criteria return. Check another city and an original all-India search.
7. Use demouser to add/edit a listing: choose a map pin, upload photos, review and archive the test listing. Confirm the same account can save/contact other owners' listings. Use a separate account to send a demo enquiry to demouser.
8. Use admin to archive/restore a demo listing; restore it before ending the demo. Check one phone layout with finger drawing and the Map/List switch.
9. Open the illustrative 3D model: rotate, Look inside, Reset view and arrow keys. It must remain labelled synthetic.

The compact cursor SVG should decode at 24x24 pixels. Its CSS hotspot is (3,21); `?v=2` selects the updated asset. On a browser that cannot use the SVG cursor, CSS falls back to a crosshair. Touch input has no mouse cursor. Ctrl+F5 refreshes cached application assets.

## Release completion

Validate Markdown links, public demo JSON and `git diff --check`. Confirm web/API builds, readiness and focused workflow results. Stage only intended source/assets/tests/docs and synthetic data; leave `.env`, `.tools`, backups and screenshots ignored. Fetch and inspect remote changes before pushing; use an ordinary push without force. Confirm `git rev-list --left-right --count HEAD...origin/main` is `0 0` after the push.

Backend tests, local browser flows and a production asset build do not establish live inventory accuracy, independent RERA verification, lender eligibility, Azure runtime, production load/security or full accessibility certification.
