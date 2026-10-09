"""Check final responsive controls, filtering, and deep-linked properties."""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".tools"))
from playwright.sync_api import sync_playwright, expect

checks = []
errors = []
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe", headless=True)
    page = browser.new_page()
    page.on('pageerror', lambda error: errors.append(str(error)))
    for width in [1920, 768, 390, 360]:
        page.set_viewport_size({'width': width, 'height': 900 if width > 760 else 844})
        page.goto('http://localhost:8090/homes?q=Hyderabad&purpose=sale', wait_until='networkidle')
        expect(page.locator('.results-grid .property-card')).to_have_count(12)
        sizes = page.evaluate('({width: innerWidth, scroll: document.documentElement.scrollWidth})')
        assert sizes['scroll'] <= sizes['width'], sizes
        for button in page.locator('.filters-container button').all():
            box = button.bounding_box()
            if box:
                assert box['x'] >= 0 and box['x'] + box['width'] <= width + 1, (width, button.inner_text(), box)
        assert page.locator('.sort').evaluate("el => getComputedStyle(el).flexDirection") == 'row'
        page.screenshot(path=str(ROOT / 'artifacts' / f'final-search-{width}.png'))
        page.get_by_role('button', name='Filters', exact=True).click()
        page.get_by_label('Property type', exact=True).select_option('Villa')
        page.get_by_role('button', name='Apply filters', exact=True).click()
        expect(page.locator('.results-grid .property-card')).to_have_count(4)
        page.get_by_role('button', name='Reset', exact=True).click()
        expect(page.locator('.results-grid .property-card')).to_have_count(12)
        checks.append(f'{width}px: visible filters, no overflow, horizontal sort, property type filtering')
        print('PASS:', checks[-1], flush=True)
    page.goto('http://localhost:8090/homes?q=Hyderabad&purpose=sale&property=1', wait_until='networkidle')
    expect(page.get_by_role('dialog')).to_be_visible()
    page.get_by_role('button', name='Close dialog', exact=True).click()
    expect(page.get_by_role('dialog')).not_to_be_visible()
    assert 'property=' not in page.url
    checks.append('Deep-linked property opens and closes correctly')
    page.set_viewport_size({'width': 1920, 'height': 1080})
    page.goto('http://localhost:8090/', wait_until='networkidle')
    page.screenshot(path=str(ROOT / 'artifacts' / 'final-home.png'), full_page=True)
    page.screenshot(path=str(ROOT / 'artifacts' / 'homepage-preview.png'))
    assert not errors, errors
    (ROOT / 'artifacts' / 'layout-results.json').write_text(json.dumps({'checks': checks, 'errors': errors}, indent=2))
    browser.close()
print(f'Completed {len(checks)} final layout checks')
