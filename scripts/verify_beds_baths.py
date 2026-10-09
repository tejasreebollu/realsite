"""Verify plus counts and exact-match checkboxes, touch controls and saved searches."""
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import json
import secrets
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.tools'))
from playwright.sync_api import sync_playwright, expect

BASE = 'http://localhost:8090'
ARTIFACTS = ROOT / 'artifacts'
ARTIFACTS.mkdir(exist_ok=True)
checks, errors = [], []
def room_label(count, mode, label):
    return f'Exactly {count} {label}' if mode == 'exact' else f'{count}+ {label}'
NON_HOMES = ['Open Plot', 'Commercial Building', 'Office', 'Shop']


def record(label):
    checks.append(label)
    print('PASS:', label, flush=True)


def close_filters(page):
    # The popup is almost flush with the left edge at 360px. Click the exposed
    # right edge of the backdrop, using its actual dimensions rather than a
    # hard-coded point that may fall inside the popup.
    backdrop = page.get_by_role('button', name='Close filters', exact=True)
    box = backdrop.bounding_box()
    backdrop.click(position={'x': box['width'] - 4, 'y': box['height'] / 2})


def choose(page, beds, baths, bed_mode='exact', bath_mode='exact', touch=False):
    page.get_by_role('button', name='Beds & baths', exact=True).click()
    for label, count, mode in [('Bedrooms', beds, bed_mode), ('Bathrooms', baths, bath_mode)]:
        checkbox = page.get_by_label('Use exact match for ' + label.lower(), exact=True)
        if mode == 'exact':
            checkbox.check()
            expect(checkbox).to_be_checked()
        else:
            checkbox.uncheck()
            expect(checkbox).not_to_be_checked()
        group = page.get_by_role('group', name=label + ' count', exact=True)
        name = 'Any' if not count else str(count) + ('+' if mode == 'min' else '')
        choice = group.get_by_role('button', name=name, exact=True)
        if touch:
            choice.tap()
        else:
            choice.focus()
            choice.press('Enter' if label == 'Bedrooms' else 'Space')
        expect(choice).to_have_attribute('aria-pressed', 'true')
        assert choice.bounding_box()['height'] >= 44
        if count:
            assert choice.evaluate('e => getComputedStyle(e).backgroundColor') != group.get_by_role('button', name='Any', exact=True).evaluate('e => getComputedStyle(e).backgroundColor')
    expect(page.locator('.mobile-view-toggle')).not_to_be_visible()
    expect(page.get_by_text('Match counts', exact=True)).not_to_be_visible()
    expect(page.locator('.room-filter-popover select')).to_have_count(0)
    expect(page.get_by_label('Bedrooms match', exact=True)).to_have_count(0)
    expect(page.get_by_label('Bathrooms match', exact=True)).to_have_count(0)
    expect(page.get_by_text('At least', exact=True)).not_to_be_visible()
    expect(page.get_by_text('At most', exact=True)).not_to_be_visible()
    popover = page.locator('.room-filter-popover')
    sizes = popover.evaluate('e => ({scroll: e.scrollHeight, visible: e.clientHeight})')
    assert sizes['scroll'] <= sizes['visible'], sizes
    box = popover.bounding_box()
    assert box['x'] >= 0 and box['x'] + box['width'] <= page.viewport_size['width'] + 1
    assert box['y'] + box['height'] <= page.viewport_size['height'] + 1
    return popover


def matches(value, count, mode):
    if not count:
        return True
    return {'exact': value == count, 'min': value >= count, 'max': value <= count}[mode]


