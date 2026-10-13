"""Advanced India filters over known, unknown and legacy listing metadata."""
import os
os.environ["DATABASE_URL"] = "sqlite:////tmp/portal-tests.db"
from datetime import datetime, timedelta, timezone
import pytest
from sqlalchemy import select
from app.models import Property, SessionLocal
from app.seed import seed
from test_portal import client, register, new_listing

@pytest.fixture
def advanced_inventory(client):
    register(client)
    profiles = [
        {'posted_by':'Owner','listing_status':'Available','sale_type':'Resale','possession':'Ready to move','ownership':'Freehold','maintenance':1000,'parking':2,'covered_parking':True,'carpet_sqft':900,'plot_sqft':1800,'year_built':2015,'floors':1,'basement':True,'senior_living':False,'facing':'East','views':['City','Park'],'site_visit':True,'tour_3d_url':'/tours/demo-3d.html','video_url':'https://example.com/tour','rera_id':'DEMO-001'},
        {'posted_by':'Broker','listing_status':'Coming soon','sale_type':'New project','possession':'Under construction','ownership':'Leasehold','maintenance':5000,'parking':1,'covered_parking':False,'carpet_sqft':1800,'year_built':2025,'floors':4,'basement':False,'senior_living':True,'views':['Water']},
        {'posted_by':'Builder','listing_status':'Under offer','sale_type':'Bank auction','possession':'Ready to move','parking':0,'carpet_sqft':1500,'year_built':2005,'floors':2,'views':['Hills']},
        {},
    ]
    ids=[]
    for i, features in enumerate(profiles):
        body = new_listing() | {'city':'Advanced Filter Test','features':features,'price':10_000_000*(i+1),'sqft':[1200,2400,2000,1100][i], 'lat':[17.44,17.46,17.6,17.8][i], 'furnishing':['Furnished','Semi-furnished','Unfurnished','Unfurnished'][i], 'amenities':['Swimming pool','Gym','Lift'] if i==0 else ['Swimming pool']}
        response=client.post('/api/properties',json=body)
        assert response.status_code==201,response.text
        ids.append(response.json()['id'])
    plot = new_listing() | {'city':'Advanced Filter Test','kind':'Open Plot','beds':0,'baths':0,'sqft':1800,'area_value':200,'area_unit':'sqyd','plot_facing':'East','plot_use':'Residential','plot_approval':'DEMO authority','road_width_ft':40,'features':{'posted_by':'Owner','maintenance':0}, 'lat':17.5}
    response=client.post('/api/properties',json=plot)
    assert response.status_code==201,response.text
    ids.append(response.json()['id'])
    with SessionLocal() as db:
        db.get(Property,ids[3]).features=None
        db.get(Property,ids[3]).created_at=datetime.now(timezone.utc)-timedelta(days=70)
        db.commit()
    return client,ids

@pytest.mark.parametrize('filters,indexes', [
    ({'posted_by':'Owner'},[0,4]), ({'posted_by':'Owner,Broker'},[0,1,4]), ({'posted_by':'none'},[]),
    ({'sale_type':'New project'},[1]), ({'sale_type':'Bank auction'},[2]), ({'listing_status':'Coming soon'},[1]),
    ({'possession':'Under construction'},[1]), ({'furnishing_filter':'Furnished'},[0]), ({'ownership':'Leasehold'},[1]),
    ({'max_maintenance':0},[4]), ({'max_maintenance':2000},[0,4]), ({'min_parking':2,'covered_parking':True},[0]),
    ({'max_sqft':1500},[0,3]), ({'min_carpet':800,'max_carpet':1000},[0]),
    ({'min_plot':190,'max_plot':210,'plot_unit':'sqyd'},[0,4]), ({'min_plot':0.04,'max_plot':0.05,'plot_unit':'acre'},[0,4]),
    ({'year_min':2010,'year_max':2020},[0]), ({'basement':True,'single_storey':True},[0]),
    ({'senior_living':'only'},[1]), ({'senior_living':'exclude'},[0,2,3,4]),
    ({'amenities_all':'Swimming pool,Gym'},[0]), ({'views':'Park,Water'},[0,1]), ({'facing':'East'},[0,4]),
    ({'rera_only':True,'site_visit':True,'tour_3d':True,'video_tour':True},[0]),
    ({'plot_use_filter':'Residential'},[4]), ({'approval_only':True},[4]), ({'min_road_width':40},[4]),
    ({'radius_lat':17.44,'radius_lng':78.39,'radius_km':1},[0]), ({'days_listed':30},[0,1,2,4]),
])
def test_filter_predicates_and_cache(advanced_inventory,filters,indexes):
    client,ids=advanced_inventory
    params={'q':'Advanced Filter Test'}|filters
    for _ in range(2):
        response=client.get('/api/properties',params=params)
        assert response.status_code==200,response.text
        assert [p['id'] for p in response.json()['items']]==[ids[i] for i in indexes]
        assert response.json()['total']==len(indexes)
    distribution=client.get('/api/properties/price-distribution',params=params)
    assert distribution.status_code==200,distribution.text
    assert distribution.json()['total']==sum(distribution.json()['counts'])==len(indexes)


