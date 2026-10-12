"""Illustrative Indian resale/rental scenarios, expressed directly in INR.

These are demo assumptions, not live valuations or copied listings. Existing
inventory is repriced only by an explicit command and only if recognisable
original seed facts and amounts still match. Normal seeding never resets edits.
"""
import argparse
import json
import random
from statistics import median
from functools import lru_cache
from sqlalchemy import select
from .models import Property, SessionLocal

# Prior demo model: sale INR/sqft, rent INR/sqft/month, locality adjustments.
# Retained to recognise unchanged existing rows and preserve rental amounts.
PROFILES = {
    'Hyderabad': (5200, 18, [1.10, 1.30, 1.00, 1.25, 1.10, 1.15]),
    'Bengaluru': (6200, 20, [1.00, 1.25, .90, 1.15, 1.10, .95]),
    'Mumbai': (12500, 32, [1.35, 1.10, 1.10, 1.40, 1.30, .95]),
    'Pune': (4800, 16, [1.05, 1.20, .85, 1.00, .90, 1.10]),
    'New Delhi': (6200, 19, [1.20, 1.10, .80, 1.15, 1.25, 1.00]),
}


# User-selected sale demo ranges, in whole rupees (one crore = 10,000,000).
SALE_RANGES = {
    'Hyderabad': (20_000_000, 100_000_000),
    'Mumbai': (50_000_000, 200_000_000),
    'Pune': (30_000_000, 120_000_000),
    'Bengaluru': (30_000_000, 150_000_000),
    'New Delhi': (30_000_000, 150_000_000),
}


def _scenario_amount(city, index, sqft, kind, purpose):
    sale_rate, rent_rate, localities = PROFILES[city]
    variation = random.Random(f'realsite-india-prices-v1:{city}:{index}').uniform(.88, 1.04)
    type_factor = {'Apartment': 1.0, 'Villa': 1.18, 'House': 1.08}[kind]
    return sqft * (rent_rate if purpose == 'rent' else sale_rate) * localities[index % 6] * type_factor * variation


def prior_scenario_price(city, index, sqft, kind, purpose):
    """The previous direct-INR model, for safe upgrades and unchanged rents."""
    step = 500 if purpose == 'rent' else 50000
    return max(step, round(_scenario_amount(city, index, sqft, kind, purpose) / step) * step)


@lru_cache(maxsize=5)
def _sale_score_bounds(city):
    from .seed import CITIES
    scores = [_scenario_amount(city, index, facts['sqft'], facts['kind'], 'sale')
              for _, index, facts in legacy_scenarios(CITIES)
              if facts['city'] == city and facts['purpose'] == 'sale']
    return min(scores), max(scores)


def scenario_price(city, index, sqft, kind, purpose):
    """Stable user-selected sale ranges; rentals retain the prior model exactly."""
    if purpose == 'rent':
        return prior_scenario_price(city, index, sqft, kind, purpose)
    lower, upper = SALE_RANGES[city]
    score = _scenario_amount(city, index, sqft, kind, purpose)
    low_score, high_score = _sale_score_bounds(city)
    fraction = max(0, min(1, (score - low_score) / (high_score - low_score)))
    return max(lower, min(upper, round((lower + fraction * (upper - lower)) / 50000) * 50000))


def legacy_scenarios(cities):
    """Reproduce the old RNG exactly, including archived surplus and coordinates."""
    rng = random.Random(42)
    for city, info in cities.items():
        for index in range(24):
            beds = [3, 4, 2, 3, 4, 2, 3, 5][index % 8]
            sqft = beds * 450 + rng.randrange(100, 600, 50)
            price = rng.randrange(24, 95) * 1000 if index >= 16 else rng.randrange(65, 380) * 100000
            if city == 'Mumbai': price = int(price * 1.7)
            rng.uniform(-.07, .07); rng.uniform(-.07, .07)
            if 12 <= index < 16: continue
            area = info['areas'][index % 6]
            yield f'india-demo-v2:{city}:{index}', index, {
                'city': city, 'price': price, 'sqft': sqft, 'beds': beds,
                'kind': ['Apartment','Villa','House'][index % 3],
                'purpose': 'rent' if index >= 16 else 'sale',
                'title': f"{beds} BHK {['Apartment','Villa','Independent house'][index % 3]} in {area}",
                'address': f'{12 + index}, {area} Road, {area}',
            }


def reprice_existing(db, cities, apply=False):
    original = {key: (index, facts) for key, index, facts in legacy_scenarios(cities)}
    plan, skipped = [], []
    for item in db.scalars(select(Property).where(Property.demo.is_(True), Property.purpose == 'sale', Property.seed_key.in_(list(original)))):
        index, facts = original[item.seed_key]
        if any(getattr(item, key) != value for key, value in facts.items() if key != 'price'):
            skipped.append(item.id)
            continue
        amount = scenario_price(item.city, index, item.sqft, item.kind, item.purpose)
        prior = prior_scenario_price(item.city, index, item.sqft, item.kind, item.purpose)
        if item.price not in (facts['price'], prior, amount) or item.previous_price not in (None, round(item.price * 1.05)):
            skipped.append(item.id)
            continue
        previous = round(amount * 1.05) if item.previous_price is not None else None
        if amount == item.price and previous == item.previous_price: continue
        plan.append({'id': item.id, 'seed_key': item.seed_key, 'city': item.city, 'purpose': item.purpose,
            'before': item.price, 'after': amount, 'previous_before': item.previous_price, 'previous_after': previous})
        if apply:
            item.price, item.previous_price = amount, previous
    if apply: db.commit()
    return {'applied': apply, 'changes': plan, 'skipped_ids': sorted(skipped)}


def main():
    parser = argparse.ArgumentParser(description='Safely reprice unchanged synthetic sale homes; rentals are untouched; defaults to a preview.')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    from .seed import CITIES
    with SessionLocal() as db:
        report = reprice_existing(db, CITIES, apply=args.apply)
        if args.apply and report['changes']:
            from .main import invalidate
            invalidate()
        report['city_after'] = []
        for city in CITIES:
            changes = [row for row in report['changes'] if row['city'] == city]
            report['city_after'].append({'city': city, **{purpose: {'count': len(values), 'min': min(values),
                'median': median(values), 'max': max(values)} if (values := [r['after'] for r in changes if r['purpose'] == purpose]) else None
                for purpose in ('sale','rent')}})
        print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
