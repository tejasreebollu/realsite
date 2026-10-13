"""Price filter UI, real server results, financing, sliders and compact layouts."""
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import json
import math
import secrets
import sys
import time
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.tools'))
from playwright.sync_api import sync_playwright, expect
BASE = 'http://localhost:8090'
ARTIFACTS = ROOT / 'artifacts'
ARTIFACTS.mkdir(exist_ok=True)
checks, errors, layouts = [], [], []

def record(label):
    checks.append(label)
    print('PASS:', label, flush=True)

def open_price(page):
    page.get_by_role('button', name='Price', exact=True).click()
    panel = page.get_by_role('dialog', name='Price range', exact=True)
    expect(panel).to_be_visible()
    return panel

def check_layout(page, panel, mode):
    box = panel.bounding_box()
    size = panel.evaluate('e => ({scroll: e.scrollHeight, visible: e.clientHeight})')
    assert box['x'] >= 0 and box['x'] + box['width'] <= page.viewport_size['width'] + 1, box
    assert box['y'] + box['height'] <= page.viewport_size['height'] + 1, box
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    expect(panel.get_by_role('button', name='Apply', exact=True)).to_be_in_viewport()
    expect(page.locator('.mobile-view-toggle')).not_to_be_visible()
    layouts.append({'viewport':page.viewport_size,'mode':mode,'box':box,**size})

def results(page):
    response = page.request.get(BASE + '/api/properties?' + urlparse(page.url).query + '&page_size=100')
    assert response.ok, response.text()
    data = response.json()
    expect(page.locator('.results-grid .property-card')).to_have_count(min(data['total'],24))
    return data

def emi(price, down, rate, years):
    r = rate / 1200
    return price * (1-down/100) * (r / (1-(1+r)**(-years*12)) if r else 1/(years*12))

