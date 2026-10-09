# Client demo

Open **http://localhost:8090** and use **Sign in**. The public demo uses one account for buying, renting and selling.

| Account | Email | Password | What to demonstrate |
| --- | --- | --- | --- |
| demouser | `demouser@demo.example.com` | `DemoUser@2026` | Search, filters, maps, saved homes/searches, enquiries, 100 owned listings, publication, editing and archival |
| Administrator | `admin@demo.example.com` | `AdminDemo@2026` | Inventory metrics, filters, paginated listings/accounts/enquiries, archive and restore |

The generic account displays **demouser** with role **User**. The old buyer and seller demo emails no longer sign in. Public registration creates a user account without asking for buyer/seller account type. All users can save homes, contact owners and manage their own properties. Administration remains restricted to provisioned administrators.

## Inventory

| City | State | Sale | Rent | Total |
| --- | --- | ---: | ---: | ---: |
| Hyderabad | Telangana | 12 | 8 | 20 |
| Bengaluru | Karnataka | 12 | 8 | 20 |
| Mumbai | Maharashtra | 12 | 8 | 20 |
| Pune | Maharashtra | 12 | 8 | 20 |
| New Delhi | Delhi | 12 | 8 | 20 |
| **All supported cities** | | **60** | **40** | **100** |

Homes include apartments, villas and independent houses with 2–5 bedrooms, Indian addresses, INR sale/monthly rental prices, map coordinates, galleries, amenities and fictional agent profiles. Addresses, PIN codes, map locations and prices are illustrative; they are not verified property information. Photos are illustrative Unsplash assets and do not depict the listed Indian addresses. The mock enquiry phone is a placeholder. No email, SMS or external agent messages are sent.

The generic account starts with one favourite, saved search and synthetic enquiry per city. During the upgrade, the old buyer's saved activity and sent enquiries are transferred to the renamed seller account. Those historical enquiries now appear as sent from the same account that owns the demo homes. Messages from other accounts appear as received enquiries. Changes during a presentation persist.

## Suggested walkthrough

1. Search Hyderabad; demonstrate sale/rental filters, galleries and Map Options.
2. Sign in as **demouser**. Show Favourites, Updates and Inbox.
3. With the same login, open **Manage listings**, edit a property, or choose **Sell a property**, **Sell an open plot**, or **Rent a property**. Follow Details, Location, Photos and Review; select a map location and upload your photos. New properties are additional inventory, separate from the 100 synthetic homes.
4. To demonstrate incoming enquiries, submit one from another registered user, then return to demouser's Inbox.
5. Sign out and sign in as admin. Show metrics and city filters. Archive a listing, verify it disappears from search, then restore it before the next demo.

Satellite needs internet access. Street view opens Google Maps. Climate-risk data remains unavailable.

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
docker compose run --rm --no-deps api python -m pytest -q -p no:cacheprovider
python scripts/verify_demo.py
python scripts/verify_browser.py
```

The API suite verifies inventory, one-account buying/selling, ownership isolation, admin boundaries, disabled demo sessions, repeated seeding and account consolidation with preserved activity. Browser checks exercise both demo accounts and the public registration/listing flow. Demo checks assume the 100 active homes and at least the five initial favourites/searches remain intact; additional saved choices are preserved. Moderation checks restore their listing before finishing; evidence is saved under ignored `artifacts/`.
