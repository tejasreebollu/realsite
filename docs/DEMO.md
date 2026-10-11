# Client demo

Updated: 11 October 2026.

## Accepted homepage and compact dashboard

Start with **Find your space. Build your future.** on the homepage, then search a city. The existing hero subtitle and search remain available. Demonstrate the smaller `.in` wordmark suffix and the blue map-pin/white-house emblem.

Sign in as admin and open Analytics: four compact KPIs and nine charts, with reporting controls on the left and Refresh/Export city report on the right. Hover a KPI for its light shadow, thin border and small lift. The full-width **Listing & enquiry activity** chart sits on the third chart row; grouped blue/teal bars show new listings and enquiries. Account growth stays a line. Show 30 days (30 daily groups), 90 days (13 seven-day groups) and 12 months (13 thirty-day groups); final groups can be shorter. The menu does not include 120 days.

Switch all/owner/synthetic datasets, switch sale/rent price distributions and export the aggregate city CSV. Management tabs remain visible for Listings and Enquiries as well as the account sections. See [analytics](ADMIN-ANALYTICS.md) for definitions and planning limits. Run `python scripts/verify_admin_analytics.py` before presenting to check the accepted homepage and admin workflows without inserting business records.

Open **http://localhost:8090** and use **Sign in**. The public demo uses one account for buying, renting and selling.

| Account | Email | Password | What to demonstrate |
| --- | --- | --- | --- |
| demouser | `demouser@demo.example.com` | `DemoUser@2026` | Search, filters, maps, saved homes/searches, enquiries, 100 owned listings, publication, editing and archival |
| Administrator | `admin@demo.example.com` | `AdminDemo@2026` | Analytics charts, reporting controls, planning signals, city CSV, filters, paginated listings/enquiries, account edit/suspend/reactivate, agent reviews, account activity, archive and restore |

The generic account displays **demouser** with role **User**. The old buyer and seller demo emails no longer sign in. Public registration creates a user account without asking for buyer/seller account type. All users can save homes, contact owners and manage their own properties. Administration remains restricted to provisioned administrators.

## Presentation branding

The approved identity is **RealSite.in**, with a blue house/map-pin emblem, bold live text, a light shadow and a smaller .in suffix. It appears in the header, sign-in, footer and illustrative tour. Use Ctrl+F5 after updating the local frontend, then check the desktop and phone layouts before presenting. No logo subtitle is displayed.

## Inventory

| City | State | Sale | Rent | Total |
| --- | --- | ---: | ---: | ---: |
| Hyderabad | Telangana | 12 | 8 | 20 |
| Bengaluru | Karnataka | 12 | 8 | 20 |
| Mumbai | Maharashtra | 12 | 8 | 20 |
| Pune | Maharashtra | 12 | 8 | 20 |
| New Delhi | Delhi | 12 | 8 | 20 |
| **All supported cities** | | **60** | **40** | **100** |

Homes include apartments, villas and independent houses with 2–5 bedrooms, Indian addresses, INR sale/monthly rental prices, map coordinates, galleries, amenities and fictional agent labels on sample listings. Addresses, PIN codes, map locations and prices are illustrative; they are not verified property information. Photos are illustrative Unsplash assets and do not depict the listed Indian addresses. The mock enquiry phone is a placeholder. No enquiry email, SMS or external agent messages are sent. Email-change verification uses an explicitly labelled local demo code unless SMTP is configured.

The generic account starts with one favourite, saved search and synthetic enquiry per city. During the upgrade, the old buyer's saved activity and sent enquiries are transferred to the renamed seller account. Those historical enquiries now appear as sent from the same account that owns the demo homes. Messages from other accounts appear as received enquiries. Changes during a presentation persist.

## Suggested walkthrough

1. Search Hyderabad; hover a property card to show its matching pin's thin cyan glow, then demonstrate sale/rental filters, exact bedroom/bathroom matching, INR price or estimated-payment filters, India More Filters, galleries and Map Options. Draw an area with the pen, release, Apply, refresh and Remove Boundary to show that Hyderabad returns.
2. Sign in as **demouser**. Show Favourites, Updates and Inbox.
3. With the same login, open **Manage listings**, edit a property, or choose **Sell a property**, **Sell an open plot**, or **Rent a property**. Follow Details, Location, Photos and Review; select a map location and upload your photos. New properties are additional inventory, separate from the 100 synthetic homes.
4. To demonstrate incoming enquiries, submit one from another registered user, then return to demouser's Inbox.
5. Sign out and sign in as admin. Analytics opens by default: show the nine charts, change the reporting period and listing dataset, switch Sale/Rent pricing and export the city report. Explain that synthetic listings are labelled and that account/agent charts cover the whole portal. Open Listings to show city filters. Archive a listing, verify it disappears from search, then restore it before the next demo.