def test_combined_filters_saved_search_and_keywords(advanced_inventory):
    client,ids=advanced_inventory
    filters={'q':'Advanced Filter Test','posted_by':'Owner','amenities_all':'Swimming pool,Gym','year_min':2010,'year_max':2020,'min_price':5_000_000,'max_price':11_000_000,'rera_only':True,'sort':'price_asc'}
    assert client.get('/api/properties',params=filters|{'page_size':1}).json()['total']==1
    saved=client.post('/api/saved-searches',json={'name':'India filters','filters':filters})
    assert saved.status_code==201,saved.text
    restored={k:v for k,v in saved.json()['filters'].items() if v is not None and v!=''}
    assert client.get('/api/properties',params=restored).json()['items'][0]['id']==ids[0]
    assert client.get('/api/properties',params={'q':'Advanced Filter Test','keywords':f'IN-{ids[1]:05}'}).json()['items'][0]['id']==ids[1]
    assert client.get('/api/properties',params={'q':'Advanced Filter Test','keywords':'%'}).json()['total']==0
    assert client.get('/api/properties',params={'q':'Advanced Filter Test','keywords':'bright'}).json()['total']==5


def test_metadata_updates_reductions_unknown_and_rent(advanced_inventory):
    client,ids=advanced_inventory
    original=client.get(f'/api/properties/{ids[0]}').json()
    legacy=new_listing()|{k:original[k] for k in new_listing()}
    legacy['price']=9_000_000
    changed=client.put(f'/api/properties/{ids[0]}',json=legacy)
    assert changed.status_code==200,changed.text
    assert changed.json()['features']==original['features']
    assert changed.json()['previous_price']==10_000_000
    assert client.get('/api/properties',params={'q':'Advanced Filter Test','price_reduced':True}).json()['items'][0]['id']==ids[0]
    legacy['price']=11_000_000
    assert client.put(f'/api/properties/{ids[0]}',json=legacy).status_code==200
    assert client.get('/api/properties',params={'q':'Advanced Filter Test','price_reduced':True}).json()['total']==0
    rental=new_listing()|{'city':'Advanced Filter Test','purpose':'rent','furnishing':'Furnished','features':{'maintenance':1500,'parking':1}}
    assert client.post('/api/properties',json=rental).status_code==201
    assert client.get('/api/properties',params={'q':'Advanced Filter Test','purpose':'rent','max_maintenance':2000,'furnishing_filter':'Furnished','min_parking':1}).json()['total']==1
    assert client.get(f'/api/properties/{ids[3]}').json()['features']=={}

@pytest.mark.parametrize('invalid', [
    {'posted_by':'Hacker'}, {'sale_type':'Foreclosure'}, {'views':'Ocean'}, {'amenities_all':'Bad'},
    {'max_sqft':100,'min_sqft':200}, {'min_carpet':200,'max_carpet':100}, {'year_min':2020,'year_max':2000},
    {'min_plot':2,'max_plot':1}, {'radius_km':5}, {'radius_lat':90}, {'days_listed':366}, {'year_min':1700},
])
def test_invalid_advanced_criteria(client,invalid):
    for route in ['/api/properties','/api/properties/price-distribution']:
        response=client.get(route,params=invalid)
        assert response.status_code==422,response.text
    register(client)
    assert client.post('/api/saved-searches',json={'name':'Invalid','filters':invalid}).status_code==422


def test_metadata_validation_and_demo_enrichment_repeatability(client):
    register(client)
    for features in [{'tour_3d_url':'javascript:alert(1)'},{'video_url':'http://example.com'},{'parking':-1},{'carpet_sqft':9999999},{'posted_by':'unknown'},{'views':['Sea']},{'extra':True}]:
        assert client.post('/api/properties',json=new_listing()|{'features':features}).status_code==422
    with SessionLocal() as db:
        first=db.scalar(select(Property).where(Property.seed_key=='india-demo-v2:Hyderabad:0'))
        assert first.features['posted_by']=='Owner'
        first.features=first.features|{'maintenance':9876}
        first.price=12345678
        db.commit()
        seed(db)
        assert first.features['maintenance']==9876 and first.price==12345678
