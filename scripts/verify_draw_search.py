"""Live map drawing, PostgreSQL geometry, persistence and responsive UI checks."""
from pathlib import Path
from urllib.parse import urlparse,parse_qs,urlencode
import json,sys,time,secrets,math
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'.tools'))
from playwright.sync_api import sync_playwright,expect
BASE='http://localhost:8090';ARTIFACTS=ROOT/'artifacts';ARTIFACTS.mkdir(exist_ok=True)
checks=[];errors=[]
def record(label):
    checks.append(label);print('PASS:',label,flush=True)
def inside(point,polygon):
    y,x=point;odd=False
    for a,b in zip(polygon,polygon[1:]+polygon[:1]):
        y1,x1=a;y2,x2=b
        det=(x2-x1)*(y-y1)-(y2-y1)*(x-x1)
        if abs(det)<=1e-10 and min(y1,y2)-1e-10<=y<=max(y1,y2)+1e-10 and min(x1,x2)-1e-10<=x<=max(x1,x2)+1e-10:return True
        if (y1>y)!=(y2>y) and x<x1+(y-y1)*(x2-x1)/(y2-y1):odd=not odd
    return odd
def marker_snapshot(pg):
    markers=pg.locator('.map-pane .price-marker')
    assert markers.count()>0, 'The filtered search needs property markers'
    state=markers.evaluate_all("els=>els.map(el=>({text:el.textContent,visibility:getComputedStyle(el).visibility,display:getComputedStyle(el).display,opacity:getComputedStyle(el).opacity,pointer:getComputedStyle(el).pointerEvents}))")
    assert all(m['visibility']=='visible' and m['display']!='none' and float(m['opacity'])>0 for m in state),state
    return [m['text'] for m in state]

def drawing_markers(pg,expected):
    assert marker_snapshot(pg)==expected, 'Drawing must retain current filtered property markers'
    assert pg.locator('.map-pane .price-marker').evaluate_all("els=>els.every(el=>getComputedStyle(el).pointerEvents==='none')")

def stroke(pg,touch=False):
    markers=marker_snapshot(pg)
    box=pg.locator('.map-pane .leaflet-container').bounding_box()
    path=[(box['x']+box['width']*(.5+.23*math.cos(i*math.tau/48)),box['y']+box['height']*(.6+.22*math.sin(i*math.tau/48))) for i in range(49)]
    session=pg.context.new_cdp_session(pg) if touch else None
    if touch:session.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':path[0][0],'y':path[0][1]}]})
    else:pg.mouse.move(*path[0]);pg.mouse.down()
    for index,point in enumerate(path[1:]):
        if touch:session.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':point[0],'y':point[1]}]})
        else:pg.mouse.move(*point,steps=2)
        if index==15:
            drawing_markers(pg,markers)
            assert pg.locator('.draw-vertex').count()==0, 'A live stroke must not create a marker for each sample'
            expect(pg.locator('.map-pane .leaflet-overlay-pane path')).to_have_count(1)
    if touch:session.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});session.detach()
    else:pg.mouse.up()
    bar=pg.get_by_role('region',name='Draw search area')
    expect(bar.get_by_role('button',name='Apply',exact=True)).to_be_enabled()
    expect(pg.locator('.map-draw-hint')).to_contain_text('Area ready')
    assert 3<=pg.locator('.draw-vertex').count()<=64
    drawing_markers(pg,markers)

