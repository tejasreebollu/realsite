# India More Filters

Updated: 11 October 2026.

The supplied images guide a scrollable blue/white dropdown with a grey heading and fixed Reset all filters / Apply actions. Controls filter stored attributes; the panel is not a collection of decorative options.

| Reference control | RealSite India implementation |
| --- | --- |
| Max HOA | Max monthly maintenance in INR; unknown charges do not match a maximum |
| Listing type | Owner / Broker / Builder, plus Resale / New project / Bank auction for sale |
| Listing status | Available / Coming soon / Under offer; archive state remains separate |
| Construction / availability | Ready to move / Under construction; furnishing and ownership |
| Tours / Showcase | Site visit available, 3D tour link, video tour link |
| Garage / parking | Minimum parking spaces and covered parking |
| Square feet / lot size | Built-up and carpet ranges in sqft; plot/attached-land area in sqft, sqyd or acres |
| India plot details | Land use, minimum road width, approval details provided, facing |
| Year / stories / basement | Year-built range, single-storey and basement requirements |
| 55+ communities | Senior living: include all, hide, or only; no age cutoff is assumed |
| Amenities / views | Multiple required amenities; City / Hills / Park / Water views |
| Commute | Map-selected nearby location and radius in kilometres; straight-line distance |
| Listing updates | Actual asking-price reduction, Days on RealSite |
| Keywords / MLS | Title, description, address, approval text or IN-00001 listing reference |

RERA number and approval text are owner supplied; these filters mean details were provided, not that RealSite independently verified them. Bank-auction categories do not implement a bidding or bank integration. The distance control does not provide travel time, traffic or routing. US MLS, HOA terminology, proprietary previews, Showcase and INRIX branding are not reproduced as local integrations.

## Behaviour

- Within listing-source/category/status groups, selected choices use OR. Clearing every checkbox matches no listings; selecting all removes that group's restriction, including listings with unknown metadata.
- Selected amenities must all be present (AND). Selected views match any selected view (OR). Different criteria combine with AND.
- Blank minimum/maximum inputs mean no bound. Numeric ranges are inclusive and reject reversed values. Plot units convert to square feet before querying; changing units clears that range so numbers are not reinterpreted silently.
- Unknown feature values are excluded when a requirement needs a known value. Hide senior living excludes known senior communities and retains unspecified listings.
- Year built and property age are independent of Days on RealSite. Days on RealSite uses the original listing creation timestamp.
- Price reduced compares asking price with the previous price tracked on actual edits. Demo reductions and attributes are synthetic, clearly identified as demo data.
- Nearby distance uses the stored property coordinate and the chosen map pin, computed in SQL before totals and pagination.
- Clear/reset changes the draft; Apply changes the search. Reset all filters clears price, rooms, advanced criteria and a drawn polygon while retaining the sale/rent context and restoring the original city. Escape/backdrop cancels the draft.
- URLs and saved searches restore all criteria. The same predicates filter result lists, map queries and price distributions. Redis keys include the advanced criteria.

## Listing data

Owners use the collapsed optional details section in the existing four-step listing form. Detailed fields appear in property facts; supplied tours open in a separate tab. Unknown values can remain blank. New non-demo listings default to Owner / Available. This is listing information, not an account role; one public account still buys, sells and rents.

The additive migration adds nullable JSON `features` and nullable integer `previous_price`. Existing customer metadata is not fabricated. Stable synthetic rows receive varied attributes only when their feature JSON is absent. Enrichment preserves price, dates, ownership, photos and other original fields, and later restarts preserve edits. The local sample 3D model is illustrative, not a scan or measured tour of the listed address. Demo videos are left absent rather than claiming unavailable footage.

## Verification

```powershell
docker compose run --rm --no-deps -e DATABASE_URL=sqlite:////tmp/portal-tests.db api python -m pytest -q -p no:cacheprovider
python scripts/verify_more_filters.py
python scripts/verify_price_filter.py
```

`tests/conftest.py` forces SQLite before imports and the fixture refuses to reset a non-SQLite database. Browser scripts create their own accounts, remove temporary searches and archive their own test listings. Evidence, backups and screenshots are under ignored `artifacts/`.

## Combining with a drawn area

Advanced requirements continue to filter listings inside the selected polygon. Remove Boundary restores the city searched before drawing and leaves these requirements selected. The nearby-distance pin and a drawn polygon can both apply; nearby distance remains straight-line distance. The price histogram uses the same advanced and area predicates, excluding only active price limits. See [drawing](DRAW-SEARCH.md) and [handoff](HANDOFF.md).

## Agent profiles and visible map pins

The listing-source value (Owner / Broker / Builder) describes the listing and is separate from approved agent account status. The public agent directory contains only approved active profiles; its View listings action uses a stable owner ID, which combines with all other search criteria. See [user management](USER-MANAGEMENT.md).

Current filtered pins stay visible while drafting a boundary. Hovering a result card adds a thin cyan border and soft glow to its pin; the draft does not change matching inventory until Apply.
