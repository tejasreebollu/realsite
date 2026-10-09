"""Demo accounts, dataset persistence and privileged access boundaries."""
import os
os.environ["DATABASE_URL"] = "sqlite:////tmp/portal-tests.db"
os.environ["SEED_DEMO"] = "true"
os.environ["DEMO_ACCOUNTS_ENABLED"] = "true"

import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine, func, select, text
from app import main
from app.migrations import migrate
from app.models import AuthSession, Favorite, Inquiry, Property, SavedSearch, SessionLocal, User
from app.seed import CITIES, seed
from app.passwords import hash_password, verify_password
from test_portal import client, new_listing, register


def login(client, role):
    client.post('/api/auth/logout')
    email, password = ('demouser@demo.example.com', 'DemoUser@2026') if role == 'user' else ('admin@demo.example.com', 'AdminDemo@2026')
    result = client.post('/api/auth/login', json={'email': email, 'password': password})
    assert result.status_code == 200, result.text
    assert result.json()['role'] == role
    return result.json()


def test_100_properties_across_all_supported_cities(client):
    for city in CITIES:
        sale = client.get('/api/properties', params={'q': city, 'purpose': 'sale'}).json()
        rent = client.get('/api/properties', params={'q': city, 'purpose': 'rent'}).json()
        assert sale['total'] == 12 and rent['total'] == 8
        assert all(p['demo'] and p['owner_id'] for p in sale['items'] + rent['items'])
    login(client, 'user')
    assert len(client.get('/api/favorites').json()) == 5
    assert len(client.get('/api/saved-searches').json()) == 5
    assert len(client.get('/api/inquiries').json()) == 5
    user = client.get('/api/auth/me').json()
    assert user['name'] == 'demouser'
    listings = client.get('/api/me/listings').json()
    assert len(listings) == 100 and all(p['owner_id'] == user['id'] for p in listings)
    inbox = client.get('/api/inquiries').json()
    assert len(inbox) == 5 and all(i['direction'] == 'sent' for i in inbox)


def test_admin_access_and_listing_moderation(client):
    assert client.get('/api/admin/summary').status_code == 401
    for role in ['user']:
        login(client, role)
        for path in ['summary', 'properties', 'users', 'inquiries']:
            assert client.get('/api/admin/' + path).status_code == 403
        assert client.patch('/api/admin/properties/1', json={'active': False}).status_code == 403
    login(client, 'admin')
    summary = client.get('/api/admin/summary').json()
    assert summary['active_properties'] == summary['synthetic_properties'] == 100
    assert summary['sale'] == 60 and summary['rent'] == 40
    assert summary['users'] == 2 and summary['inquiries'] == 5
    assert client.get('/api/admin/properties?city=Pune&page_size=5').json()['total'] == 20
    accounts = client.get('/api/admin/users').json()['items']
    assert {u['role'] for u in accounts} == {'user', 'admin'}
    assert not any('password' in key for u in accounts for key in u)
    assert client.patch('/api/admin/properties/1', json={'active': False}).status_code == 200
    assert client.get('/api/properties/1').status_code == 404
    assert client.get('/api/admin/properties?status=archived').json()['total'] == 1
    assert client.patch('/api/admin/properties/1', json={'active': True}).status_code == 200
    assert client.get('/api/properties/1').status_code == 200


def test_public_roles_and_demo_disabled_sessions(client, monkeypatch):
    register_body = {'name': 'New User', 'email': 'newuser@example.com', 'password': 'long-password-123'}
    assert client.post('/api/auth/register', json=register_body | {'role': 'admin'}).status_code == 422
    user = client.post('/api/auth/register', json=register_body).json()
    assert user['role'] == 'user'
    assert client.post('/api/properties', json=new_listing()).status_code == 201
    assert len(client.get('/api/me/listings').json()) == 1
    assert client.put('/api/favorites/1').status_code == 204
    login(client, 'admin')
    monkeypatch.setenv('DEMO_ACCOUNTS_ENABLED', 'false')
    assert client.get('/api/admin/summary').status_code == 401
    assert client.post('/api/auth/login', json={'email': 'admin@demo.example.com', 'password': 'AdminDemo@2026'}).status_code == 403
    assert client.post('/api/auth/login', json=register_body).status_code == 200


