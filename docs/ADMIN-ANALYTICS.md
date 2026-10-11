# Admin analytics and planning

Updated: 11 October 2026.

Sign in as an administrator and open **Admin → Analytics** at `/admin`. Analytics is the default admin view. Listings, Accounts, Agent reviews, Account activity and Enquiries remain available in the same workspace.

## Reporting controls

- **Reporting period:** last 30 days, 90 days or 365 days (labelled last 12 months). Calendar days use Asia/Kolkata; the current day can be incomplete. The prior comparison is the immediately preceding equal-length period.
- **Listing dataset:** all listings, owner listings or synthetic listings, using the stored `Property.demo` flag. This scopes inventory, prices, listing additions, enquiries, saved homes and city analysis. Owner listings can include testing activity; they are not automatically verified market inventory.
- **Refresh:** requests a fresh, private database snapshot. Loading and failures clear previous charts so old data is not presented under newly selected controls. Retry is available.
- **Export city report:** downloads aggregate CSV with the period, dataset, listing counts, enquiries, rates and median prices in INR. No names, emails, phones or enquiry messages are exported. Cells are quoted and spreadsheet formula prefixes escaped.

Account and agent charts always cover the whole portal, including demo accounts. The chart subtitles and this guide describe their scope; these counts do not change when the listing dataset changes.

## Metrics and nine charts

| View | Meaning and planning use |
| --- | --- |
| Active listings KPI | Current publicly active stock, with sale/rent split. Archived records are counted separately; archival does not imply a completed sale. |
| Enquiries KPI | Enquiry records created in the selected period, including enquiries on listings that are now archived. Shows the absolute change from the previous period. This is not a count of unique buyers or conversions. |
| Median sale / rent KPIs | Median of current active asking prices, separated into sale price and monthly rent. Sale inventory includes open plots. Empty groups display a dash. |
| Listing and enquiry activity | Grouped vertical bars: blue new listings and teal enquiries in each time bucket. Actual creation events, including listing additions that are now archived. Zero-filled daily, 7-day or 30-day buckets start at the first selected day; the final bucket can be shorter. Hover or keyboard focus reveals values. It is not historical inventory size. |
| City supply and demand | Grouped bars compare current active inventory and period enquiries. Shows up to eight cities ranked by enquiry count; the table and CSV contain all cities. |
| Inventory mix | Donut shows sale/rent shares, with owner/synthetic and archived totals. Interactive legend reveals segment counts. |
| Property types | Bars show current active stock by stored type, including residential, commercial and plot types when present. |
| Asking price distribution | Separate Sale and Rent modes. Sale bands: under ₹50 lakh, ₹50 lakh–1 crore, ₹1–2 crore, ₹2–5 crore, ₹5 crore+. Rental bands: under ₹15,000, ₹15,000–30,000, ₹30,000–50,000, ₹50,000–1 lakh and ₹1 lakh+. Lower bounds are included, upper bounds excluded. |
| Account composition | Current role counts, with active/suspended and demo account totals. A user role can both buy and sell. |
| Account growth | Line chart of registrations created in the selected period, across all accounts. Current saved-search count is labelled separately as a stock total. |
| Agent review pipeline | Current pending/approved/rejected application counts; does not represent historical approvals or independent licence verification. Links to the review queue. |
| Inventory age | Current active listings grouped by elapsed days since creation: 0–30, 31–90, 91–180 and 181+. Age alone does not establish poor performance. |

The city table shows sale/rent counts, enquiries, enquiry rate and separate medians. **Enquiries per 100 active listings** uses period enquiries on currently active listings divided by current active stock, multiplied by 100. It is an intensity measure, can exceed 100, and is not a conversion percentage. Cities with enquiries but no active stock show a dash for this rate.

Current saved homes are the number of favourite records attached to the selected listing dataset, including archived listings. Favourites have no timestamp, so no period trend is claimed. Listings without enquiries count only currently active listings with zero enquiry records in the selected period.

## Planning signals

Three deterministic suggestions link to the existing management sections: examine the city with most enquiries (or establish a baseline if none), review listings with no enquiries, and review pending agent applications. These describe RealSite activity and do not forecast external market demand, financial returns or revenue. The listing dataset control separates synthetic and owner inventory; thin or empty datasets stay empty rather than receiving invented series.

## Implementation and access

