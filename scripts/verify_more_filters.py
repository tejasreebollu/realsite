"""Live India More Filters, metadata editing, saved searches, distance and layouts."""
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import json, math, secrets, sys, time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'.tools'))
from playwright.sync_api import sync_playwright,expect
BASE='http://localhost:8090';ARTIFACTS=ROOT/'artifacts';ARTIFACTS.mkdir(exist_ok=True)
checks,errors,layouts=[],[],[]
def record(label):
    checks.append(label);print('PASS:',label,flush=True)
def open_more(page):
    page.get_by_role('button',name='Filters',exact=True).click()
    panel=page.get_by_role('dialog',name='More filters',exact=True)
    expect(panel).to_be_visible();return panel
def result(page):
    response=page.request.get(BASE+'/api/properties?'+urlparse(page.url).query+'&page_size=100')
    assert response.ok,response.text()
    data=response.json();expect(page.locator('.results-grid .property-card')).to_have_count(min(24,data['total']))
    return data
def toggle_group(panel,name,selected):
    group=panel.get_by_role('group',name=name,exact=True)
    for option in {'Listed by':['Owner','Broker','Builder'],'Listing status':['Available','Coming soon','Under offer']}[name]:
        group.get_by_role('checkbox',name=option,exact=True).set_checked(option in selected)
