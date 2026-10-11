"""Local homepage and demo-admin analytics checks; only creates an authentication session."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'.tools'))
(ROOT/'artifacts').mkdir(exist_ok=True)
from playwright.sync_api import sync_playwright,expect
checks=[];errors=[]
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True)
    context=browser.new_context(viewport={'width':1440,'height':1000},accept_downloads=True)
    page=context.new_page();page.on('pageerror',lambda e: errors.append(str(e)))
    login=context.request.post('http://localhost:8090/api/auth/login',data={'email':'admin@demo.example.com','password':'AdminDemo@2026'})
    assert login.ok,login.text()
    page.goto('http://localhost:8090',wait_until='domcontentloaded')
    expect(page.locator('.hero h1')).to_be_visible()
    assert ' '.join(page.locator('.hero h1').inner_text().split())=='Find your space. Build your future.'
    assert 'Buy. Sell. Rent.' not in page.locator('.hero').inner_text()
    assert 'Recommended' not in page.locator('.hero').inner_text()
    checks.append('Home hero shows the chosen headline exactly and removes the old wording')
    for width in [1920,1440,768,390,320]:
        page.set_viewport_size({'width':width,'height':900});page.wait_for_timeout(100)
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),width
        hero=page.locator('.hero').bounding_box()
        for selector in ['.hero h1','.hero .search-input-wrap','.hero-subtitle']:
            item=page.locator(selector).bounding_box()
            assert item['x']>=hero['x']-1 and item['x']+item['width']<=hero['x']+hero['width']+1,(width,selector,'horizontal')
            assert item['y']+item['height']<=hero['y']+hero['height']+1,(width,selector,'vertical')
        assert page.locator('.hero h1').evaluate('e=>e.scrollWidth<=e.clientWidth'),width
        if width in [1440,390]: page.locator('.hero').screenshot(path=str(ROOT/'artifacts'/f'hero-headline-{width}.png'))
    checks.append('Headline, search and subtitle fit within the hero at 1920/1440/768/390/320px')
    page.locator('.hero input').fill('Pune');page.locator('.hero input').press('Enter')
    page.wait_for_url('**/homes?**')
    expect(page.locator('.results-heading h1')).to_contain_text('Pune')
    expect(page.locator('.results-grid .property-card').first).to_be_visible()
    checks.append('Hero search still opens filtered property results')
    page.set_viewport_size({'width':1440,'height':1000})
    page.goto('http://localhost:8090/admin',wait_until='networkidle')
    expect(page.locator('.analytics-kpi')).to_have_count(4)
    report=context.request.get('http://localhost:8090/api/admin/analytics?days=30&dataset=all')
    assert report.ok,report.text()
    data=report.json()
    assert page.locator('.analytics-kpi>strong').first.inner_text()==str(data['summary']['active'])
    assert page.locator('.analytics-panel').count()==11
    checks.append('Admin landing opens analytics: four real-data KPIs and nine charts')
    rows=page.locator('.analytics>.analytics-grid')
    assert rows.nth(0).locator('.analytics-panel').count()==3
    assert rows.nth(1).locator('.analytics-panel').count()==3
    assert rows.nth(2).locator('.activity-panel').count()==1
    assert rows.nth(2).locator('.analytics-panel').count()==1
    panel=page.locator('.activity-panel').bounding_box()
    kpis=page.locator('.analytics-kpis').bounding_box()
    assert abs(panel['width']-kpis['width'])<2 and abs(panel['x']-kpis['x'])<2
    plot=page.locator('.activity-panel .activity-chart')
    expect(plot).to_be_visible()
    page.wait_for_timeout(100)
    size=plot.evaluate('e=>({width:e.clientWidth,view:e.viewBox.baseVal.width,right:e.querySelector("line").x2.baseVal.value})')
    assert abs(size['width']-size['view'])<2 and abs(size['right']-size['view']+28)<.01
    checks.append('Activity is the full-width third chart row; plot fills its available width without stretched text')
    for removed in ['Portal analytics','Explore inventory, enquiries and account activity to guide your next move.','INSIGHTS & PLANNING','100 synthetic listings included','Inventory is a current snapshot. Activity covers the selected period. Account and agent charts cover the whole portal.','People & platform health','Account growth, agent coverage and inventory engagement.']:
        assert page.get_by_text(removed,exact=True).count()==0,removed
    assert page.locator('.analytics-heading,.analytics-context,.analytics-section-heading').count()==0
    for name in ['Refresh analytics','Export city report']:
        assert page.get_by_role('button',name=name,exact=True).evaluate("e=>!!e.closest('.analytics-toolbar')")
    assert page.locator('.analytics-kpi').evaluate_all('els=>els.every(e=>e.getBoundingClientRect().height<125)')
    assert page.locator('.analytics-grid').evaluate_all("els=>els.every(e=>getComputedStyle(e).rowGap==='10px')")
    checks.append('Requested headings/notes removed; toolbar actions grouped right; KPIs and chart row gaps compact')
    page.screenshot(path=str(ROOT/'artifacts'/'analytics-desktop.png'),full_page=True)
    page.locator('.city-comparison button').first.hover()
    assert 'enquiries per 100' in page.locator('.city-panel .chart-readout').inner_text()
    page.locator('.activity-panel .activity-chart [role=button]').nth(10).focus()
    assert 'new listings' in page.locator('.activity-panel .chart-readout').inner_text()
    checks.append('Chart hover and keyboard focus show values')
    chart=page.locator('.activity-panel .activity-chart')
    expect(chart.locator('.activity-bar-group')).to_have_count(len(data['activity']))
    expect(chart.locator('.activity-data-bar')).to_have_count(2*len(data['activity']))
    assert chart.locator('polyline').count()==0
    assert page.locator('.registration-panel .activity-chart').locator('polyline').count()==1
    highest=max(1,*[max(r['listings'],r['inquiries']) for r in data['activity']])
    for key in ['listings','inquiries']:
        heights=chart.locator(f'[data-series={key}]').evaluate_all('els=>els.map(e=>Number(e.getAttribute("height")))')
        assert all(abs(height-row[key]/highest*118)<.001 for height,row in zip(heights,data['activity']))
    checks.append('Grouped bars accurately encode listing/enquiry counts; account growth retains its line chart')
    for days in ['90','365','30']:
        with page.expect_response(lambda r: '/api/admin/analytics?' in r.url and r.status==200):
            page.get_by_label('Analytics reporting period').select_option(days)
        expect(page.locator('.analytics-kpi')).to_have_count(4)
        expected=context.request.get(f'http://localhost:8090/api/admin/analytics?days={days}&dataset=all').json()
        expect(page.locator('.activity-panel .activity-data-bar')).to_have_count(2*len(expected['activity']))
    checks.append('30/90/365-day reporting works')
    for dataset in ['owner','synthetic','all']:
        with page.expect_response(lambda r: '/api/admin/analytics?' in r.url and r.status==200):
            page.get_by_label('Analytics listing dataset').select_option(dataset)
        expect(page.locator('.analytics-kpi')).to_have_count(4)
        d=context.request.get(f'http://localhost:8090/api/admin/analytics?dataset={dataset}').json()
        assert page.locator('.analytics-kpi>strong').first.inner_text()==str(d['summary']['active'])
    checks.append('Dataset changes scope listing and enquiry totals correctly')
    page.get_by_label('Price distribution mode').get_by_role('button',name='Rent',exact=True).click()
    expect(page.get_by_label('Price distribution mode').get_by_role('button',name='Rent',exact=True)).to_have_attribute('aria-pressed','true')
    assert 'Monthly rents' in page.locator('.pricing-panel').inner_text()
    checks.append('Sale and rent price distributions switch separately')
    with page.expect_download() as info: page.get_by_role('button',name='Export city report').click()
    download=info.value;download.save_as(str(ROOT/'artifacts'/'analytics-city-report.csv'))
    csv=Path(download.path()).read_text(encoding='utf-8-sig')
    assert 'Median monthly rent INR' in csv and 'Hyderabad' in csv
    checks.append('Aggregate city CSV exports with period, dataset and INR columns')
    for section in ['Listings','Accounts','Agent reviews','Account activity','Enquiries']:
        page.get_by_role('button',name=section,exact=True).click()
        page.wait_for_timeout(350)
        tabs=page.get_by_label('Administration sections')
        expect(tabs).to_be_visible()
        assert tabs.bounding_box()['y'] < 160, section
        page.evaluate('window.scrollTo(0, document.documentElement.scrollHeight)')
        page.wait_for_timeout(100)
        assert tabs.bounding_box()['y'] >= 0 and tabs.bounding_box()['y'] < 160,section
        assert page.locator('.analytics').count()==0
        assert page.get_by_role('button',name=section,exact=True).evaluate("e=>e.classList.contains('active')")
    page.get_by_role('button',name='Analytics',exact=True).click();expect(page.locator('.analytics-kpi')).to_have_count(4)
    checks.append('All management tabs, including Listings/Enquiries, stay visible at the top and during scrolling')
    for width in [1280,768,390,320]:
        page.set_viewport_size({'width':width,'height':900})
        page.wait_for_timeout(250)
        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'),f'Overflow at {width}'
        assert page.locator('.analytics').evaluate('e=>e.scrollWidth<=e.clientWidth'),f'Analytics overflow at {width}'
        chart=page.locator('.activity-panel .activity-chart')
        size=chart.evaluate('e=>({width:e.clientWidth,view:e.viewBox.baseVal.width})')
        assert abs(size['width']-size['view'])<2,f'Plot did not resize at {width}'
        bars=chart.locator('.activity-data-bar').evaluate_all('els=>els.map(e=>({x:Number(e.getAttribute("x")),width:Number(e.getAttribute("width"))}))')
        assert all(bars[i]['x']+bars[i]['width']<bars[i+1]['x'] for i in range(len(bars)-1)),f'Bars overlap at {width}'
        page.screenshot(path=str(ROOT/'artifacts'/f'analytics-{width}.png'),full_page=True)
        if width==390: page.screenshot(path=str(ROOT/'artifacts'/'analytics-mobile-viewport.png'))
    checks.append('Responsive layouts at 1280, 768, 390 and 320px have no page overflow')
    page.set_viewport_size({'width':1440,'height':1000})
    page.route('**/api/admin/analytics?*',lambda route: route.fulfill(status=500,content_type='application/json',body=json.dumps({'detail':'Analytics temporarily unavailable'})))
    page.get_by_role('button',name='Refresh analytics').click()
    expect(page.get_by_role('alert')).to_contain_text('Analytics temporarily unavailable')
    assert page.locator('.analytics-kpi').count()==0
    page.unroute('**/api/admin/analytics?*');page.get_by_role('button',name='Try again',exact=True).click();expect(page.locator('.analytics-kpi')).to_have_count(4)
    checks.append('Failure clears stale charts and retry reloads the report')
    empty=json.loads(json.dumps(data))
    empty['dataset']='synthetic'
    empty['summary']={k:(None if k.startswith('median_') else 0) for k in empty['summary']}
    empty['cities']=[];empty['types']=[]
    for row in empty['activity']:
        row['listings']=row['inquiries']=row['registrations']=0
    for group in [*empty['pricing'].values(),empty['age'],empty['agents']]:
        for row in group: row['count']=0
    empty['signals']=[{'title':'Establish an enquiry baseline','detail':'No enquiries in this selection.','section':'inquiries'}]
    page.route('**/api/admin/analytics?*',lambda route: route.fulfill(status=200,content_type='application/json',body=json.dumps(empty)))
    page.get_by_label('Analytics listing dataset').select_option('synthetic')
    expect(page.locator('.analytics-context')).to_have_count(0)
    expect(page.locator('.analytics-kpi>strong').first).to_have_text('0')
    expect(page.locator('.analytics-kpi>strong').nth(2)).to_have_text('—')
    expect(page.get_by_text('No cities in this selection.',exact=True)).to_be_visible()
    checks.append('Empty inventory displays zero and missing medians without removed context banners')
    page.unroute('**/api/admin/analytics?*')
    hostile=json.loads(json.dumps(data));hostile['cities'][0]['city']='  =1+1'
    page.route('**/api/admin/analytics?*',lambda route: route.fulfill(status=200,content_type='application/json',body=json.dumps(hostile)))
    page.get_by_role('button',name='Refresh analytics').click()
    expect(page.locator('.analytics-table tbody th').first).to_contain_text('=1+1')
    with page.expect_download() as info: page.get_by_role('button',name='Export city report').click()
    assert chr(34)+chr(39)+'  =1+1'+chr(34) in Path(info.value.path()).read_text(encoding='utf-8-sig')
    checks.append('CSV export escapes formula prefixes including leading whitespace')
    page.unroute('**/api/admin/analytics?*')
    assert not errors,errors
    browser.close()
print(json.dumps({'checks':checks,'browser_errors':errors},indent=2))
(ROOT/'artifacts'/'analytics-browser-results.json').write_text(json.dumps({'checks':checks,'browser_errors':errors},indent=2),encoding='utf-8')
