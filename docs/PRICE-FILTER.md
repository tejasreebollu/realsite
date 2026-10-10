# Price filters

Updated: 11 October 2026.

The reference screenshots guide the blue/white tabbed layout. RealSite uses Indian rupees and its existing home-loan calculator.

## List Price

A 30-bin histogram represents actual active inventory for the current location, room counts, property type, India More Filters, amenities, agent and map viewport or drawn polygon. It ignores the current price limits so the full distribution remains useful. The right endpoint rounds up to a multiple of INR 50 lakh for sale, or INR 25,000 for rent. It is an open upper bound when the maximum handle reaches the endpoint. Numeric inputs can exceed the chart domain, up to the API's INR 200 crore list-price limit.

Both slider handles support dragging and keyboard arrows. Numeric Min/Max fields synchronise with the handles; only **Apply** updates results. Blank values mean no bound. **Clear** removes the bounds. Maximum must be greater than or equal to minimum; amounts are whole rupees. Empty inventory and chart failures have explicit states, and the numeric fields remain available.

## Monthly Payment

For-sale searches can filter estimated loan EMI, using asking price, down payment percentage, annual interest rate and loan tenure. The default assumptions match the existing calculator: 20 percent down, 8.5 percent annual interest and 20 years. Rates and tenure can be edited; zero interest uses principal divided by months. Taxes, insurance, maintenance, registration, stamp duty and other charges are excluded. This is an estimate, not a lender quote, approval or affordability assessment. The budget link opens the separate working EMI calculator.

The **Credit Score** selector is visibly labelled **demo scenario**. Bands use the 300-900 Indian credit-score scale ([CIBIL FAQ](https://www.cibil.com/faq/understand-your-credit-score-and-report)); no score is retrieved or verified. Each scenario sets an arbitrary planning assumption (8.25 to 10.5 percent), which can be overridden. These preset interest rates are demo values and are not sourced from CIBIL or any lender. Selecting No selection restores the default 8.5 percent assumption.

The API applies the EMI predicate before totals, pagination and map results. Results include rounded `estimated_payment`; inclusion uses the unrounded calculation. Monthly bounds allow INR 0 through INR 2 crore per month; down payment allows 0-90 percent, annual rate 0-25 percent and tenure 5-30 years. The chosen values are kept in the URL, Redis search keys and saved-search JSON. Credit bands are stored as the selected scenario; calculation uses the explicit rate, which may have been edited.

Rental searches offer **Monthly Rent** using asking-rent bounds and the inventory histogram. Home-loan controls are hidden, and changing sale/rent clears both types of price bounds. The backend rejects payment mode for rent and invalid/reversed active ranges. Legacy URLs and saved searches default to list-price mode. No database migration is needed.

## Layout and validation

The panel remains anchored beneath Price, within the viewport. Controls use a compact layout; short screens can scroll the panel while Apply remains accessible. Existing room controls are unchanged.

```powershell
docker compose run --rm --no-deps -e DATABASE_URL=sqlite:////tmp/portal-tests.db api python -m pytest -q -p no:cacheprovider
python scripts/verify_price_filter.py
```

Backend tests cover aggregate bins, filter context, empty/archive behaviour, EMI boundaries, zero interest, financing/cache isolation, list/rental/pagination, invalid inputs and saved searches. Browser checks cover mouse and keyboard sliders, actual INR/EMI results, reload, saved-search restoration, rental switching, the calculator link and six desktop/mobile layouts. Screenshots and metrics are saved under ignored `artifacts/price-*`.

## Combining with a drawn area

Price and financing criteria continue to apply inside a drawn polygon. Removing the boundary restores the original city while retaining the selected price mode and budget. Editing, redrawing and refreshing preserve those choices. See [drawing](DRAW-SEARCH.md) and [release verification](VERIFICATION.md).

## Agent and map context

Directory listing searches use `agent_id`, a stable owner identifier, alongside existing price and area criteria. A hovered result card highlights its price pin with a thin cyan glow. Filtered pins remain visible while drawing; Apply commits the boundary and recalculates results and distribution using the selected budget. Active accounts can save these combined searches. See [user management](USER-MANAGEMENT.md).
