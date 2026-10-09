"""Exact and maximum room counts, mixed matching, cache isolation and saved searches."""
import pytest
from test_portal import client, register, new_listing


@pytest.fixture
def inventory(client):
    register(client)
    ids = {}
    for purpose in ['sale', 'rent']:
        ids[purpose] = []
        for beds, baths in [(1, 1), (2, 2), (3, 2), (4, 3)]:
            body = new_listing() | {'city': 'Room Matching Test', 'purpose': purpose, 'beds': beds, 'baths': baths}
            response = client.post('/api/properties', json=body)
            assert response.status_code == 201, response.text
            ids[purpose].append(response.json()['id'])
        commercial = new_listing() | {'city': 'Room Matching Test', 'purpose': purpose, 'kind': 'Office', 'beds': 0, 'baths': 2}
        assert client.post('/api/properties', json=commercial).status_code == 201
    plot = new_listing() | {'city': 'Room Matching Test', 'kind': 'Open Plot', 'beds': 0, 'baths': 0, 'area_value': 1600, 'plot_use': 'Residential'}
    assert client.post('/api/properties', json=plot).status_code == 201
    return client, ids


@pytest.mark.parametrize('purpose', ['sale', 'rent'])
@pytest.mark.parametrize('mode,beds,baths,indexes', [('exact', 2, 2, [1]), ('max', 3, 2, [0, 1, 2]), ('min', 2, 2, [1, 2, 3])])
def test_room_matching_modes(inventory, purpose, mode, beds, baths, indexes):
    client, ids = inventory
    params = {'q': 'Room Matching Test', 'purpose': purpose, 'beds': beds, 'baths': baths, 'beds_match': mode, 'baths_match': mode}
    expected = [ids[purpose][i] for i in indexes]
    for _ in range(2):  # The second request also exercises cached search results.
        response = client.get('/api/properties', params=params)
        assert response.status_code == 200
        assert response.json()['total'] == len(expected)
        assert [row['id'] for row in response.json()['items']] == expected
    paginated = client.get('/api/properties', params=params | {'page_size': 1}).json()
    assert paginated['total'] == len(expected)
    assert paginated['items'][0]['id'] == expected[0]


def test_independent_room_modes_any_and_cache_isolation(inventory):
    client, ids = inventory
    base = {'q': 'Room Matching Test', 'beds': 3, 'baths': 2}
    mixed = client.get('/api/properties', params=base | {'beds_match': 'max', 'baths_match': 'exact'}).json()
    assert [p['id'] for p in mixed['items']] == ids['sale'][1:3]
    exact = client.get('/api/properties', params=base | {'beds_match': 'exact', 'baths_match': 'exact'}).json()
    assert [p['id'] for p in exact['items']] == [ids['sale'][2]]
    bathrooms_only = client.get('/api/properties', params=base | {'beds': 0, 'beds_match': 'exact', 'baths_match': 'exact'}).json()
    assert [p['id'] for p in bathrooms_only['items']] == ids['sale'][1:3]
    any_result = client.get('/api/properties', params=base | {'beds': 0, 'baths': 0, 'beds_match': 'exact', 'baths_match': 'max'}).json()
    assert any_result['total'] == 6  # Four homes, office and plot with no room constraint.


def test_room_matching_saved_search_and_legacy_defaults(inventory):
    client, ids = inventory
    legacy = {'q': 'Room Matching Test', 'beds': 2, 'baths': 2}
    assert [p['id'] for p in client.get('/api/properties', params=legacy).json()['items']] == ids['sale'][1:]
    for modes in [{'beds_match': 'exact', 'baths_match': 'exact'}, {'beds_match': 'max', 'baths_match': 'min'}, {}]:
        filters = legacy | modes
        response = client.post('/api/saved-searches', json={'name': 'Room search', 'filters': filters})
        assert response.status_code == 201, response.text
        saved = response.json()
        assert saved['filters']['beds_match'] == modes.get('beds_match', 'min')
        assert saved['filters']['baths_match'] == modes.get('baths_match', 'min')
        restored_response = client.get('/api/properties', params={k: v for k, v in saved['filters'].items() if v is not None and v != ''})
        assert restored_response.status_code == 200
        assert restored_response.json() == client.get('/api/properties', params=filters).json()
        restored = next(s for s in client.get('/api/saved-searches').json() if s['id'] == saved['id'])
        assert restored['filters'] == saved['filters']


def test_room_matching_rejects_invalid_modes_and_counts(client):
    for params in [{'beds_match': 'less'}, {'baths_match': 'invalid'}, {'beds': 21}, {'baths': -1}]:
        assert client.get('/api/properties', params=params).status_code == 422
    assert client.post('/api/auth/register', json={'name': 'Room Test', 'email': 'rooms@example.com', 'password': 'RoomTestPassword123'}).status_code == 201
    assert client.post('/api/saved-searches', json={'name': 'Bad mode', 'filters': {'beds_match': 'less'}}).status_code == 422
