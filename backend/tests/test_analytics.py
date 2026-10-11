"""Analytics accuracy, date boundaries and administrator-only access."""
from datetime import datetime, timedelta, timezone
import pytest
from sqlalchemy import delete
from test_portal import client, register, new_listing
from test_accounts import admin
from app import analytics
from app.models import SessionLocal, Property, Inquiry, Favorite, User


@pytest.fixture
def inventory(client, monkeypatch):
    fixed = datetime(2026, 10, 11, 10, tzinfo=timezone.utc)
    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed.astimezone(tz) if tz else fixed.replace(tzinfo=None)
    monkeypatch.setattr(analytics, 'datetime', Clock)
    admin(client)
    with SessionLocal() as db:
        db.execute(delete(Favorite)); db.execute(delete(Inquiry)); db.execute(delete(Property))
        owner = db.query(User).filter(User.role == 'admin').first()
        rows = []
        for city, purpose, price, demo, active, days in [
            ('Hyderabad','sale',4000000,False,True,2),
            ('Hyderabad','sale',12000000,False,True,40),
            ('Pune','rent',20000,False,True,3),
            ('Hyderabad','sale',80000000,True,True,4),
            ('Pune','sale',1000000,False,False,2),
        ]:
            prop = Property(**(new_listing() | {'city':city,'purpose':purpose,'price':price,
                'demo':demo,'active':active,'agent':'','owner_id':owner.id,'created_at':fixed-timedelta(days=days)}))
            db.add(prop); db.flush(); rows.append(prop)
        for index, days in [(0,1),(0,2),(1,40),(2,1),(3,1),(4,1)]:
            db.add(Inquiry(property_id=rows[index].id,user_id=owner.id,message='Private enquiry',phone='9876543210',created_at=fixed-timedelta(days=days)))
        db.add(Favorite(property_id=rows[0].id,user_id=owner.id))
        db.commit()
    return client


def test_analytics_requires_administrator(client):
    assert client.get('/api/admin/analytics').status_code == 401
    register(client)
    assert client.get('/api/admin/analytics').status_code == 403


def test_stock_flow_medians_and_city_rates(inventory):
    response = inventory.get('/api/admin/analytics')
    assert response.status_code == 200
    assert 'no-store' in response.headers['cache-control']
    data = response.json(); s = data['summary']
    assert (s['active'],s['archived'],s['sale'],s['rent']) == (4,1,3,1)
    assert (s['synthetic'],s['owner'],s['median_sale'],s['median_rent']) == (1,3,12000000,20000)
    assert (s['inquiries'],s['previous_inquiries'],s['new_listings'],s['previous_new_listings']) == (5,1,4,1)
    assert (s['without_inquiries'],s['saved_homes']) == (1,1)
    city = {c['city']:c for c in data['cities']}
    assert city['Hyderabad']['per_100'] == 100
    assert city['Pune']['inquiries'] == 2 and city['Pune']['active_inquiries'] == 1
    assert city['Pune']['per_100'] == 100
    assert sum(row['listings'] for row in data['activity']) == s['new_listings']
    assert sum(row['inquiries'] for row in data['activity']) == s['inquiries']
    assert sum(i['count'] for i in data['pricing']['sale']) == s['sale']
    assert sum(i['count'] for i in data['age']) == s['active']
    assert not any(value in response.text for value in ['Private enquiry','9876543210','password_hash','admin@demo.example.com'])


def test_dataset_filter_applies_to_inventory_enquiries_and_saves(inventory):
    owner = inventory.get('/api/admin/analytics?dataset=owner').json()
    synthetic = inventory.get('/api/admin/analytics?dataset=synthetic').json()
    assert owner['summary']['active'] == 3 and owner['summary']['inquiries'] == 4
    assert owner['summary']['median_sale'] == 8000000
    assert synthetic['summary']['active'] == synthetic['summary']['inquiries'] == 1
    assert synthetic['summary']['median_rent'] is None and synthetic['summary']['saved_homes'] == 0
    assert owner['accounts'] == synthetic['accounts']  # Explicit whole-portal scope.


@pytest.mark.parametrize('days,buckets,width',[(30,30,1),(90,13,7),(365,13,30)])
def test_periods_zero_fill_complete_nonoverlapping_buckets(inventory,days,buckets,width):
    data=inventory.get(f'/api/admin/analytics?days={days}').json()
    assert len(data['activity']) == buckets and data['period']['bucket_days'] == width
    assert data['activity'][0]['date'] == data['period']['start']
    assert data['activity'][-1]['end'] == data['period']['end']
    assert sum(row['inquiries'] for row in data['activity']) == data['summary']['inquiries']


def test_ist_midnight_and_current_day_upper_bound(inventory):
    # First selected day starts at 18:30 UTC on the preceding date.
    with SessionLocal() as db:
        prop = db.query(Property).filter(Property.active.is_(True)).first()
        for timestamp in [datetime(2026,9,11,18,29,59,tzinfo=timezone.utc),datetime(2026,9,11,18,30,tzinfo=timezone.utc),datetime(2026,10,11,18,30,tzinfo=timezone.utc)]:
            db.add(Inquiry(property_id=prop.id,user_id=prop.owner_id,message='Boundary',phone='',created_at=timestamp))
        db.commit()
    data=inventory.get('/api/admin/analytics').json()
    assert data['summary']['inquiries']==6 and data['summary']['previous_inquiries']==2
    assert data['activity'][0]['inquiries']==1


def test_empty_inventory_and_archived_only_city(inventory):
    with SessionLocal() as db:
        for prop in db.query(Property): prop.active=False
        db.commit()
    data=inventory.get('/api/admin/analytics').json()
    assert data['summary']['active']==0 and data['summary']['median_sale'] is None
    assert all(c['per_100'] is None for c in data['cities'])
    with SessionLocal() as db:
        db.execute(delete(Favorite));db.execute(delete(Inquiry));db.execute(delete(Property));db.commit()
    data=inventory.get('/api/admin/analytics').json()
    assert data['cities']==[] and data['types']==[] and data['summary']['inquiries']==0
    assert 'No enquiries' in data['signals'][0]['detail']


@pytest.mark.parametrize('query',['days=0','days=999','dataset=live','dataset=owner&days=oops'])
def test_invalid_parameters_rejected(inventory,query):
    assert inventory.get('/api/admin/analytics?'+query).status_code==422


def test_price_buckets_put_thresholds_in_next_band():
    result=analytics.distribution([0,4999999,5000000,10000000,20000000,50000000],
        [5000000,10000000,20000000,50000000],['a','b','c','d','e'])
    assert [r['count'] for r in result]==[2,1,1,1,1]
