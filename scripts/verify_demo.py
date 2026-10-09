"""Verify the generic user and admin demos against the running Docker app."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.tools'))
from playwright.sync_api import sync_playwright, expect

BASE = 'http://localhost:8090'
ARTIFACTS = ROOT / 'artifacts'
ARTIFACTS.mkdir(exist_ok=True)
checks, errors = [], []


def check(label):
    checks.append(label)
    print('PASS:', label, flush=True)


def sign_in(page, role):
    page.goto(BASE, wait_until='networkidle')
    if page.get_by_role('button', name='Sign out', exact=True).count():
        page.get_by_role('button', name='Sign out', exact=True).click()
    page.get_by_role('button', name='Sign in', exact=True).click()
    email, password = ('demouser@demo.example.com', 'DemoUser@2026') if role == 'user' else ('admin@demo.example.com', 'AdminDemo@2026')
    page.get_by_label('Email address', exact=True).fill(email)
    page.get_by_label('Password', exact=True).fill(password)
    page.get_by_role('dialog').locator('form').get_by_role('button', name='Sign in', exact=True).click()
    expect(page.get_by_role('dialog', name='Welcome home')).not_to_be_visible()
    expect(page.locator('.account .role-badge')).to_have_text(role)


with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe', headless=True)
    context = browser.new_context(viewport={'width': 1920, 'height': 1080})
    page = context.new_page()
    page.on('pageerror', lambda e: errors.append(str(e)))
    for city in ['Hyderabad', 'Bengaluru', 'Mumbai', 'Pune', 'New Delhi']:
        for purpose, count in [('sale', 12), ('rent', 8)]:
            response = context.request.get(BASE + '/api/properties', params={'q': city, 'purpose': purpose})
            assert response.ok and response.json()['total'] == count, (city, purpose, response.text())
    check('All five cities have 12 sale and 8 rental synthetic properties')

    # The obsolete demo credentials must no longer authenticate.
    for email, password in [('buyer@demo.example.com', 'BuyerDemo@2026'), ('seller@demo.example.com', 'SellerDemo@2026')]:
        assert context.request.post(BASE + '/api/auth/login', data={'email': email, 'password': password}).status == 401
    check('Old buyer and seller demo logins are removed')
    page.goto(BASE, wait_until='networkidle')
    page.get_by_role('button', name='Sign in', exact=True).click()
    page.get_by_role('button', name='Create account', exact=True).click()
    expect(page.get_by_label('Account type')).to_have_count(0)
    expect(page.get_by_text('Buy, rent, and sell homes with one account.', exact=True)).to_be_visible()
    page.get_by_role('button', name='Close dialog', exact=True).click()
    check('Registration offers one public account without a buyer/seller selector')

    sign_in(page, 'user')
    expect(page.locator('.account .account-name')).to_have_text('demouser')
    page.get_by_role('button', name='Favourites', exact=True).click()
    favorite_count = len(context.request.get(BASE + '/api/favorites').json())
    assert favorite_count >= 5
    expect(page.locator('.standalone-grid .property-card')).to_have_count(favorite_count)
    page.screenshot(path=str(ARTIFACTS / 'demo-user-favourites.png'))
    check(f'Generic demo login retains {favorite_count} saved properties')
    page.get_by_role('button', name='Updates', exact=True).click()
    search_count = len(context.request.get(BASE + '/api/saved-searches').json())
    assert search_count >= 5
    expect(page.locator('.saved-search-list article')).to_have_count(search_count)
    page.get_by_role('button', name='Inbox', exact=True).click()
    expect(page.locator('.inquiry-list article').first).to_be_visible()
    inquiries = context.request.get(BASE + '/api/inquiries').json()
    assert len(inquiries) >= 5
    check('The same user retains saved searches and enquiry history')
    page.get_by_role('button', name='Manage listings', exact=True).click()
    expect(page.locator('.managed-property')).to_have_count(100)
    page.screenshot(path=str(ARTIFACTS / 'demo-user-listings.png'))
    page.get_by_role('button', name='Edit listing', exact=True).first.click()
    expect(page.get_by_role('dialog', name='Edit your listing')).to_be_visible()
    assert page.get_by_label('Listing title', exact=True).input_value()
    page.get_by_role('button', name='Close dialog', exact=True).click()
    assert context.request.get(BASE + '/api/admin/summary').status == 403
    check('The same user manages 100 listings while administration remains protected')

    sign_in(page, 'admin')
    expect(page.get_by_role('heading', name='Portal overview')).to_be_visible()
    expect(page.locator('.admin-metrics article').first.locator('strong')).to_have_text('100')
    expect(page.locator('.admin-table tbody tr')).to_have_count(20)
    assert context.request.get(BASE + '/api/admin/summary').json()['synthetic_properties'] == 100
    page.screenshot(path=str(ARTIFACTS / 'demo-admin.png'), full_page=True)
    check('Admin login opens inventory metrics and a paginated dashboard')
    page.get_by_role('button', name='Next', exact=True).click()
    expect(page.get_by_text('100 records · page 2', exact=True)).to_be_visible()
    page.get_by_label('City', exact=True).select_option('Hyderabad')
    expect(page.get_by_text('20 records · page 1', exact=True)).to_be_visible()
    check('Admin pagination and city filters work')

    row = page.locator('.admin-table tbody tr').first
    reference = row.locator('small').first.inner_text().split(' · ')[0]
    property_id = int(reference.removeprefix('IN-'))
    row.get_by_role('button', name='Archive', exact=True).click()
    expect(page.get_by_role('region', name='Confirm listing moderation')).to_be_visible()
    page.get_by_role('button', name='Cancel', exact=True).click()
    assert context.request.get(BASE + f'/api/properties/{property_id}').ok
    row.get_by_role('button', name='Archive', exact=True).click()
    page.get_by_role('button', name='Confirm archive', exact=True).click()
    try:
        expect(page.locator('.admin-metrics article').first.locator('strong')).to_have_text('99')
        assert context.request.get(BASE + f'/api/properties/{property_id}').status == 404
        page.get_by_label('Listing status', exact=True).select_option('archived')
        target = page.locator('.admin-table tbody tr').filter(has_text=reference)
        target.get_by_role('button', name='Restore', exact=True).click()
        page.get_by_role('button', name='Confirm restore', exact=True).click()
        expect(page.locator('.admin-metrics article').first.locator('strong')).to_have_text('100')
        assert context.request.get(BASE + f'/api/properties/{property_id}').ok
    finally:
        response = context.request.patch(BASE + f'/api/admin/properties/{property_id}', data={'active': True})
        assert response.ok
    check('Admin confirmation, archival and restoration update public searches')

    page.get_by_role('button', name='Accounts', exact=True).click()
    expect(page.get_by_role('cell', name='admin@demo.example.com', exact=True)).to_be_visible()
    expect(page.get_by_role('cell', name='demouser@demo.example.com', exact=True)).to_be_visible()
    expect(page.get_by_role('cell', name='buyer@demo.example.com', exact=True)).to_have_count(0)
    expect(page.get_by_role('cell', name='seller@demo.example.com', exact=True)).to_have_count(0)
    page.get_by_role('button', name='Enquiries', exact=True).click()
    expect(page.locator('.admin-enquiries article').first).to_be_visible()
    check('Admin can review accounts and enquiry records')
    for width in [768, 390, 360]:
        page.set_viewport_size({'width': width, 'height': 844})
        page.goto(BASE + '/admin')
        expect(page.get_by_role('heading', name='Portal overview')).to_be_visible()
        expect(page.locator('.admin-table')).to_be_visible()
        widths = page.evaluate('({viewport: innerWidth, document: document.documentElement.scrollWidth})')
        assert widths['document'] <= widths['viewport'], widths
        page.screenshot(path=str(ARTIFACTS / f'demo-admin-{width}.png'))
    check('Admin dashboard works on tablet and mobile without page overflow')
    assert not errors, errors
    check('No JavaScript errors across both demo accounts')
    browser.close()

(ARTIFACTS / 'demo-results.json').write_text(json.dumps({'checks': checks, 'javascript_errors': errors}, indent=2), encoding='utf-8')
print(f'{len(checks)} demo checks passed')
