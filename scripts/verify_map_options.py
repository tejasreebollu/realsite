"""Verify map options, real satellite imagery, street links, and mobile placement."""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.tools'))
from playwright.sync_api import sync_playwright, expect

checks, errors, satellite_status = [], [], []

def check(message):
    checks.append(message)
    print('PASS:', message, flush=True)

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe', headless=True)
    page = browser.new_page(viewport={'width': 1920, 'height': 1080})
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.on('response', lambda response: satellite_status.append(response.status) if 'World_Imagery/MapServer/tile/' in response.url else None)
    page.goto('http://localhost:8090/homes?q=Hyderabad&purpose=rent', wait_until='networkidle')
    expect(page.locator('.results-grid .property-card')).to_have_count(8)
    toggle = page.get_by_role('button', name='Map options', exact=True)
    toggle.click()
    panel = page.get_by_role('region', name='Map options', exact=True)
    expect(panel).to_be_visible()
    expect(panel.get_by_role('radio')).to_have_count(9)
    expect(panel.get_by_role('radio', name='Automatic', exact=True)).to_be_checked()
    expect(panel.get_by_role('radio', name='None selected', exact=True)).to_be_checked()
    expect(panel.get_by_role('radio', name='Automatic', exact=True)).to_be_focused()
    for radio in panel.get_by_role('radio').all():
        box = radio.bounding_box()
        assert 20 <= box['width'] <= 30 and abs(box['width'] - box['height']) < 1, box
        assert radio.evaluate("el => getComputedStyle(el).borderRadius") == '50%'
    page.screenshot(path=str(ROOT / 'artifacts' / 'map-options-desktop.png'))
    check('Map Options matches the view choices and six climate choices, with keyboard focus')

    panel.get_by_role('radio', name='Satellite', exact=True).check()
    page.wait_for_function("Array.from(document.querySelectorAll('.leaflet-tile')).some(i => i.src.includes('World_Imagery') && i.complete && i.naturalWidth > 0)", timeout=30000)
    expect(page.locator('.leaflet-control-attribution')).to_contain_text('Esri')
    expect(page.locator('.price-marker')).to_have_count(8)
    page.screenshot(path=str(ROOT / 'artifacts' / 'map-options-satellite.png'))
    check('Satellite loads actual imagery, credits the provider, and retains listing pins')

    for risk in ['Wind', 'Flood', 'Air', 'Fire', 'Heat']:
        panel.get_by_role('radio', name=risk, exact=True).check()
        expect(panel.get_by_role('status')).to_contain_text(f'{risk} risk data is unavailable')
    panel.get_by_role('radio', name='None selected', exact=True).check()
    expect(panel.locator('.climate-unavailable')).to_have_count(0)
    check('Climate selections report missing data explicitly; None selected clears the status')

    panel.get_by_role('radio', name='Street view', exact=True).check()
    link = panel.get_by_role('link', name='Open in Google Maps')
    assert 'map_action=pano' in link.get_attribute('href') and 'viewpoint=' in link.get_attribute('href')
    assert link.get_attribute('target') == '_blank'
    page.keyboard.press('Escape')
    expect(panel).not_to_be_visible()
    expect(toggle).to_be_focused()
    expect(page.get_by_role('link', name='Open Street View', exact=True)).to_be_visible()
    check('Street view targets the map centre in Google Maps; Escape restores focus')

    toggle.click()
    panel.get_by_role('radio', name='Automatic', exact=True).check()
    page.wait_for_function("Array.from(document.querySelectorAll('.leaflet-tile')).some(i => i.src.includes('tile.openstreetmap.org') && i.complete && i.naturalWidth > 0)")
    expect(page.locator('.leaflet-control-attribution')).not_to_contain_text('Esri')
    page.locator('.results-heading h1').click()
    expect(panel).not_to_be_visible()
    check('Automatic restores the map and correct credits; outside click closes the menu')

    for width, height in [(768, 900), (390, 844), (360, 640)]:
        page.set_viewport_size({'width': width, 'height': height})
        if width == 390:
            page.get_by_role('button', name='Map', exact=True).click()
        expect(toggle).to_be_visible()
        toggle.click()
        expect(panel).to_be_visible()
        box, map_box = panel.bounding_box(), page.locator('.map-pane').bounding_box()
        assert box['x'] >= map_box['x'] and box['x'] + box['width'] <= map_box['x'] + map_box['width'] + 1, (width, box, map_box)
        assert box['y'] >= map_box['y'] and box['y'] + box['height'] <= map_box['y'] + map_box['height'] + 1, (width, box, map_box)
        for radio in panel.get_by_role('radio').all():
            size = radio.bounding_box()
            assert size['width'] <= 30 and abs(size['width'] - size['height']) < 1, size
        if width <= 760:
            switch = page.get_by_role('button', name='List', exact=True).bounding_box()
            control = toggle.bounding_box()
            assert switch['x'] + switch['width'] <= control['x'], (width, switch, control)
        panel.get_by_role('radio', name='Heat', exact=True).check()
        expect(panel.get_by_role('status')).to_contain_text('No climate overlay')
        page.screenshot(path=str(ROOT / 'artifacts' / f'map-options-{width}.png'))
        panel.get_by_role('radio', name='None selected', exact=True).check()
        page.keyboard.press('Escape')
        check(f'{width}px: menu stays within the map; controls work even in a short viewport')
    assert not errors, errors
    assert 200 in satellite_status, satellite_status
    (ROOT / 'artifacts' / 'map-options-results.json').write_text(json.dumps({'checks': checks, 'javascript_errors': errors, 'satellite_http_statuses': sorted(set(satellite_status))}, indent=2))
    browser.close()
print(f'Completed {len(checks)} map option checks')