with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True)
    context=browser.new_context(viewport={'width':1440,'height':900});page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
    for purpose in ['sale','rent']:
        query=urlencode({'q':'Hyderabad','purpose':purpose,'beds':3,'baths':2,'max_price':20000000 if purpose=='sale' else 100000})
        page.goto(BASE+'/homes?'+query,wait_until='networkidle')
        original_url=page.url;markers=marker_snapshot(page)
        page.get_by_role('button',name='Draw',exact=True).click()
        drawing_markers(page,markers);assert page.url==original_url
        canvas=page.locator('.map-pane .leaflet-container').bounding_box()
        for marker in page.locator('.map-pane .price-marker').all():
            box=marker.bounding_box()
            if box and canvas['x']+10<box['x']+box['width']/2<canvas['x']+canvas['width']-10 and canvas['y']+130<box['y']+box['height']/2<canvas['y']+canvas['height']-65:
                page.mouse.click(box['x']+box['width']/2,box['y']+box['height']/2)
                expect(page.locator('.leaflet-popup')).to_have_count(0)
                expect(page.locator('.map-draw-hint')).to_contain_text('Press and hold')
                break
        toolbar=page.get_by_role('region',name='Draw search area')
        toolbar.get_by_role('button',name='Move map',exact=True).click();drawing_markers(page,markers)
        toolbar.get_by_role('button',name='Pen',exact=True).click();stroke(page)
        drawing_markers(page,markers);assert page.url==original_url
        page.screenshot(path=str(ARTIFACTS/f'draw-visible-markers-{purpose}.png'))
        toolbar.get_by_role('button',name='Redraw area',exact=True).click();drawing_markers(page,markers)
        toolbar.get_by_role('button',name='Cancel',exact=True).click()
        assert marker_snapshot(page)==markers and page.url==original_url
        assert page.locator('.map-pane .price-marker').evaluate_all("els=>els.every(el=>getComputedStyle(el).pointerEvents!=='none')")
        record(f'Filtered {purpose} markers remain visible in Pen, Move map, stroke, preview and Redraw; cancel restores interaction')
    all_sale=page.request.get(BASE+'/api/properties?page_size=100').json()['items']
    page.goto(BASE+'/homes?q=Hyderabad',wait_until='networkidle');page.get_by_role('button',name='Draw',exact=True).click()
    bar=page.get_by_role('region',name='Draw search area');expect(bar.get_by_role('button',name='Pen',exact=True)).to_have_attribute('aria-pressed','true')
    expect(bar.get_by_role('button',name='Apply',exact=True)).to_be_disabled()
    assert bar.bounding_box()['height']<=70
    stroke(page)
    page.screenshot(path=str(ARTIFACTS/'pen-draw-preview.png'))
    record('Default pen mode shows a smooth single live stroke and closes it on release')
    handle=page.locator('.draw-vertex').first.bounding_box()
    before=page.locator('.map-pane .leaflet-overlay-pane path').get_attribute('d')
    page.mouse.move(handle['x']+handle['width']/2,handle['y']+handle['height']/2);page.mouse.down();page.mouse.move(handle['x']+handle['width']/2+25,handle['y']+handle['height']/2+10,steps=12);page.mouse.up()
    expect(bar.get_by_role('button',name='Apply',exact=True)).to_be_enabled();assert page.locator('.map-pane .leaflet-overlay-pane path').get_attribute('d')!=before
    record('Finished pen boundary has draggable corners for adjustment')
    bar.get_by_role('button',name='Apply',exact=True).click();expect(page.get_by_role('button',name='Remove Boundary',exact=True)).to_be_visible()
    assert parse_qs(urlparse(page.url).query)['boundary_q']==['Hyderabad']
    shape=json.loads(parse_qs(urlparse(page.url).query)['polygon'][0]);expected=[r['id'] for r in all_sale if inside([r['lat'],r['lng']],shape)]
    data=page.request.get(BASE+'/api/properties?'+urlparse(page.url).query+'&page_size=100').json()
    assert 0<len(expected)<len(all_sale)
    assert [r['id'] for r in data['items']]==expected
    expect(page.locator('.results-meta')).to_contain_text(str(len(expected))+' results')
    expect(page.locator('.map-pane .price-marker')).to_have_count(len(expected))
    chart=page.request.get(BASE+'/api/properties/price-distribution?'+urlparse(page.url).query).json();assert chart['total']==sum(chart['counts'])==len(expected)
    record('Adjusted pen area filters real PostgreSQL results, map markers, counts and price histogram')
    applied_url=page.url;page.reload(wait_until='networkidle');expect(page.get_by_role('button',name='Edit boundary',exact=True)).to_be_visible()
    page.get_by_role('button',name='Edit boundary',exact=True).click();expect(bar.get_by_role('button',name='Apply',exact=True)).to_be_enabled();expect(page.locator('.draw-vertex')).to_have_count(len(shape))
    bar.get_by_role('button',name='Cancel',exact=True).click();assert page.url==applied_url
    page.get_by_role('button',name='Draw',exact=True).click();bar.get_by_role('button',name='Move map',exact=True).click()
    canvas=page.locator('.map-pane .leaflet-container');box=canvas.bounding_box();before=page.locator('.map-pane .leaflet-map-pane').get_attribute('style')
    x=box['x']+box['width']*.5;y=box['y']+box['height']*.6
    page.mouse.move(x,y);page.mouse.down();page.mouse.move(x+70,y+20,steps=10);page.mouse.up();page.wait_for_timeout(250)
    assert page.locator('.map-pane .leaflet-map-pane').get_attribute('style')!=before
    expect(bar.get_by_role('button',name='Apply',exact=True)).to_be_disabled();assert not page.locator('.draw-vertex').count()
    bar.get_by_role('button',name='Pen',exact=True).click();stroke(page);bar.get_by_role('button',name='Redraw area',exact=True).click()
    expect(bar.get_by_role('button',name='Apply',exact=True)).to_be_disabled();assert not page.locator('.draw-vertex').count()
    stroke(page);page.keyboard.press('Escape');expect(bar).not_to_be_visible();assert page.url==applied_url
    record('Edit, Move map, Redraw and Escape preserve applied search until Apply')
    page.get_by_role('button',name='Remove Boundary',exact=True).click();assert 'polygon' not in parse_qs(urlparse(page.url).query)
    assert parse_qs(urlparse(page.url).query)['q']==['Hyderabad']
    assert 'boundary_q' not in parse_qs(urlparse(page.url).query)
    expect(page.locator('.results-heading h1')).to_contain_text('Hyderabad')
    restored=page.request.get(BASE+'/api/properties?'+urlparse(page.url).query+'&page_size=100').json()
    original=page.request.get(BASE+'/api/properties?q=Hyderabad&page_size=100').json()
    assert [r['id'] for r in restored['items']]==[r['id'] for r in original['items']]
    expect(page.locator('.map-pane .price-marker')).to_have_count(len(original['items']))
    page.screenshot(path=str(ARTIFACTS/'boundary-hyderabad-restored.png'))
    record('Remove Boundary after reload restores Hyderabad results and city map')
    # Reproduce a user returning to the starting point and overrunning it.
    page.get_by_role('button',name='Draw',exact=True).click();box=canvas.bounding_box()
    raw=[(.35,.45),(.7,.45),(.7,.8),(.35,.8),(.35,.45),(.40,.45),(.40,.48)]
    page.mouse.move(box['x']+box['width']*raw[0][0],box['y']+box['height']*raw[0][1]);page.mouse.down()
    for x,y in raw[1:]:page.mouse.move(box['x']+box['width']*x,box['y']+box['height']*y,steps=12)
    page.mouse.up();expect(bar.get_by_role('button',name='Apply',exact=True)).to_be_enabled()
    expect(page.locator('.map-draw-hint')).to_contain_text('Area ready')
    page.screenshot(path=str(ARTIFACTS/'pen-closing-overlap-fixed.png'))
    bar.get_by_role('button',name='Apply',exact=True).click();shape=json.loads(parse_qs(urlparse(page.url).query)['polygon'][0])
    expected=[r['id'] for r in all_sale if inside([r['lat'],r['lng']],shape)]
    data=page.request.get(BASE+'/api/properties?'+urlparse(page.url).query+'&page_size=100');assert data.ok,data.text()
    assert [r['id'] for r in data.json()['items']]==expected
    record('Returning to the pen start and overrunning it trims the closing loop and applies matching PostgreSQL results')

    # Accidental clicks give guidance, and a crossed pen stroke remains editable but cannot apply.
    page.get_by_role('button',name='Draw',exact=True).click();box=canvas.bounding_box();page.mouse.click(box['x']+box['width']*.4,box['y']+box['height']*.6)
    expect(page.locator('.map-draw-hint')).to_contain_text('Press and hold')
    path=[(.3,.4),(.7,.8),(.3,.8),(.7,.4)]
    page.mouse.move(box['x']+box['width']*path[0][0],box['y']+box['height']*path[0][1]);page.mouse.down()
    for x,y in path[1:]:page.mouse.move(box['x']+box['width']*x,box['y']+box['height']*y,steps=15)
    page.mouse.up();expect(page.locator('.map-draw-hint')).to_have_attribute('role','alert');expect(bar.get_by_role('button',name='Apply',exact=True)).to_be_disabled()
    bar.get_by_role('button',name='Redraw area',exact=True).click();stroke(page);expect(bar.get_by_role('button',name='Apply',exact=True)).to_be_enabled()
    bar.get_by_role('button',name='Cancel',exact=True).click()
    record('Accidental taps explain pen drawing; crossed strokes are blocked and Redraw repairs them')
    for width,height in [(1366,600),(390,844),(320,568)]:
        ctx=browser.new_context(viewport={'width':width,'height':height},has_touch=width<600,is_mobile=width<600);pg=ctx.new_page();pg.on('pageerror',lambda e:errors.append(str(e)))
        pg.goto(BASE+'/homes?q=Hyderabad',wait_until='networkidle')
        if width<600:pg.get_by_role('button',name='Map',exact=True).click()
        pg.get_by_role('button',name='Draw',exact=True).click();toolbar=pg.get_by_role('region',name='Draw search area');box=toolbar.bounding_box()
        assert box['height']<=70 and box['x']>=0 and box['x']+box['width']<=width+1
        assert pg.evaluate('document.documentElement.scrollWidth<=innerWidth')
        stroke(pg,touch=width<600);pg.screenshot(path=str(ARTIFACTS/f'pen-draw-{width}-{height}.png'))
        toolbar.get_by_role('button',name='Apply',exact=True).click();expect(pg.get_by_role('button',name='Remove Boundary',exact=True)).to_be_visible()
        params=parse_qs(urlparse(pg.url).query);assert 'polygon' in params
        pg.reload(wait_until='networkidle')
        if width<600:pg.get_by_role('button',name='Map',exact=True).click()
        expect(pg.get_by_role('button',name='Edit boundary',exact=True)).to_be_visible();ctx.close()
        record(f'{width}x{height}: compact pen toolbar, continuous '+('finger' if width<600 else 'mouse')+' stroke, Apply and reload')
    # Return context survives reload, redrawing and browser navigation across markets.
    for city in ['Hyderabad','Bengaluru','Mumbai','Pune','New Delhi','']:
        query=urlencode({'q':city,'beds':2,'max_price':100000000})
        page.goto(BASE+'/homes?'+query,wait_until='networkidle')
        original=page.request.get(BASE+'/api/properties?'+query+'&page_size=100').json()
        page.get_by_role('button',name='Draw',exact=True).click();stroke(page)
        bar.get_by_role('button',name='Apply',exact=True).click()
        params=parse_qs(urlparse(page.url).query,keep_blank_values=True)
        assert params.get('boundary_q',[''])==[city]
        page.reload(wait_until='networkidle')
        if city=='Hyderabad':
            page.get_by_role('button',name='Draw',exact=True).click();stroke(page)
            bar.get_by_role('button',name='Apply',exact=True).click()
        page.get_by_role('button',name='Remove Boundary',exact=True).click()
        params=parse_qs(urlparse(page.url).query,keep_blank_values=True)
        assert params['q']==[city] and 'polygon' not in params and 'boundary_q' not in params
        assert params['beds']==['2'] and params['max_price']==['100000000']
        expect(page.locator('.results-heading h1')).to_contain_text(city or 'India')
        expect(page.locator('.results-meta')).to_contain_text(str(original['total'])+' results')
        restored=page.request.get(BASE+'/api/properties?'+urlparse(page.url).query+'&page_size=100').json()
        assert [r['id'] for r in restored['items']]==[r['id'] for r in original['items']]
        page.go_back(wait_until='networkidle');expect(page.get_by_role('button',name='Remove Boundary',exact=True)).to_be_visible()
        page.go_forward(wait_until='networkidle');expect(page.locator('.results-heading h1')).to_contain_text(city or 'India')
    record('Five city searches and all-India search restore their location and room/price criteria after drawing, reload, redraw and Back/Forward')
    page.goto(BASE+'/homes?q=Hyderabad&beds=2',wait_until='networkidle')
    page.get_by_role('button',name='Draw',exact=True).click();stroke(page)
    bar.get_by_role('button',name='Apply',exact=True).click()
    page.get_by_role('button',name='Reset',exact=True).click()
    params=parse_qs(urlparse(page.url).query)
    assert params['q']==['Hyderabad'] and 'polygon' not in params and params['beds']==['0']
    expect(page.locator('.results-heading h1')).to_contain_text('Hyderabad')
    record('Reset clears property filters and drawn area while restoring the original city')
    assert not errors,errors
    (ARTIFACTS/'pen-draw-results.json').write_text(json.dumps({'checks':checks,'browser_errors':errors},indent=2),encoding='utf-8')
    browser.close();print(f'All {len(checks)} pen drawing checks passed.',flush=True)