def test_seed_retains_edits_archives_and_user_choices(client):
    owner = register(client)
    manual = client.post('/api/properties', json=new_listing()).json()
    with SessionLocal() as db:
        home = db.get(Property, 1)
        home.price = 8765432
        home.active = False
        user = db.scalar(select(User).where(User.role == 'user', User.demo.is_(True)))
        db.query(Favorite).filter(Favorite.user_id == user.id).delete()
        db.query(SavedSearch).filter(SavedSearch.user_id == user.id).delete()
        db.commit()
        seed(db)
        seed(db)
        assert db.scalar(select(func.count()).select_from(Property)) == 101
        assert db.get(Property, 1).price == 8765432 and not db.get(Property, 1).active
        assert db.get(Property, manual['id']).owner_id == owner['id']
        assert db.scalar(select(func.count()).select_from(Favorite)) == 0
        assert db.scalar(select(func.count()).select_from(SavedSearch)) == 0
        assert db.scalar(select(func.count()).select_from(Inquiry)) == 5
        assert db.scalar(select(func.count()).select_from(User).where(User.demo.is_(True))) == 2


def test_legacy_seed_upgrade_preserves_references(client):
    with SessionLocal() as db:
        homes = db.scalars(select(Property)).all()
        for home in homes:
            home.owner_id = None
            home.seed_key = None
        for city, info in CITIES.items():
            for i in range(12, 16):
                area = info['areas'][i % 6]
                beds = [3, 4, 2, 3, 4, 2, 3, 5][i % 8]
                values = new_listing() | {'title': f"{beds} BHK {['Apartment', 'Villa', 'Independent house'][i % 3]} in {area}", 'address': f'{12 + i}, {area} Road, {area}', 'city': city}
                db.add(Property(**values, demo=True, agent=['Ananya Sharma', 'Arjun Reddy', 'Priya Mehta', 'Vikram Rao'][i % 4]))
        db.commit()
        seed(db)
        seed(db)
        assert db.scalar(select(func.count()).select_from(Property)) == 120
        assert db.scalar(select(func.count()).select_from(Property).where(Property.active.is_(True))) == 100
        assert db.scalar(select(func.count()).select_from(Inquiry)) == 5
        assert all(db.get(Property, p.id).owner_id for p in homes)


def test_additive_migration_is_repeatable_and_preserves_old_accounts():
    engine = create_engine('sqlite://')
    with engine.begin() as connection:
        connection.execute(text('CREATE TABLE users (id INTEGER PRIMARY KEY, name VARCHAR(100))'))
        connection.execute(text("INSERT INTO users VALUES (7, 'Existing owner')"))
        connection.execute(text('CREATE TABLE properties (id INTEGER PRIMARY KEY, title VARCHAR(160))'))
        connection.execute(text("INSERT INTO properties VALUES (9, 'Existing home')"))
    migrate(engine)
    migrate(engine)
    with engine.connect() as connection:
        assert connection.execute(text('SELECT name, role, demo FROM users')).one() == ('Existing owner', 'user', 0)
        assert connection.execute(text('SELECT title, seed_key FROM properties')).one() == ('Existing home', None)
    engine.dispose()