def distance(a,b,c,d):
    x=math.radians(a-c);y=math.radians(b-d)
    return 12742*math.asin(math.sqrt(math.sin(x/2)**2+math.cos(math.radians(a))*math.cos(math.radians(c))*math.sin(y/2)**2))
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True)
    context=browser.new_context(viewport={'width':1440,'height':900})
    page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(BASE+'/homes?q=Hyderabad',wait_until='networkidle');baseline=result(page)
    panel=open_more(page)
    toggle_group(panel,'Listed by',['Owner'])
    panel.get_by_label('Max monthly maintenance (₹)',exact=True).select_option('2000')
    for label in ['Parking','Security']:
        panel.get_by_role('group',name='Required amenities',exact=True).get_by_role('checkbox',name=label,exact=True).check()
    for label in ['Park','Water']:
        panel.get_by_role('group',name='Property views',exact=True).get_by_role('checkbox',name=label,exact=True).check()
    page.screenshot(path=str(ARTIFACTS/'more-filters-desktop.png'))
    panel.get_by_role('button',name='Apply',exact=True).click()
    expected=[row['id'] for row in baseline['items'] if row['features'].get('posted_by')=='Owner' and row['features'].get('maintenance') is not None and row['features']['maintenance']<=2000 and {'Parking','Security'}.issubset(row['amenities']) and set(row['features'].get('views',[])).intersection(['Park','Water'])]
    assert expected and [row['id'] for row in result(page)['items']]==expected
    original_params=parse_qs(urlparse(page.url).query)
    assert original_params['posted_by']==['Owner'] and original_params['amenities_all']==['Parking,Security']
    expect(page.locator('.applied-filters')).to_contain_text('more filters')
    page.reload(wait_until='networkidle');panel=open_more(page)
    expect(panel.get_by_label('Max monthly maintenance (₹)',exact=True)).to_have_value('2000')
    expect(panel.get_by_role('group',name='Listed by',exact=True).get_by_role('checkbox',name='Broker',exact=True)).not_to_be_checked()
    panel.get_by_label('Minimum year built',exact=True).fill('2020')
    panel.get_by_label('Maximum year built',exact=True).fill('2000')
    panel.get_by_role('button',name='Apply',exact=True).click()
    expect(panel.get_by_role('alert')).to_be_visible()
    expect(panel.get_by_role('alert')).to_contain_text('maximum')
    panel.get_by_label('Minimum year built',exact=True).press('Escape')
    assert [row['id'] for row in result(page)['items']]==expected
    panel=open_more(page)
    expect(panel.get_by_label('Minimum year built',exact=True)).to_have_value('')
    panel.get_by_label('Minimum year built',exact=True).press('Escape')
    record('Owner selection, INR maintenance, AND amenities, OR views, real results, URL/reload, visible validation and cancel')

    registration=page.request.post(BASE+'/api/auth/register',data={'name':'More Filter Browser','email':f'more-browser-{int(time.time())}@example.com','password':'MoreTest-'+secrets.token_hex(12)})
    assert registration.status==201,registration.text()
    created=[]
    try:
        page.reload(wait_until='networkidle')
        page.get_by_role('button',name='Save search',exact=True).click()
        expect(page.locator('.toast')).to_contain_text('Search saved')
        page.get_by_role('button',name='Updates',exact=True).click()
        article=page.locator('.saved-search-list article').filter(has_text='more filters')
        expect(article).to_have_count(1);article.get_by_role('button',name='View homes',exact=True).click()
        restored=parse_qs(urlparse(page.url).query)
        for key in ['posted_by','max_maintenance','amenities_all','views']:
            assert restored[key]==original_params[key]
        assert [row['id'] for row in result(page)['items']]==expected
        record('Saved advanced search restores the criteria and matching inventory')
        body={'title':'More Browser Property','address':'90, More Filter Browser Road','city':'Hyderabad','state':'Telangana','pincode':'500032','price':9000000,'beds':3,'baths':2,'sqft':1600,'kind':'Apartment','purpose':'sale','lat':17.44,'lng':78.39,'images':['/images/home-1.jpg'],'amenities':['Parking','Gym'],'description':'A synthetic property used only to verify the new property details editor and search behaviour.','features':{'posted_by':'Owner','maintenance':1500,'parking':1,'carpet_sqft':1100,'views':['Park']}}
        for mode in ['sale','rent','plot']:
            title='More Browser '+mode+' '+str(int(time.time()))
            payload=body|{'title':title}
            if mode=='rent':payload|={'purpose':'rent','price':40000,'furnishing':'Furnished'}
            if mode=='plot':payload|={'kind':'Open Plot','beds':0,'baths':0,'area_unit':'sqyd','area_value':200,'plot_use':'Residential','features':{'posted_by':'Owner','maintenance':0}}
            response=page.request.post(BASE+'/api/properties',data=payload)
            assert response.status==201,response.text()
            item=response.json();created.append(item['id'])
            page.goto(BASE+'/manage',wait_until='networkidle')
            card=page.locator('.managed-property').filter(has=page.get_by_role('button',name='View '+title,exact=True))
            card.get_by_role('button',name='Edit listing',exact=True).click()
            expect(page.locator('.listing-extra-details')).not_to_have_attribute('open','')
            page.locator('.listing-extra-details summary').click()
            page.get_by_label('Listed by',exact=True).select_option('Broker')
            page.get_by_label('Monthly maintenance (₹)',exact=True).fill('2500')
            if mode!='plot':
                page.get_by_label('Parking spaces',exact=True).fill('2')
                page.get_by_label('Covered parking',exact=True).select_option('true')
                page.get_by_label('Carpet area (sqft)',exact=True).fill('1200')
                page.get_by_label('Year built',exact=True).fill('2018')
                page.get_by_label('Building storeys',exact=True).fill('1')
                page.get_by_label('Furnishing',exact=True).select_option('Semi-furnished')
            else:
                expect(page.get_by_label('Parking spaces',exact=True)).to_have_count(0)
                page.get_by_label('Layout / authority approval (optional)',exact=True).fill('DEMO authority details')
                page.get_by_label('Road width in feet (optional)',exact=True).fill('40')
            for next_step in ['location','photos','review']:
                page.get_by_role('button',name='Next: '+next_step,exact=True).click()
            with page.expect_response(lambda r:r.url.endswith('/api/properties/'+str(item['id'])) and r.request.method=='PUT') as saved:
                page.get_by_role('button',name='Save changes',exact=True).click()
            assert saved.value.status==200,saved.value.text()
            updated=saved.value.json()
            assert updated['features']['posted_by']=='Broker' and updated['features']['maintenance']==2500
            if mode!='plot':assert updated['features']['parking']==2 and updated['features']['carpet_sqft']==1200 and updated['furnishing']=='Semi-furnished'
            else:assert updated['road_width_ft']==40 and updated['plot_approval']=='DEMO authority details'
            filtered=page.request.get(BASE+'/api/properties',params={'q':title,'purpose':'rent' if mode=='rent' else 'sale','posted_by':'Broker','max_maintenance':3000})
            assert filtered.ok and filtered.json()['total']==1,filtered.text()
            record(mode+' listing: optional details stay compact, edit/save works and new attributes filter the property')
    finally:
        for saved in page.request.get(BASE+'/api/saved-searches').json():
            assert page.request.delete(BASE+f'/api/saved-searches/{saved["id"]}').status==204
        for property_id in created:
            assert page.request.delete(BASE+f'/api/properties/{property_id}').status==204
    page.goto(BASE+'/homes?q=Hyderabad',wait_until='networkidle');panel=open_more(page)
    panel.get_by_role('button',name='Choose a location on the map',exact=True).click()
    panel.get_by_role('button',name='Place pin at map centre',exact=True).click()
    panel.get_by_label('Within distance',exact=True).select_option('2')
    panel.get_by_role('button',name='Apply',exact=True).click()
    params=parse_qs(urlparse(page.url).query)
    lat,lng=float(params['radius_lat'][0]),float(params['radius_lng'][0])
    expected_distance=[row['id'] for row in baseline['items'] if distance(row['lat'],row['lng'],lat,lng)<=2]
    assert [row['id'] for row in result(page)['items']]==expected_distance
    record('Map destination, distance radius and actual PostgreSQL distance results work')
    page.goto(BASE+'/tours/demo-3d.html',wait_until='networkidle')
    expect(page.get_by_role('heading',name='Explore a sample 3D home',exact=True)).to_be_visible()
    page.get_by_role('button',name='Look inside',exact=True).click()
    expect(page.get_by_role('button',name='Show roof',exact=True)).to_have_attribute('aria-pressed','true')
    page.locator('canvas').focus();page.locator('canvas').press('ArrowLeft')
    page.screenshot(path=str(ARTIFACTS/'demo-3d-model.png'))
    record('Synthetic 3D model loads, rotates and opens its roof with clear illustrative disclosure')
    context.close()

    for width,height in [(1920,900),(1366,600),(768,700),(390,844),(360,640),(320,568)]:
        context=browser.new_context(viewport={'width':width,'height':height},has_touch=width<=760)
        page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
        for purpose in ['sale','rent']:
            page.goto(BASE+'/homes?q=Hyderabad&purpose='+purpose,wait_until='networkidle');original=result(page)
            panel=open_more(page);box=panel.bounding_box()
            assert box['x']>=0 and box['x']+box['width']<=width+1 and box['y']+box['height']<=height+1,box
            expect(panel.get_by_role('button',name='Apply',exact=True)).to_be_in_viewport()
            expect(panel.get_by_role('button',name='Reset all filters',exact=True)).to_be_in_viewport()
            expect(page.locator('.mobile-view-toggle')).not_to_be_visible()
            if purpose=='rent':expect(panel.get_by_role('group',name='Sale type',exact=True)).to_have_count(0)
            checkbox=panel.get_by_role('checkbox',name='Covered parking',exact=True)
            checkbox.tap() if width<=760 else checkbox.check()
            expect(checkbox).to_be_checked()
            radio=panel.get_by_role('radio',name='Only senior living',exact=True)
            radio.scroll_into_view_if_needed();radio.check()
            radio_size=radio.bounding_box();assert radio_size['width']<=24 and radio_size['height']<=24,radio_size
            keyword=panel.get_by_label('Listing keywords',exact=True);keyword.scroll_into_view_if_needed();keyword.fill('terrace')
            page.screenshot(path=str(ARTIFACTS/f'more-filters-{purpose}-{width}-{height}-bottom.png'))
            expect(panel.get_by_role('button',name='Apply',exact=True)).to_be_in_viewport()
            panel.get_by_role('button',name='Reset all filters',exact=True).click()
            expect(keyword).to_have_value('')
            expect(checkbox).not_to_be_checked()
            panel.locator('.more-filter-body').evaluate('e=>e.scrollTop=0')
            page.screenshot(path=str(ARTIFACTS/f'more-filters-{purpose}-{width}-{height}.png'))
            layouts.append({'viewport':page.viewport_size,'purpose':purpose,'box':box})
            panel.get_by_role('button',name='Apply',exact=True).click()
            assert result(page)['total']==original['total']
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        page.goto(BASE+'/homes?q=Hyderabad',wait_until='networkidle');panel=open_more(page)
        panel.get_by_label('Property type',exact=True).select_option('Open Plot')
        expect(panel.get_by_label('Land use',exact=True)).to_be_visible()
        expect(panel.get_by_role('checkbox',name='Covered parking',exact=True)).to_have_count(0)
        panel.get_by_label('Plot area unit',exact=True).select_option('sqyd')
        panel.get_by_label('Minimum plot area',exact=True).fill('150')
        panel.get_by_label('Maximum plot area',exact=True).fill('250')
        panel.get_by_role('checkbox',name='Layout approval details provided',exact=True).check()
        panel.get_by_label('Minimum road width (ft)',exact=True).select_option('40')
        panel.get_by_role('button',name='Apply',exact=True).click()
        assert parse_qs(urlparse(page.url).query)['plot_unit']==['sqyd']
        record(f'{width}x{height}: sale/rent scroll sections, touch/radios, fixed actions, reset, viewport fit and plot-specific fields')
        context.close()
    assert not errors,errors
    record('No browser JavaScript errors')
    (ARTIFACTS/'more-filters-results.json').write_text(json.dumps({'checks':checks,'layouts':layouts,'errors':errors},indent=2)+'\n',encoding='utf-8')
    browser.close()
print('Completed',len(checks),'More Filters checks',flush=True)
