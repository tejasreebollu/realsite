"""Drawn-area predicates must filter before pagination and preserve saved criteria."""
import json
import pytest
from sqlalchemy import select
from app import main
from app.models import Property, SessionLocal
from test_portal import client, register
from app.map_boundary import parse_boundary

RECT=[[17.42,78.37],[17.46,78.37],[17.46,78.41],[17.42,78.41]]

def locate(items):
    with SessionLocal() as db:
        for p in db.scalars(select(Property)).all():
            p.active=False
        for i,(lat,lng,purpose,price) in enumerate(items):
            db.add(Property(title=f'Drawn property {i}',address='Test Road',city='Hyderabad',state='Telangana',pincode='500032',price=price,beds=2,baths=2,sqft=1000,kind='Apartment',purpose=purpose,lat=lat,lng=lng,images=['/images/home-1.jpg'],amenities=['Parking'],description='A synthetic listing for isolated map search tests.',owner_id=1,agent='Test Owner',features={'posted_by':'Owner'}))
        db.commit()

def test_polygon_applied_before_counts_pages_histogram_and_other_filters(client):
    locate([(17.44,78.39,'sale',1000000),(17.43,78.40,'sale',2000000),(17.42,78.39,'sale',3000000),(17.46,78.41,'sale',4000000),(17.45,78.42,'sale',5000000),(17.44,78.39,'rent',25000)])
    params={'polygon':json.dumps(RECT),'page_size':2}
    first=client.get('/api/properties',params=params).json()
    second=client.get('/api/properties',params=params|{'page':2}).json()
    assert first['total']==second['total']==4
    assert len({p['id'] for p in first['items']+second['items']})==4
    assert client.get('/api/properties',params=params|{'max_price':1500000,'posted_by':'Owner'}).json()['total']==1
    assert client.get('/api/properties',params=params|{'purpose':'rent'}).json()['total']==1
    chart=client.get('/api/properties/price-distribution',params=params).json()
    assert chart['total']==sum(chart['counts'])==4
    # Shape participates in the cache key, including an empty-result area.
    far=json.dumps([[20,80],[21,80],[21,81],[20,81]])
    assert client.get('/api/properties',params={'polygon':far}).json()['total']==0
    assert client.get('/api/properties',params=params).json()['total']==4
    assert client.get('/api/properties').json()['total']==5

@pytest.mark.parametrize('reverse',[False,True])
def test_concave_polygon_excludes_notch_and_includes_edges(client,reverse):
    polygon=[[17,78],[17,79],[18,79],[18,78.5],[19,78.5],[19,78]]
    locate([(17.5,78.8,'sale',1000000),(18.5,78.3,'sale',1000000),(18.5,78.8,'sale',1000000),(18.5,78.5,'sale',1000000)])
    if reverse:polygon.reverse()
    response=client.get('/api/properties',params={'polygon':json.dumps(polygon)})
    assert response.status_code==200,response.text
    assert response.json()['total']==3

@pytest.mark.parametrize('value',[
    'bad','{}','[]','[[17,78],[18,79]]','[[17,78],[18,79],[19,80]]',
    '[[17,78],[18,79],[17,79],[18,78]]',
    '[[17,78],[18,79],[17,78],[18,78]]',
    '[[true,78],[18,79],[18,78]]',
    '[[NaN,78],[18,79],[18,78]]',
    '[[91,78],[18,79],[18,78]]',
    '[[17,181],[18,79],[18,78]]',
    '[[17,78,1],[18,79],[18,78]]',
    json.dumps([[17+i*.001,78+i*.002] for i in range(66)]),
    'x'*3001,
])
def test_invalid_boundary_rejected(client,value):
    assert client.get('/api/properties',params={'polygon':value}).status_code==422
    assert client.get('/api/properties/price-distribution',params={'polygon':value}).status_code==422

def test_closed_polygon_and_saved_search_validation(client):
    assert parse_boundary(json.dumps(RECT+[RECT[0]]))==parse_boundary(json.dumps(RECT))
    register(client)
    shape=json.dumps(RECT,separators=(',',':'))
    saved=client.post('/api/saved-searches',json={'name':'My map area','filters':{'q':'','polygon':shape,'boundary_q':'Hyderabad','beds':2}})
    assert saved.status_code==201,saved.text
    stored=client.get('/api/saved-searches').json()[0]['filters']
    assert stored['polygon']==shape
    assert stored['boundary_q']=='Hyderabad'
    assert stored['q']==''
    assert client.post('/api/saved-searches',json={'name':'Invalid','filters':{'polygon':'bad'}}).status_code==422


def test_boundary_return_location_does_not_constrain_search(client):
    locate([(17.44,78.39,'sale',1000000),(17.43,78.40,'sale',2000000)])
    params={'polygon':json.dumps(RECT),'boundary_q':'Mumbai'}
    # A shape can extend beyond the original text location.
    result=client.get('/api/properties',params=params)
    assert result.status_code==200,result.text
    assert result.json()['total']==2
    assert client.get('/api/properties/price-distribution',params=params).json()['total']==2
    assert client.get('/api/properties',params=params|{'boundary_q':'x'*151}).status_code==422
