"""Real price distributions and estimated loan-payment searches."""
import pytest
from test_portal import client, register, new_listing


@pytest.fixture
def price_inventory(client):
    register(client)
    ids = {}
    for purpose, prices in [('sale', [5_000_000, 10_000_000, 20_000_000]), ('rent', [10_000, 30_000, 50_000])]:
        ids[purpose] = []
        for i, price in enumerate(prices):
            body = new_listing() | {'city': 'Price Filter Test', 'purpose': purpose, 'price': price, 'beds': i + 1, 'lat': 17.4 + i * 0.01}
            response = client.post('/api/properties', json=body)
            assert response.status_code == 201, response.text
            ids[purpose].append(response.json()['id'])
    return client, ids


@pytest.mark.parametrize('purpose', ['sale', 'rent'])
def test_histogram_uses_inventory_not_price_limits(price_inventory, purpose):
    client, ids = price_inventory
    base = {'q': 'Price Filter Test', 'purpose': purpose}
    dist = client.get('/api/properties/price-distribution', params=base).json()
    assert dist['total'] == sum(dist['counts']) == 3
    assert len(dist['counts']) == 30 and dist['counts'][-1] == 1
    assert dist['domain_max'] == (20_000_000 if purpose == 'sale' else 50_000)
    limited = client.get('/api/properties/price-distribution', params=base | {'min_price': 1, 'max_price': 2}).json()
    assert limited == dist
    filtered = client.get('/api/properties/price-distribution', params=base | {'beds': 2, 'beds_match': 'exact'}).json()
    assert filtered['total'] == sum(filtered['counts']) == 1
    bounded = client.get('/api/properties/price-distribution', params=base | {'south': 17.415, 'north': 17.425, 'west': 78, 'east': 79}).json()
    assert bounded['total'] == sum(bounded['counts']) == 1
    assert bounded['counts'][-1] == 1
    assert client.get(f'/api/properties/{ids[purpose][0]}').status_code == 200


def test_empty_histogram_and_archived_inventory(price_inventory):
    client, ids = price_inventory
    empty = client.get('/api/properties/price-distribution?q=NoMatchingPriceCity').json()
    assert empty['total'] == 0 and sum(empty['counts']) == 0 and empty['domain_max'] > 0
    assert client.delete(f"/api/properties/{ids['sale'][2]}").status_code == 204
    dist = client.get('/api/properties/price-distribution?q=Price Filter Test').json()
    assert dist['total'] == sum(dist['counts']) == 2
    assert dist['domain_max'] == 10_000_000


def test_payment_filter_and_cache_financing_isolation(price_inventory):
    client, ids = price_inventory
    # Zero interest with 20% down and 20 years: payments = asking price / 300.
    base = {'q': 'Price Filter Test', 'price_mode': 'payment', 'annual_rate': 0, 'down_pct': 20, 'loan_years': 20, 'min_payment': 30_000, 'max_payment': 40_000}
    for _ in range(2):
        response = client.get('/api/properties', params=base)
        assert response.status_code == 200
        assert response.json()['total'] == 1
        assert [p['id'] for p in response.json()['items']] == [ids['sale'][1]]
        assert response.json()['items'][0]['estimated_payment'] == 33_333
    # Inactive list-price limits do not constrain payment mode.
    assert client.get('/api/properties', params=base | {'max_price': 1}).json() == response.json()
    changed = client.get('/api/properties', params=base | {'down_pct': 60}).json()
    assert [p['id'] for p in changed['items']] == [ids['sale'][2]]
    tenure = client.get('/api/properties', params=base | {'loan_years': 10}).json()
    assert [p['id'] for p in tenure['items']] == [ids['sale'][0]]
    rate = client.get('/api/properties', params=base | {'annual_rate': 8.5}).json()
    assert [p['id'] for p in rate['items']] == [ids['sale'][0]]
    assert rate['items'][0]['estimated_payment'] == 34_713
    dist = client.get('/api/properties/price-distribution', params=base).json()
    assert dist['total'] == sum(dist['counts']) == 3


def test_list_price_rent_and_pagination(price_inventory):
    client, ids = price_inventory
    base = {'q': 'Price Filter Test', 'price_mode': 'price', 'min_price': 10_000_000, 'max_price': 20_000_000, 'min_payment': 1, 'max_payment': 2}
    result = client.get('/api/properties', params=base | {'page_size': 1, 'page': 2}).json()
    assert result['total'] == 2 and result['items'][0]['id'] == ids['sale'][2]
    assert 'estimated_payment' not in result['items'][0]
    rent = client.get('/api/properties', params={'q': 'Price Filter Test', 'purpose': 'rent', 'min_price': 10_000, 'max_price': 30_000}).json()
    assert [p['id'] for p in rent['items']] == ids['rent'][:2]
    payment_page = client.get('/api/properties', params={'q': 'Price Filter Test', 'price_mode': 'payment', 'page_size': 1, 'page': 2}).json()
    assert payment_page['total'] == 3 and payment_page['items'][0]['id'] == ids['sale'][1]


@pytest.mark.parametrize('bad', [
    {'price_mode': 'invalid'}, {'price_mode': 'payment', 'purpose': 'rent'},
    {'min_price': 200, 'max_price': 100}, {'price_mode': 'payment', 'min_payment': 200, 'max_payment': 100},
    {'min_payment': -1}, {'max_payment': 20_000_001}, {'annual_rate': -1}, {'annual_rate': 26},
    {'annual_rate': 'nan'}, {'down_pct': 91}, {'loan_years': 4}, {'credit_band': 'invalid'},
])
def test_invalid_price_filters(client, bad):
    for endpoint in ['/api/properties', '/api/properties/price-distribution']:
        response = client.get(endpoint, params=bad)
        assert response.status_code == 422, response.text


def test_payment_saved_search_and_legacy_defaults(price_inventory):
    client, ids = price_inventory
    filters = {'q': 'Price Filter Test', 'price_mode': 'payment', 'min_payment': 30_000, 'max_payment': 40_000, 'annual_rate': 0, 'down_pct': 20, 'loan_years': 20, 'credit_band': '750799'}
    saved = client.post('/api/saved-searches', json={'name': 'EMI plan', 'filters': filters})
    assert saved.status_code == 201, saved.text
    assert all(saved.json()['filters'][k] == v for k, v in filters.items())
    restored = {k: v for k, v in saved.json()['filters'].items() if v is not None and v != ''}
    assert client.get('/api/properties', params=restored).json() == client.get('/api/properties', params=filters).json()
    legacy = client.post('/api/saved-searches', json={'name': 'Old list price', 'filters': {'q': 'Price Filter Test', 'max_price': 10_000_000}})
    assert legacy.status_code == 201 and legacy.json()['filters']['price_mode'] == 'price'
    assert client.post('/api/saved-searches', json={'name': 'Invalid range', 'filters': {'min_price': 2, 'max_price': 1}}).status_code == 422
    assert client.post('/api/saved-searches', json={'name': 'Rent EMI', 'filters': {'price_mode': 'payment', 'purpose': 'rent'}}).status_code == 422
