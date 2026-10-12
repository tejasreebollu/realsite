"""Demo-only price upgrades must preserve owner edits and stored relationships."""
import pytest
from sqlalchemy import select
from test_portal import client, register, new_listing
from app.models import SessionLocal, Property
from app.seed import seed, CITIES
from app.demo_pricing import legacy_scenarios, reprice_existing, scenario_price, prior_scenario_price, SALE_RANGES


def record(item):
    return {column.name: getattr(item, column.name) for column in Property.__table__.columns}


def old_amounts(db):
    original = {key: facts for key, _, facts in legacy_scenarios(CITIES)}
    for item in db.scalars(select(Property).where(Property.demo.is_(True))):
        facts = original[item.seed_key]
        item.price = facts['price']
        if item.previous_price is not None: item.previous_price = round(item.price * 1.05)
    db.commit()


def test_fresh_seed_uses_direct_inr_scenarios_with_stable_facts(client):
    with SessionLocal() as db:
        rows = db.scalars(select(Property)).all()
        assert len(rows) == 100
        original = {key: (i, facts) for key, i, facts in legacy_scenarios(CITIES)}
        for item in rows:
            index, facts = original[item.seed_key]
            assert all(getattr(item,k)==v for k,v in facts.items() if k != 'price')
            assert item.price == scenario_price(item.city,index,item.sqft,item.kind,item.purpose)
            assert item.price % (500 if item.purpose == 'rent' else 50000) == 0
            assert 10000 <= item.price <= 200000 if item.purpose == 'rent' else SALE_RANGES[item.city][0] <= item.price <= SALE_RANGES[item.city][1]
        before = {p.id:record(p) for p in rows}
        seed(db);seed(db)
        assert {p.id:record(p) for p in db.scalars(select(Property))} == before


def test_prices_correlate_with_size_type_and_city():
    for city in CITIES:
        for purpose in ('sale','rent'):
            small = scenario_price(city,0,900,'Apartment',purpose)
            large = scenario_price(city,0,1800,'Apartment',purpose)
            villa = scenario_price(city,0,1800,'Villa',purpose)
            assert small < large < villa
    assert scenario_price('Mumbai',0,1200,'Apartment','sale') > scenario_price('Hyderabad',0,1200,'Apartment','sale')
    assert scenario_price('Mumbai',0,1200,'Apartment','rent') > scenario_price('Pune',0,1200,'Apartment','rent')


def test_preview_apply_and_repeat_preserve_manual_edits_and_nonprice_fields(client):
    register(client)
    manual = client.post('/api/properties',json=new_listing()).json()
    with SessionLocal() as db:
        old_amounts(db)
        homes = db.scalars(select(Property).where(Property.demo.is_(True)).order_by(Property.id)).all()
        baseline={r['id'] for r in reprice_existing(db,CITIES)['changes']}
        homes[0].price=8765432
        homes[1].previous_price=99999999
        homes[2].active=False
        db.commit()
        before={p.id:record(p) for p in db.scalars(select(Property))}
        preview=reprice_existing(db,CITIES)
        assert {r['id'] for r in preview['changes']}==baseline-{homes[0].id,homes[1].id}
        assert preview['skipped_ids']==sorted([homes[0].id,homes[1].id])
        assert {p.id:record(p) for p in db.scalars(select(Property))}==before
        applied=reprice_existing(db,CITIES,apply=True)
        assert applied['changes']==preview['changes']
        after={p.id:record(p) for p in db.scalars(select(Property))}
        changed={p['id'] for p in applied['changes']}
        for id, previous in before.items():
            if id in changed:
                assert {k for k in previous if previous[k]!=after[id][k]} <= {'price','previous_price'}
            else: assert after[id]==previous
        assert after[manual['id']]==before[manual['id']]
        assert not db.get(Property,homes[2].id).active
        assert reprice_existing(db,CITIES,apply=True)['changes']==[]
        seed(db);assert {p.id:record(p) for p in db.scalars(select(Property))}==after


def test_customized_core_facts_are_never_repriced(client):
    with SessionLocal() as db:
        old_amounts(db)
        homes=db.scalars(select(Property).order_by(Property.id)).all()
        baseline={r['id'] for r in reprice_existing(db,CITIES)['changes']}
        homes[0].title='Owner custom title'
        homes[1].sqft+=100
        homes[2].demo=False
        homes[3].seed_key='custom-demo:untouched'
        db.commit()
        before={p.id:record(p) for p in homes[:4]}
        assert {r['id'] for r in reprice_existing(db,CITIES,apply=True)['changes']}==baseline-{p.id for p in homes[:4]}
        assert {id:record(db.get(Property,id)) for id in before}==before


@pytest.mark.parametrize('city', ['Hyderabad', 'Mumbai', 'Pune', 'Bengaluru', 'New Delhi'])
def test_each_city_sale_inventory_spans_requested_range(city):
    originals = [(index, facts) for _, index, facts in legacy_scenarios(CITIES) if facts['city'] == city]
    prices = [scenario_price(city, index, facts['sqft'], facts['kind'], 'sale')
              for index, facts in originals if facts['purpose'] == 'sale']
    assert len(prices) == 12
    assert (min(prices), max(prices)) == SALE_RANGES[city]
    assert len(set(prices)) >= 10
    for index, facts in originals:
        if facts['purpose'] == 'rent':
            assert scenario_price(city, index, facts['sqft'], facts['kind'], 'rent') == prior_scenario_price(city, index, facts['sqft'], facts['kind'], 'rent')


def test_prior_inr_sale_upgrade_preserves_all_rentals_and_is_idempotent(client):
    originals = {key: index for key, index, _ in legacy_scenarios(CITIES)}
    with SessionLocal() as db:
        for item in db.scalars(select(Property)):
            item.price = prior_scenario_price(item.city, originals[item.seed_key], item.sqft, item.kind, item.purpose)
            if item.previous_price is not None:
                item.previous_price = round(item.price * 1.05)
        db.commit()
        before = {p.id: record(p) for p in db.scalars(select(Property))}
        preview = reprice_existing(db, CITIES)
        assert len(preview['changes']) == 60
        assert all(r['purpose'] == 'sale' for r in preview['changes'])
        assert {p.id: record(p) for p in db.scalars(select(Property))} == before
        applied = reprice_existing(db, CITIES, apply=True)
        assert applied['changes'] == preview['changes']
        for item in db.scalars(select(Property)):
            old = before[item.id]
            if item.purpose == 'rent':
                assert record(item) == old
            else:
                assert {k for k, v in record(item).items() if v != old[k]} <= {'price', 'previous_price'}
                assert SALE_RANGES[item.city][0] <= item.price <= SALE_RANGES[item.city][1]
                if item.previous_price is not None:
                    assert item.previous_price == round(item.price * 1.05)
        assert reprice_existing(db, CITIES, apply=True)['changes'] == []