- UI: `frontend/src/analytics.jsx`, `analytics.css`; integrated into `admin.jsx`.
- API: `GET /api/admin/analytics?days=30&dataset=all`, implemented in `backend/app/analytics.py`, registered in `main.py`.
- Reporting period accepts only 30, 90 or 365; dataset accepts `all`, `owner`, `synthetic`. Invalid parameters return 422.
- The existing server administrator dependency enforces access; unauthenticated requests return 401 and public users 403. Responses use the existing private `no-store` policy.
- The endpoint is read-only. No migrations, new database fields, dependency packages or synthetic history are required.
- SVG/CSS charts use React and existing icons. The layout adapts down to 320px; only the city table scrolls horizontally when needed. Controls and chart points have keyboard focus and labels.
- Aggregation reads scoped inventory metadata and two reporting windows of enquiry events. At larger production volumes, move repeated aggregates to database rollups and benchmark query/index needs; this release is validated against local portal data, not a production load benchmark.

## Verification

The current full isolated backend suite passed **166 tests**, including 13 analytics cases and four demo-pricing safety cases covering admin access, private responses, medians, stock versus flow, archived enquiries, rate denominators, dataset scoping, complete time buckets, India midnight boundaries, empty inventory, invalid parameters and exact price-band boundaries.

`python scripts/verify_admin_analytics.py` uses the local demo admin and the existing `.tools` Playwright installation with Chrome. It creates a login session; mocked empty/export cases intercept only browser requests, without changing stored business records.

The final combined browser workflow passes **17 checks**: three accepted-homepage checks and 14 analytics checks. It verifies the exact headline and hero search through 320px, as well as the full-width third-row plot. Headless Chrome checked the default admin landing, all nine charts, chart focus/hover, reporting windows, all datasets, sale/rent switching, aggregate CSV, existing management tabs, 1280/768/390/320px layouts, and failure/retry without stale charts. No JavaScript errors occurred. Evidence is kept under ignored `artifacts/analytics-*`; see [verification](VERIFICATION.md).

## Compact layout refinement

The dashboard removes the portal intro, Insights & Planning heading, synthetic/context banners and People & platform health intro. Refresh and Export sit on the right of the filter toolbar. KPI cards fit their text, chart panels use smaller padding and 10px desktop / 8px mobile row gaps. Admin tabs appear before every section's content, remain sticky below the portal header while scrolling, and return to the top when switching tabs. The Listings/Enquiries summary cards are compact and appear below navigation. All nine charts, metric definitions and report controls remain available.

The earlier compact-layout browser workflow passed 12 checks, including the requested removals, toolbar placement, compact KPI height/gaps, persistent navigation across all management sections, mobile widths, empty data and export. This frontend refinement does not change analytics formulas or the database.

Dashboard cards have a light resting shadow and a thin blue hover border with a slightly stronger soft shadow. KPI cards lift by 2px without moving neighbouring cards. Hover motion is limited to fine pointers and is disabled when reduced motion is requested; focus within interactive cards retains border/shadow feedback.

## Activity bars and Indian demo prices

The activity chart uses grouped bars for all three reporting windows. Hover or keyboard focus reveals the bucket values; zero-count buckets stay zero. Account growth retains its line chart. The earlier grouped-bar browser workflow passed 13 checks, including bar heights/counts against API data and daily/weekly/monthly grouping.

The 100 synthetic homes now use city/locality/area/type pricing assumptions expressed directly in INR, rather than broad random amounts. Price KPIs, histograms and city exports read the updated stored values. Owner-entered prices remain unchanged. These are illustrative demo scenarios, not live market valuations; see [demo pricing assumptions and ranges](DEMO.md#indian-demo-pricing).

## Full-width activity row

Listing & enquiry activity occupies its own full-width third chart row, below the inventory and account overview rows. The SVG measures the available width and redistributes the bars while keeping text proportions and a compact 180px plot height. City supply, inventory age and planning signals share the following row. All nine charts remain present.

| Selected period | Time represented by each group | Number of groups |
| --- | --- | ---: |
| 30 days | One India calendar day | 30 |
| 90 days | Seven days from the selected period's first day | 13 |
| 12 months (365 days) | Thirty days from the selected period's first day | 13 |

Each group contains blue new-listing and teal enquiry totals, rather than averages. Zero counts stay zero. The final group can be shorter; the current calendar day is incomplete until midnight IST. Hover or keyboard focus shows the exact start/end dates and counts. The current menu supports 30/90/365 days; 120 days is not currently an option.