with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True)
    context=browser.new_context(viewport={'width':1440,'height':900})
    page=context.new_page()
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(BASE+'/homes?q=Hyderabad',wait_until='networkidle')
    baseline=results(page)
    panel=open_price(page)
    expect(panel.locator('.price-chart-caption')).to_contain_text(f"{baseline['total']} matching")
    expect(panel.locator('.price-bars>span')).to_have_count(30)
    expect(panel.get_by_role('tab',name='List Price',exact=True)).to_have_attribute('aria-selected','true')
    page.screenshot(path=str(ARTIFACTS/'price-list-desktop.png'))
    # Mouse dragging both native thumbs must update numeric fields.
    for name, direction, label in [('Minimum price slider',1,'Minimum price (₹)'),('Maximum price slider',-1,'Maximum price (₹)')]:
        slider=panel.get_by_label(name,exact=True)
        box=slider.bounding_box()
        x=box['x']+12 if direction==1 else box['x']+box['width']-12
        page.mouse.move(x,box['y']+box['height']/2)
        page.mouse.down()
        page.mouse.move(x+direction*60,box['y']+box['height']/2,steps=10)
        page.mouse.up()
        assert float(panel.get_by_label(label,exact=True).input_value())>0
    panel.get_by_role('button',name='Clear',exact=True).click()
    slider=panel.get_by_label('Minimum price slider',exact=True)
    slider.focus(); slider.press('ArrowRight')
    assert float(panel.get_by_label('Minimum price (₹)',exact=True).input_value())>0
    panel.get_by_label('Minimum price (₹)',exact=True).fill('10000000')
    panel.get_by_label('Maximum price (₹)',exact=True).fill('5000000')
    panel.get_by_role('button',name='Apply',exact=True).click()
    expect(panel.get_by_role('alert')).to_contain_text('Maximum must')
    panel.get_by_label('Minimum price (₹)',exact=True).fill('5000000')
    panel.get_by_label('Maximum price (₹)',exact=True).fill('12000000')
    panel.get_by_role('button',name='Apply',exact=True).click()
    data=results(page)
    expected=[x['id'] for x in baseline['items'] if 5_000_000<=x['price']<=12_000_000]
    assert [x['id'] for x in data['items']]==expected
    page.reload(wait_until='networkidle')
    panel=open_price(page)
    expect(panel.get_by_label('Minimum price (₹)',exact=True)).to_have_value('5000000')
    expect(panel.locator('.price-chart-caption')).to_contain_text(f"{baseline['total']} matching")
    panel.get_by_label('Maximum price (₹)',exact=True).press('Escape')
    expect(panel).not_to_be_visible()
    record('Real histogram, both mouse-drag thumbs, keyboard slider, INR fields, range validation, server results, reload and Escape')

    panel=open_price(page)
    panel.get_by_role('tab',name='List Price',exact=True).focus()
    panel.get_by_role('tab',name='List Price',exact=True).press('ArrowRight')
    expect(panel.get_by_role('tab',name='Monthly Payment',exact=True)).to_have_attribute('aria-selected','true')
    expect(panel.locator('.price-distribution')).to_have_count(0)
    panel.get_by_label('Minimum monthly payment (₹)',exact=True).fill('30000')
    panel.get_by_label('Maximum monthly payment (₹)',exact=True).fill('85000')
    panel.get_by_label('Down payment',exact=True).select_option('30')
    panel.get_by_label('Credit score',exact=True).select_option('700749')
    expect(panel.locator('.price-estimate-note')).to_contain_text('9% p.a.')
    panel.locator('.price-assumptions summary').click()
    panel.get_by_label('Assumed loan tenure',exact=True).select_option('25')
    panel.get_by_label('Assumed annual interest rate',exact=True).fill('8.75')
    page.screenshot(path=str(ARTIFACTS/'price-payment-desktop.png'))
    panel.get_by_role('button',name='Apply',exact=True).click()
    data=results(page)
    expected=[x['id'] for x in baseline['items'] if 30000<=emi(x['price'],30,8.75,25)<=85000]
    assert [x['id'] for x in data['items']]==expected
    assert all(x['estimated_payment']==round(emi(x['price'],30,8.75,25)) for x in data['items'])
    expect(page.locator('.results-grid .payment-estimate')).to_have_count(len(expected))
    params=parse_qs(urlparse(page.url).query)
    assert all(params[k]==[v] for k,v in {'price_mode':'payment','down_pct':'30','annual_rate':'8.75','loan_years':'25','credit_band':'700749'}.items())
    page.reload(wait_until='networkidle')
    panel=open_price(page)
    expect(panel.get_by_label('Down payment',exact=True)).to_have_value('30')
    expect(panel.get_by_label('Credit score',exact=True)).to_have_value('700749')
    expect(panel.locator('.price-estimate-note')).to_contain_text('8.75% p.a. · 25 years')
    panel.get_by_label('Maximum monthly payment (₹)',exact=True).press('Escape')
    record('Monthly Payment tab, down payment, demo credit rate, custom APR/tenure, actual EMI filtering and URL restoration')

    registration=page.request.post(BASE+'/api/auth/register',data={'name':'Price Filter Test','email':f'price-browser-{int(time.time())}@example.com','password':'PriceTest-'+secrets.token_hex(12)})
    assert registration.status==201, registration.text()
    try:
        page.reload(wait_until='networkidle')
        page.get_by_role('button',name='Save search',exact=True).click()
        expect(page.locator('.toast')).to_contain_text('Search saved')
        page.get_by_role('button',name='Updates',exact=True).click()
        article=page.locator('.saved-search-list article').filter(has_text='Est. EMI')
        expect(article).to_have_count(1)
        article.get_by_role('button',name='View homes',exact=True).click()
        restored=parse_qs(urlparse(page.url).query)
        for key in ['price_mode','min_payment','max_payment','down_pct','annual_rate','loan_years','credit_band']:
            assert restored[key]==params[key]
        assert [x['id'] for x in results(page)['items']]==expected
        record('Saved EMI search displays the budget and restores financing and matching listings')
    finally:
        for saved in page.request.get(BASE+'/api/saved-searches').json():
            assert page.request.delete(BASE+f'/api/saved-searches/{saved["id"]}').status==204
    page.goto(BASE+'/homes?q=Hyderabad&price_mode=payment&down_pct=35&loan_years=18',wait_until='networkidle')
    assert results(page)['total']==baseline['total']
    panel=open_price(page)
    expect(panel.get_by_label('Down payment',exact=True)).to_have_value('35')
    panel.locator('.price-assumptions summary').click()
    expect(panel.get_by_label('Assumed loan tenure',exact=True)).to_have_value('18')
    record('Other valid financing values from shared URLs render and restore correctly')
    panel.get_by_role('button',name='Calculate your budget',exact=True).click()
    expect(page.get_by_role('heading',name='Home loan EMI calculator',exact=True)).to_be_visible()
    record('Calculate your budget opens the working home-loan calculator')
    context.close()

    for width,height in [(1920,900),(1366,600),(768,700),(390,844),(360,640),(320,568)]:
        context=browser.new_context(viewport={'width':width,'height':height},has_touch=width<=760)
        page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(BASE+'/homes?q=Hyderabad',wait_until='networkidle')
        panel=open_price(page)
        expect(panel.locator('.price-chart-caption')).to_contain_text('matching')
        check_layout(page,panel,'price')
        page.screenshot(path=str(ARTIFACTS/f'price-list-{width}-{height}.png'))
        tab=panel.get_by_role('tab',name='Monthly Payment',exact=True)
        tab.tap() if width<=760 else tab.click()
        check_layout(page,panel,'payment')
        page.screenshot(path=str(ARTIFACTS/f'price-payment-{width}-{height}.png'))
        panel.locator('.price-assumptions summary').scroll_into_view_if_needed()
        panel.locator('.price-assumptions summary').click()
        panel.get_by_label('Assumed loan tenure',exact=True).select_option('25')
        panel.get_by_label('Down payment',exact=True).select_option('50')
        panel.get_by_role('button',name='Apply',exact=True).click()
        assert results(page)['total']==baseline['total']
        page.get_by_role('button',name='For sale',exact=True).click()
        page.get_by_role('button',name='For rent',exact=True).click()
        rental=results(page)
        assert parse_qs(urlparse(page.url).query)['price_mode']==['price']
        panel=open_price(page)
        expect(panel.get_by_role('tab',name='Monthly Rent',exact=True)).to_be_visible()
        expect(panel.get_by_label('Down payment',exact=True)).to_have_count(0)
        panel.get_by_label('Minimum price (₹)',exact=True).fill('20000')
        panel.get_by_label('Maximum price (₹)',exact=True).fill('50000')
        panel.get_by_role('button',name='Apply',exact=True).click()
        filtered=results(page)
        assert [x['id'] for x in filtered['items']]==[x['id'] for x in rental['items'] if 20000<=x['price']<=50000]
        panel=open_price(page)
        panel.get_by_role('button',name='Clear',exact=True).click()
        panel.get_by_role('button',name='Apply',exact=True).click()
        assert results(page)['total']==rental['total']
        record(f'{width}x{height}: compact list/payment layouts, touch, visible Apply, purpose reset, monthly rent range and Clear')
        context.close()
    assert not errors,errors
    record('No browser JavaScript errors')
    (ARTIFACTS/'price-filter-results.json').write_text(json.dumps({'checks':checks,'layouts':layouts,'errors':errors},indent=2)+'\n',encoding='utf-8')
    browser.close()
print(f'Completed {len(checks)} price-filter checks',flush=True)