def test_legacy_demo_merge_retains_ids_activity_and_revokes_old_sessions(client):
    login(client, 'user')
    with SessionLocal() as db:
        target = db.scalar(select(User).where(User.email == 'demouser@demo.example.com'))
        owner_id = target.id
        target.name, target.email = 'Demo Seller', 'seller@demo.example.com'
        target.password_hash = hash_password('SellerDemo@2026')
        buyer = User(name='Demo Buyer', email='buyer@demo.example.com', role='user',
                     demo=True, password_hash=hash_password('BuyerDemo@2026'))
        db.add(buyer)
        db.flush()
        buyer_id = buyer.id
        admin = db.scalar(select(User).where(User.role == 'admin'))
        db.add_all([Favorite(user_id=buyer_id, property_id=1), Favorite(user_id=buyer_id, property_id=2),
                    SavedSearch(user_id=buyer_id, name='Custom preserved search', filters={'q': 'Pune'}),
                    Inquiry(user_id=buyer_id, property_id=2, message='Keep this historical enquiry.', phone='9000000000'),
                    AuthSession(token_hash='a' * 64, user_id=admin.id,
                                expires_at=datetime.now(timezone.utc) + timedelta(days=1))])
        db.add(Property(**new_listing(), owner_id=buyer_id, agent='Demo Buyer', demo=False))
        db.get(Property, 1).price = 7654321
        db.get(Property, 2).active = False
        db.commit()
    old_seller = client.post('/api/auth/login', json={'email': 'seller@demo.example.com', 'password': 'SellerDemo@2026'})
    assert old_seller.status_code == 200
    old_seller_token = client.cookies.get('portal_session')
    assert client.post('/api/auth/login', json={'email': 'buyer@demo.example.com', 'password': 'BuyerDemo@2026'}).status_code == 200
    with SessionLocal() as db:
        seed(db)
        seed(db)
        target = db.get(User, owner_id)
        assert (target.name, target.email, target.role) == ('demouser', 'demouser@demo.example.com', 'user')
        assert db.get(User, buyer_id) is None
        assert db.scalar(select(func.count()).select_from(User)) == 2
        assert db.scalar(select(func.count()).select_from(Property)) == 101
        assert db.scalar(select(func.count()).select_from(Favorite)) == 6  # Overlapping favourites are combined.
        assert db.scalar(select(func.count()).select_from(SavedSearch)) == 6
        assert db.scalar(select(func.count()).select_from(Inquiry)) == 6
        assert not db.scalars(select(Property).where(Property.owner_id == buyer_id)).all()
        assert not db.scalars(select(SavedSearch).where(SavedSearch.user_id == buyer_id)).all()
        assert not db.scalars(select(Inquiry).where(Inquiry.user_id == buyer_id)).all()
        assert db.get(Property, 1).price == 7654321 and not db.get(Property, 2).active
        assert db.scalars(select(Property).where(Property.demo.is_(False))).one().agent == 'demouser'
        assert db.get(AuthSession, 'a' * 64) is not None
    assert client.get('/api/auth/me').status_code == 401
    client.cookies.clear()
    client.cookies.set('portal_session', old_seller_token, path='/api')
    assert client.get('/api/auth/me').status_code == 401
    for email, password in [('buyer@demo.example.com', 'BuyerDemo@2026'), ('seller@demo.example.com', 'SellerDemo@2026')]:
        assert client.post('/api/auth/login', json={'email': email, 'password': password}).status_code == 401
    assert login(client, 'user')['id'] == owner_id


def test_existing_generic_password_and_non_demo_accounts_are_protected(client):
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == 'demouser@demo.example.com'))
        user.password_hash = hash_password('changed-demo-password')
        db.commit()
        seed(db)
        assert verify_password('changed-demo-password', user.password_hash)
        protected = User(name='Actual customer', email='buyer@demo.example.com', role='user',
                         demo=False, password_hash=hash_password('customer-password'))
        db.add(protected)
        db.commit()
        protected_id = protected.id
        with pytest.raises(RuntimeError, match='Reserved demo email'):
            seed(db)
        db.rollback()
        assert db.get(User, protected_id).name == 'Actual customer'


def test_existing_public_roles_convert_without_affecting_admin():
    engine = create_engine('sqlite://')
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY, role VARCHAR(20), demo BOOLEAN)"))
        connection.execute(text("INSERT INTO users VALUES (1, 'buyer', 0), (2, 'seller', 0), (3, 'admin', 1)"))
        connection.execute(text("CREATE TABLE properties (id INTEGER PRIMARY KEY, seed_key VARCHAR(120))"))
    migrate(engine)
    migrate(engine)
    with engine.connect() as connection:
        assert connection.execute(text('SELECT role FROM users ORDER BY id')).scalars().all() == ['user', 'user', 'admin']
    engine.dispose()