Satellite needs internet access. Street view opens Google Maps. Climate-risk data remains unavailable.

## Profile and agent walkthrough

Click the header avatar to edit a photo, name, mobile, city and biography. Demouser and admin credentials stay fixed. Register a separate account to demonstrate Account Settings: change password, request a new email, use the labelled local demo code and Verify email. No mail is sent in demo mode.

From the same account, complete Agent Profile and Submit for review. Sign in as admin, open Agent reviews and approve with a reason. Find an agent then shows the approved profile and its owned listings. Professional edits return to review. Show Accounts search/edit/suspend/reactivate and Account activity; reactivate after demonstrating suspension. The directory no longer contains fictional placeholder cards. See [user management](USER-MANAGEMENT.md).

## Data and repeatability

The deterministic seed is in `backend/app/seed.py`. Stable keys prevent duplicate rows. Existing listings, edits, archives and saved choices remain intact. The original 120-home dataset retains 100 active homes and archives 20 surplus rows without deleting history.

The account upgrade reuses the former seller's ID, renames it to demouser, sets its new demo credentials once, merges the former buyer's owned properties, favourites, saved searches and enquiries, then removes the old buyer. Overlapping favourites are combined. Old sessions for these two demo logins are revoked. Admin credentials and unrelated customer accounts are preserved. A conflicting non-demo account is never taken over or deleted.

Later startups do not reset the generic password or saved choices. For another presentation, restore archived listings and reverse presentation edits through the app.

`data/demo-properties.json` is a public-field snapshot, not a database reset file. Refresh it with:

```powershell
python scripts/export_demo.py
```

Local Compose enables `SEED_DEMO=true` and `DEMO_ACCOUNTS_ENABLED=true`. Demo accounts are created and upgraded only when both are enabled. Disabling demo accounts blocks login and existing demo sessions without deleting records; the Azure overlay disables them. For a clean non-demo installation, use both flags set to false with a separate fresh database.

## Verification

```powershell
docker compose run --rm --no-deps -e DATABASE_URL=sqlite:////tmp/portal-tests.db api python -m pytest -q -p no:cacheprovider
python scripts/verify_demo.py
python scripts/verify_browser.py
```

The API suite verifies inventory, one-account buying/selling, ownership isolation, admin boundaries, disabled demo sessions, repeated seeding and account consolidation with preserved activity. Browser checks exercise both demo accounts and the public registration/listing flow. Demo checks assume the 100 active homes and at least the five initial favourites/searches remain intact; additional saved choices are preserved. Moderation checks restore their listing before finishing; evidence is saved under ignored `artifacts/`.

## Bedroom and bathroom filters

The default **2+** means two or more. Each group has its own **Use exact match** checkbox.

| What the client wants | Choose in Beds & baths, then Apply |
| --- | --- |
| Exactly 2 bedrooms and 2 bathrooms | Select 2+ in both groups and check Use exact match for both |
| At least 3 bedrooms and exactly 2 bathrooms | Select 3+ bedrooms without exact match; select 2 bathrooms with exact match |

Clear resets both groups; Any removes that group's count restriction. Applied criteria appear above the results, and saved searches retain the counts and matching modes.

## Price filter demo

Open **Buy > Price**. **List Price** shows the matching inventory distribution; drag either handle or enter INR Min/Max, then Apply. Switch to **Monthly Payment** to choose an estimated EMI budget, down payment and a demo credit scenario. Expand **Edit rate & tenure** to adjust assumptions. Matching cards show their estimated EMI beside the asking price. Save the search to retain these settings in Updates. The budget link opens the EMI calculator.

Under Rent, Price filters monthly rent and hides home-loan inputs. Credit scenarios and interest rates are illustrative planning inputs; they do not check a score or return lender offers. See [price filter details](PRICE-FILTER.md).

## India More Filters demo

