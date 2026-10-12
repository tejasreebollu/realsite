# RealSite testing and release checks

Updated: 12 October 2026. Run from the repository root. See [verification](VERIFICATION.md) for dated outcomes and [handoff](HANDOFF.md) for setup and data preservation.

## Backend isolation

Build the API image when tests or backend code change, then run the suite in a disposable container with an explicit SQLite override:

```powershell
docker compose build api
docker compose run --rm --no-deps -e DATABASE_URL=sqlite:////tmp/portal-tests.db api python -m pytest -q -p no:cacheprovider
```

`tests/conftest.py` sets SQLite before app imports, and the shared fixture refuses to drop tables on another dialect. The suite uses a Redis adapter and does not reset live PostgreSQL. Current coverage includes profiles/avatar ownership, credential/session changes, email expiry/replay/SMTP guards, agent review/public privacy, account suspension/audit, additive user migration, auth/privacy, ownership, demo seeding, uploads/listing types, room modes, price/EMI, advanced attributes, polygon geometry/counts/pagination and saved return-location context. Do not bypass the fixture's isolation checks.

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
python scripts/verify_admin_analytics.py
python scripts/verify_accounts.py
python scripts/verify_draw_search.py
python scripts/verify_beds_baths.py
python scripts/verify_price_filter.py
python scripts/verify_more_filters.py
```

The combined homepage/admin script checks the accepted headline, hero search, responsive layouts and all analytics workflows; it creates only an authentication session. Run the browser scripts sequentially against a local/demo stack. Account verification requires local demo email mode and uses a new test account; it archives its listing, rejects its test agent and suspends its account afterward. It tests live PostgreSQL, profile/photo edits, credentials, review, suspension and 320/390px layouts. Leave test history intact. Repeated security tests within ten minutes can hit the intended per-account/client-IP rate limit. Drawing verification is read-only and checks that filtered sale/rental markers remain visible through Pen, Move map, stroke, preview and Redraw, with interaction restored on Cancel. Room/price checks register disposable accounts and clean their temporary saved searches; account rows remain. More Filters also creates its own listings, archives them and cleans temporary searches. Existing demo edits may change expected fixture results. Tests check real server IDs/counts, URL/reload/saved state, keyboard/pointer/touch behavior and compact layouts; some create persistent test history.

Other focused workflows are `verify_browser.py`, `verify_demo.py`, `verify_listing_flows.py`, `verify_map_options.py` and `verify_layout.py`. They are historical/reproducible checks rather than a claim that every script ran for every release. General/listing workflows can leave accounts, enquiries and archived listings. Demo checks need the prepared seed workspace. Results and screenshots live in ignored `artifacts/`.

## Manual presentation check

1. Confirm **Find your space. Build your future.** on the homepage. Open Buy, Rent and Open plots; check INR prices and images.
2. Select 2+ beds/baths, enable exact match and confirm every residential result matches. Clear the controls and confirm minimum-count behavior.
3. Exercise List Price, Monthly Payment and rental rent filters; validate reversed ranges and saved searches.
4. Apply India Filters and inspect corresponding listing facts. Check plots/commercial units omit room controls.
5. Hover sale and rental cards: exactly the matching map pin should have a 1px cyan border and soft glow, clearing on mouse leave. Search Hyderabad, confirm filtered pins stay visible after Draw, then draw with a continuous mouse stroke, release and adjust a white corner. The compact pen stays visible during drawing; its tip is the drawing point. Move map and the finished preview show a hand.
6. Apply, refresh, Edit area/Redraw/Cancel and Remove Boundary. Hyderabad and other selected criteria return. Check another city and an original all-India search.
7. Use demouser to add/edit a listing: choose a map pin, upload photos, review and archive the test listing. Confirm the same account can save/contact other owners' listings. Use a separate account to send a demo enquiry to demouser.
8. Use admin to archive/restore a demo listing; restore it before ending the demo. Check one phone layout with finger drawing and the Map/List switch.
9. Open the illustrative 3D model: rotate, Look inside, Reset view and arrow keys. It must remain labelled synthetic.
10. Click the account avatar, edit profile/photo and reload. With a separate registered account, demonstrate password/email changes. Submit an agent application, approve it through admin, check the directory, resubmit an edit and suspend/reactivate the account. Check Account activity reasons and ensure no private email is public.
11. Check the RealSite.in logo in the header, sign-in, footer and tour: live text, Inter 900, blue map pin/white house, light shadow and .in at 80% size on the same baseline. Check desktop and 320px phone widths; navigation must fit. Ctrl+F5 refreshes cached assets.

The compact cursor SVG should decode at 24x24 pixels. Its CSS hotspot is (3,21); `?v=2` selects the updated asset. On a browser that cannot use the SVG cursor, CSS falls back to a crosshair. Touch input has no mouse cursor. Ctrl+F5 refreshes cached application assets.

## Branding validation scope

The 10 October branding release rebuilt and deployed only the frontend. Focused read-only browser checks confirmed live text/font loading, spacing/shadow, mobile navigation, shared placements and baseline-aligned suffix sizing. The earlier backend/filter/drawing results are retained as historical regression evidence; they were not rerun for the logo change. See [verification](VERIFICATION.md) for final asset hashes and local reports. No database/schema change is required.

## Release completion

Validate Markdown links, public demo JSON and `git diff --check`. Confirm web/API builds, readiness and focused workflow results. Stage only intended source/assets/tests/docs and synthetic data; leave `.env`, `.tools`, backups and screenshots ignored. Fetch and inspect remote changes before pushing; use an ordinary push without force. Confirm `git rev-list --left-right --count HEAD...origin/main` is `0 0` after the push.

Backend tests, local browser flows and a production asset build do not establish live inventory accuracy, independent RERA verification, lender eligibility, Azure runtime, production load/security or full accessibility certification.

## Account and map release evidence

The account implementation passed 149 isolated backend cases and 11 live account checks. The drawing follow-up passed 14 read-only browser checks. Two focused read-only sale/rental checks verified the matching pin's cyan 1px border, glow and mouse-leave reset. The final CSS-only hover update did not rerun the backend suite. See [verification](VERIFICATION.md) for the final frontend assets, preserved-data comparison and remaining SMTP/Azure limits.

## Initial admin analytics checks — 11 October 2026

The full isolated backend suite passed 162 cases (149 existing plus 13 analytics cases), with one existing Starlette/AnyIO deprecation warning. `backend/tests/test_analytics.py` checks authorization, no-store responses, private-field exclusion, current stock versus period activity, medians, archived enquiries, dataset scoping, rates, price bands, empty data, accepted windows and India midnight boundaries.

The live headless Chrome workflow passed 11 analytics checks: default landing/nine charts, focus/hover values, date/dataset controls, separate sale/rent pricing, CSV export, all existing admin tabs, 1280/768/390/320px layouts, failure/retry, a mocked empty synthetic dataset, and spreadsheet-prefix escaping. Browser fixtures intercept only their own requests and do not insert business data. Reports/screenshots are ignored under `artifacts/analytics-*`. See [analytics guide](ADMIN-ANALYTICS.md) and [verification](VERIFICATION.md).

### Compact dashboard follow-up

At the compact-layout stage, `python scripts/verify_admin_analytics.py` passed 12 checks, adding requested text-removal checks, actions inside the filter toolbar, desktop KPI heights below 125px, 10px desktop chart row gaps and sticky visible tabs in every management section. It verifies empty records without expecting the removed context banner. The backend was unchanged; the previous 162-case result was not rerun for this frontend-only follow-up.

### Grouped bars and Indian pricing follow-up

The 11 October full isolated backend suite passed **166 cases**, including four new `backend/tests/test_demo_pricing.py` cases. They verify fresh prices with stable seed facts, size/type/city relationships, preview/apply/repeat behavior, preservation of manual/customised rows and non-price fields, archive state, and restart preservation. Tests use disposable SQLite, not the live PostgreSQL data. One existing Starlette/AnyIO deprecation warning remains.

At the grouped-bar stage, the reusable analytics browser script passed **13 checks**, adding grouped-bar counts and proportional heights against the API, all reporting windows, and retention of the account-growth line. Four focused read-only pricing checks confirm all five cities' sale/rent prices against the exported 100 homes, sorting/budget filters, Hyderabad cards/map prices and synthetic city medians. No JavaScript errors occurred. API/web builds, health, repeat preview and post-update fingerprints passed. Evidence is in ignored `artifacts/india-pricing-*`; only synthetic `data/demo-properties.json` is tracked.

### Full-width activity row follow-up

At the full-width-row stage, the analytics browser workflow passed 14 checks. It verifies two three-card rows above the single full-width activity panel, the SVG using its available width without stretching labels, accurate bar heights, date-window bucket counts, keyboard/hover values and separation between bars at 1280/768/390/320px. Existing reporting controls, management tabs, export, empty data and error recovery remain covered. The frontend build is deployed as `index-C3ZRAcB0.css` / `index-DiqGdVjZ.js`. Backend code and data are unchanged; the preceding 166-case backend result remains prior evidence.

## Final homepage and analytics release checks

`python scripts/verify_admin_analytics.py` passes **17 checks**: three public-homepage checks plus 14 admin checks. It verifies the exact accepted headline, hero bounds and search at 1920/1440/768/390/320px, all nine charts, the full-width third row, API-proportional grouped bars, 30/90/365-day buckets, dataset changes, sale/rent switching, CSV escaping, sticky management tabs, error/retry and empty data. It writes reports/screenshots only under ignored `artifacts/` and creates a login session without changing business records.

The earlier **166-case** isolated backend result covers this release's backend, including four repricing safety cases; the final headline/doc edits do not change backend code. Four focused public-pricing checks and three card-hover checks are separate evidence from this implementation. Re-run affected tests when source or runtime behaviour changes, rather than treating previous evidence as a fresh run. See [verification](VERIFICATION.md) for final release outcomes.

## Requested city sale ranges — 12 October 2026

`test_demo_pricing.py` now includes five city-range cases plus an upgrade case for the prior INR model. They verify exact lower/upper endpoints, varied sale prices, unchanged rental formulas, sale-only preview/apply, rental/non-price preservation and idempotence. Existing safety checks retain coverage of manual/customised records and restart preservation. The search regression's budget was updated from ₹2 crore to ₹6 crore for the higher Hyderabad stock.

The isolated run passed 171 of 172 cases; the budget-adjusted search case then passed its targeted rerun, validating all 172 cases across the two runs. One existing Starlette/AnyIO deprecation warning remains. Four read-only public-pricing checks confirm live city/purpose amounts against the export, sorting and bounds, Hyderabad cards/map markers and synthetic admin medians. Private before/after fingerprints verify preservation. The earlier 17-check homepage/admin workflow is prior evidence, not a fresh run for this backend/data update.