with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe', headless=True)
    for width in [1920, 768, 390, 360]:
        context = browser.new_context(viewport={'width': width, 'height': 640 if width == 360 else 900 if width > 760 else 844}, has_touch=width <= 760)
        page = context.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))
        for purpose in ['sale', 'rent']:
            url = BASE + '/homes?q=Hyderabad&purpose=' + purpose
            response = page.request.get(BASE + '/api/properties?q=Hyderabad&purpose=' + purpose + '&page_size=100')
            assert response.ok
            baseline = response.json()
            assert baseline['total'] == len(baseline['items'])
            page.goto(url, wait_until='networkidle')
            expect(page.locator('.results-grid .property-card')).to_have_count(min(baseline['total'], 24))
            for mode, beds, baths in [('exact', 2, 2), ('min', 3, 2)]:
                if mode == 'exact':
                    page.get_by_role('button', name='Beds & baths', exact=True).click()
                    expect(page.get_by_label('Use exact match for bedrooms', exact=True)).not_to_be_checked()
                    expect(page.get_by_label('Use exact match for bathrooms', exact=True)).not_to_be_checked()
                    expect(page.get_by_role('group', name='Bedrooms count', exact=True).get_by_role('button', name='2+', exact=True)).to_be_visible()
                    close_filters(page)
                popover = choose(page, beds, baths, mode, mode, width <= 760)
                if mode == 'exact':
                    page.screenshot(path=str(ARTIFACTS / f'beds-baths-{purpose}-{width}.png'))
                popover.get_by_role('button', name='Apply', exact=True).click()
                expect(popover).not_to_be_visible()
                expected_ids = [row['id'] for row in baseline['items'] if row['kind'] not in NON_HOMES and matches(row['beds'], beds, mode) and matches(row['baths'], baths, mode)]
                expect(page.locator('.results-grid .property-card')).to_have_count(min(len(expected_ids), 24))
                params = parse_qs(urlparse(page.url).query)
                assert params['beds'] == [str(beds)] and params['baths'] == [str(baths)]
                assert params['beds_match'] == [mode] and params['baths_match'] == [mode]
                expect(page.locator('.applied-filters')).to_contain_text(room_label(beds, mode, 'beds'))
                expect(page.locator('.applied-filters')).to_contain_text(room_label(baths, mode, 'baths'))
                actual = page.request.get(BASE + '/api/properties?' + urlparse(page.url).query + '&page_size=100')
                assert actual.ok
                assert [row['id'] for row in actual.json()['items']] == expected_ids
                page.reload(wait_until='networkidle')
                expect(page.locator('.results-grid .property-card')).to_have_count(min(len(expected_ids), 24))
                page.get_by_role('button', name='Beds & baths', exact=True).click()
                for label in ['Bedrooms', 'Bathrooms']:
                    checkbox = page.get_by_label('Use exact match for ' + label.lower(), exact=True)
                    if mode == 'exact':
                        expect(checkbox).to_be_checked()
                    else:
                        expect(checkbox).not_to_be_checked()
                page.get_by_role('group', name='Bedrooms count', exact=True).get_by_role('button', name='Any', exact=True).click()
                close_filters(page)
                page.get_by_role('button', name='Beds & baths', exact=True).click()
                selected_name = str(beds) + ('+' if mode == 'min' else '')
                expect(page.get_by_role('group', name='Bedrooms count', exact=True).get_by_role('button', name=selected_name, exact=True)).to_have_attribute('aria-pressed', 'true')
                page.locator('.room-filter-popover').get_by_role('button', name='Clear', exact=True).click()
                expect(page.get_by_role('group', name='Bedrooms count', exact=True).get_by_role('button', name='Any', exact=True)).to_have_attribute('aria-pressed', 'true')
                expect(page.get_by_role('group', name='Bathrooms count', exact=True).get_by_role('button', name='Any', exact=True)).to_have_attribute('aria-pressed', 'true')
                page.locator('.room-filter-popover').get_by_role('button', name='Apply', exact=True).click()
                expect(page.locator('.results-grid .property-card')).to_have_count(min(baseline['total'], 24))
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            record(f'{purpose} at {width}px: plus defaults, exact-match checkboxes for 2/2, 3+/2+ without dropdowns, visible selection, touch/keyboard, real results, reload, cancel and Clear')
        context.close()

    context = browser.new_context(viewport={'width': 1440, 'height': 900})
    page = context.new_page()
    page.on('pageerror', lambda error: errors.append(str(error)))
    legacy_url = BASE + '/homes?q=Hyderabad&purpose=sale&beds=2&baths=2'
    page.goto(legacy_url, wait_until='networkidle')
    expect(page.locator('.applied-filters')).to_contain_text('2+ beds')
    page.get_by_role('button', name='Beds & baths', exact=True).click()
    expect(page.get_by_label('Use exact match for bedrooms', exact=True)).not_to_be_checked()
    expect(page.get_by_label('Use exact match for bathrooms', exact=True)).not_to_be_checked()
    close_filters(page)
    mixed = choose(page, 3, 2, 'min', 'exact')
    mixed.get_by_role('button', name='Apply', exact=True).click()
    expect(page.locator('.applied-filters')).to_contain_text('3+ beds')
    expect(page.locator('.applied-filters')).to_contain_text('Exactly 2 baths')
    record('Legacy minimum URLs and independent bedroom/bathroom exact matching work')

    registration = page.request.post(BASE + '/api/auth/register', data={'name':'Room Filter Test','email':f'room-browser-{int(time.time())}@example.com','password':'RoomTest-'+secrets.token_hex(12)})
    assert registration.status == 201
    try:
        for bed_mode, bath_mode, beds, baths in [('exact','exact',2,2),('min','min',3,2)]:
            page.goto(BASE+'/homes?q=Hyderabad&purpose=sale',wait_until='networkidle')
            popover=choose(page,beds,baths,bed_mode,bath_mode)
            popover.get_by_role('button',name='Apply',exact=True).click()
            page.get_by_role('button',name='Save search',exact=True).click()
            expect(page.locator('.toast')).to_contain_text('Search saved')
            page.get_by_role('button',name='Updates',exact=True).click()
            summary=room_label(beds, bed_mode, 'bedrooms')
            article=page.locator('.saved-search-list article').filter(has_text=summary)
            expect(article).to_contain_text(room_label(baths, bath_mode, 'bathrooms'))
            article.get_by_role('button',name='View homes').click()
            restored=parse_qs(urlparse(page.url).query)
            assert restored['beds_match']==[bed_mode] and restored['baths_match']==[bath_mode]
            expect(page.locator('.applied-filters')).to_contain_text(room_label(beds, bed_mode, 'beds'))
        legacy=page.request.post(BASE+'/api/saved-searches',data={'name':'Legacy rooms','filters':{'q':'Hyderabad','beds':2,'baths':2}})
        assert legacy.status==201
        page.goto(BASE+'/updates',wait_until='networkidle')
        article=page.locator('.saved-search-list article').filter(has_text='Legacy rooms')
        expect(article).to_contain_text('2+ bedrooms')
        article.get_by_role('button',name='View homes').click()
        expect(page.locator('.applied-filters')).to_contain_text('2+ baths')
        record('Exact and plus-count saved searches display and restore both room criteria; legacy searches stay plus counts')
    finally:
        for saved in page.request.get(BASE+'/api/saved-searches').json():
            assert page.request.delete(BASE+f'/api/saved-searches/{saved["id"]}').status==204
    context.close()
    assert not errors, errors
    record('No browser JavaScript errors')
    (ARTIFACTS/'beds-baths-results.json').write_text(json.dumps({'checks':checks,'errors':errors},indent=2)+'\n',encoding='utf-8')
    browser.close()
print(f'Completed {len(checks)} room-filter checks',flush=True)