Open **Buy > Filters**. Combine Owner listings, Max monthly maintenance, possession, parking and required amenities. Selected amenities use AND; views and selected listing categories use OR within the group. Scroll the panel; Reset all filters and Apply remain visible. Changes stay in the panel until Apply. Save a search, then open it through Updates to restore all criteria.

Rent hides sale categories/RERA; plots expose land use, square-yard/acre ranges, road width and approval-details filters while hiding building-specific requirements. The nearby map pin filters straight-line distance; it does not calculate travel time. The sample 3D model is clearly labelled illustrative. Video filters match only listings with a supplied video URL; no video availability is invented.

The existing 100 synthetic homes receive varied new feature metadata once. Existing owners' prices, dates, photos and edits are retained. Unknown customer details remain unknown. See [India filter details](MORE-FILTERS.md).

## Draw your own search area

Open Buy, Rentals or Open plots and choose **Draw** on the map (switch to Map on phones). Press and hold, draw around a neighbourhood with the mouse or your finger, then release and choose Apply. Pen is selected by default. Filtered properties stay visible in Pen, Move map and preview; pin clicks are disabled during drawing so they do not interrupt the stroke. The compact pen cursor indicates drawing; the hand indicates Move map or adjusting the finished preview. Use Redraw to try again, or drag the white corner handles to adjust the boundary. Results and map prices show only matching listings within that boundary. Keep refining the price or property criteria, save the area, or choose Remove Boundary. Applying an area temporarily replaces the text city search; Remove Boundary restores the original location, including after a refresh. Price, room and other filters stay selected. See [drawing instructions](DRAW-SEARCH.md).

For the current release checks, setup and maintenance instructions, see [testing](TESTING.md), [verification](VERIFICATION.md) and [project handoff](HANDOFF.md). The live database may contain additional presentation/test accounts and listings; the fixed 100-listing count describes the synthetic seed, not all current records.

See [admin analytics](ADMIN-ANALYTICS.md) for chart definitions and planning suggestions. The demo uses actual stored synthetic/test activity; no fake growth series, closed sales or revenue are inserted. Sparse periods stay sparse.

## Indian demo pricing

The 100 synthetic homes use deterministic Indian sale and monthly-rent assumptions in `backend/app/demo_pricing.py`. Prices depend on the city, locality, floor area and property type; larger homes and Mumbai generally cost more. This is direct INR pricing, with no USD conversion. The previous seed used broad random INR amounts unrelated to the home's area.

| City | Base sale assumption ₹/sqft | Base rent assumption ₹/sqft/month | Demo median sale | Demo median monthly rent |
| --- | ---: | ---: | ---: | ---: |
| Hyderabad | 5,200 | 18 | ₹98.25 lakh | ₹42,750 |
| Bengaluru | 6,200 | 20 | ₹1.07 crore | ₹40,500 |
| Mumbai | 12,500 | 32 | ₹2.43 crore | ₹71,500 |
| Pune | 4,800 | 16 | ₹81 lakh | ₹30,000 |
| New Delhi | 6,200 | 19 | ₹1.14 crore | ₹38,000 |

Locality multipliers range from 0.80–1.40. Apartments use a type multiplier of 1.00, houses 1.08 and villas 1.18, with reproducible variation of 0.88–1.04. Sale values round to ₹50,000 and monthly rents to ₹500. The current 60 sale homes range from ₹52.5 lakh to ₹3.69 crore; the 40 rentals range from ₹19,000 to ₹92,000/month. The seed contains 2–5 bedroom homes, so it does not represent the full market of smaller budget units or luxury properties.

These numbers are chosen demonstration assumptions, not measured city averages or verified quotes for the illustrative addresses. [Magicbricks locality price trends](https://www.magicbricks.com/Property-Rates-Trends/ALL-RESIDENTIAL-rates-in-Hyderabad) and [its rental research](https://property.magicbricks.com/microsite/research-insights/rental-index/index.html) were reviewed for Indian pricing context; the formula is not a valuation model or live feed.

The local update changed 98 unchanged seed prices; two already matched. It preserved all other property fields, owner-entered prices, account records, photos, favourites, saved searches and enquiries. Older surplus archived seed rows are retained with their historical amounts. Normal restarts do not reset presentation edits. The exported 100-property snapshot matches the live synthetic inventory; use the Synthetic listings dataset to show its medians separately from owner/test inventory.
