"""Account isolation, search, listing ownership, and enquiry regression tests."""
import os
os.environ["DATABASE_URL"] = "sqlite:////tmp/portal-tests.db"
os.environ["SEED_DEMO"] = "true"
os.environ["DEMO_ACCOUNTS_ENABLED"] = "true"

import pytest
from fastapi.testclient import TestClient
from app import main
from app.models import Base, engine


class FakeRedis:
    def __init__(self):
        self.values = {}
    def ping(self): return True
    def get(self, key):
        value = self.values.get(key)
        return str(value) if value is not None else None
    def setex(self, key, ttl, value): self.values[key] = value
    def incr(self, key):
        self.values[key] = int(self.values.get(key, 0)) + 1
        return self.values[key]
    def pipeline(self): return self
    def expire(self, *args, **kwargs): return self
    def execute(self): return (1, True)
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def close(self): pass


@pytest.fixture
def client(monkeypatch):
    assert engine.dialect.name == "sqlite", "Tests must never reset the portal database"
    Base.metadata.drop_all(engine)
    monkeypatch.setattr(main, "cache", FakeRedis())
    with TestClient(main.app) as client:
        yield client
    Base.metadata.drop_all(engine)


def register(client, email="first@example.com"):
    response = client.post("/api/auth/register", json={"name": "Test Owner", "email": email, "password": "long-password-123"})
    assert response.status_code == 201, response.text
    return response.json()


def new_listing():
    return {"title": "A bright 3 BHK apartment", "address": "12, Test Road, Gachibowli", "city": "Hyderabad", "state": "Telangana", "pincode": "500032", "price": 9900000, "beds": 3, "baths": 2, "sqft": 1600, "kind": "Apartment", "purpose": "sale", "lat": 17.44, "lng": 78.39, "images": ["https://example.com/photo.jpg"], "amenities": ["Parking", "Gym"], "description": "A bright and spacious apartment with a balcony and reserved parking."}


def test_search_filters_and_indian_market(client):
    results = client.get("/api/properties", params={"q": "Hyderabad", "purpose": "sale", "beds": 3, "max_price": 20000000, "sort": "price_asc"}).json()
    assert results["total"] > 0
    items = results["items"]
    assert all(p["city"] == "Hyderabad" and p["beds"] >= 3 and p["price"] <= 20000000 and p["purpose"] == "sale" for p in items)
    assert [p["price"] for p in items] == sorted(p["price"] for p in items)
    rent = client.get("/api/properties?q=Hyderabad&purpose=rent").json()
    assert rent["total"] == 8
    assert all(p["purpose"] == "rent" for p in rent["items"])


def test_search_amenities_pagination_bounds_and_agent(client):
    first = client.get("/api/properties?q=Hyderabad&page_size=2&page=1").json()
    second = client.get("/api/properties?q=Hyderabad&page_size=2&page=2").json()
    assert set(p["id"] for p in first["items"]).isdisjoint(p["id"] for p in second["items"])
    result = client.get("/api/properties?q=Bengaluru&amenity=Gym&agent=Ananya%20Sharma").json()
    assert result["total"] > 0
    assert all("Gym" in p["amenities"] and p["agent"] == "Ananya Sharma" for p in result["items"])
    empty = client.get("/api/properties?north=1&south=0&east=1&west=0").json()
    assert empty["total"] == 0
    assert client.get("/api/properties?page=0").status_code == 422


def test_auth_password_and_session_revocation(client):
    assert client.get("/api/auth/me").status_code == 401
    register(client)
    cookie = client.cookies.get("portal_session")
    assert cookie
    assert client.get("/api/auth/me").json()["email"] == "first@example.com"
    assert client.post("/api/auth/logout").status_code == 204
    client.cookies.set("portal_session", cookie, path="/api")
    assert client.get("/api/auth/me").status_code == 401
    assert client.post("/api/auth/login", json={"email": "first@example.com", "password": "bad"}).status_code == 401
    assert client.post("/api/auth/login", json={"email": "FIRST@example.com", "password": "long-password-123"}).status_code == 200


def test_duplicate_account_and_weak_password(client):
    register(client)
    assert client.post("/api/auth/register", json={"name": "Owner", "email": "first@example.com", "password": "long-password-123"}).status_code == 409
    assert client.post("/api/auth/register", json={"name": "Owner", "email": "other@example.com", "password": "short"}).status_code == 422


def test_favorites_are_idempotent_and_private(client):
    assert client.put("/api/favorites/1").status_code == 401
    register(client)
    assert client.put("/api/favorites/1").status_code == 204
    assert client.put("/api/favorites/1").status_code == 204
    assert len(client.get("/api/favorites").json()) == 1
    client.post("/api/auth/logout")
    register(client, "second@example.com")
    assert client.get("/api/favorites").json() == []
    assert client.delete("/api/favorites/1").status_code == 204
    client.post("/api/auth/logout")
    client.post("/api/auth/login", json={"email": "first@example.com", "password": "long-password-123"})
    assert len(client.get("/api/favorites").json()) == 1


def test_saved_search_ownership(client):
    register(client)
    saved = client.post("/api/saved-searches", json={"name": "Hyderabad homes", "filters": {"q": "Hyderabad", "beds": 3}})
    assert saved.status_code == 201
    search_id = saved.json()["id"]
    client.post("/api/auth/logout")
    register(client, "second@example.com")
    assert client.delete(f"/api/saved-searches/{search_id}").status_code == 404
    assert client.get("/api/saved-searches").json() == []


def test_listing_ownership_and_cache_invalidation(client):
    register(client)
    before = client.get("/api/properties?q=Hyderabad").json()["total"]
    created = client.post("/api/properties", json=new_listing())
    assert created.status_code == 201, created.text
    item = created.json()
    assert item["demo"] is False
    assert client.get("/api/properties?q=Hyderabad").json()["total"] == before + 1
    changed = new_listing() | {"price": 8800000}
    assert client.put(f'/api/properties/{item["id"]}', json=changed).status_code == 200
    assert client.get(f'/api/properties/{item["id"]}').json()["price"] == 8800000
    client.post("/api/auth/logout")
    register(client, "second@example.com")
    assert client.put(f'/api/properties/{item["id"]}', json=changed).status_code == 404
    assert client.delete(f'/api/properties/{item["id"]}').status_code == 404


def test_archive_hides_listing_and_preserves_history(client):
    register(client)
    item = client.post("/api/properties", json=new_listing()).json()
    before = client.get("/api/properties?q=Hyderabad").json()["total"]
    assert client.delete(f'/api/properties/{item["id"]}').status_code == 204
    assert client.get(f'/api/properties/{item["id"]}').status_code == 404
    assert client.get("/api/properties?q=Hyderabad").json()["total"] == before - 1
    assert client.get("/api/me/listings").json()[0]["active"] is False


def test_inquiry_routes_to_owner_and_sender_only(client):
    register(client)
    item = client.post("/api/properties", json=new_listing()).json()
    client.post("/api/auth/logout")
    register(client, "buyer@example.com")
    result = client.post("/api/inquiries", json={"property_id": item["id"], "message": "Can I visit this property?", "phone": "9876543210"})
    assert result.status_code == 201
    assert result.json()["demo"] is False
    assert client.get("/api/inquiries").json()[0]["direction"] == "sent"
    client.post("/api/auth/logout")
    register(client, "outsider@example.com")
    assert client.get("/api/inquiries").json() == []
    client.post("/api/auth/logout")
    client.post("/api/auth/login", json={"email": "first@example.com", "password": "long-password-123"})
    received = client.get("/api/inquiries").json()
    assert len(received) == 1 and received[0]["direction"] == "received"


def test_validation_and_cross_origin_write_rejection(client):
    register(client)
    assert client.post("/api/properties", json=new_listing() | {"images": ["javascript:alert(1)"]}).status_code == 422
    assert client.post("/api/properties", json=new_listing() | {"pincode": "123"}).status_code == 422
    assert client.post("/api/inquiries", json={"property_id": 1, "message": "Please share some details", "phone": "123"}).status_code == 422
    assert client.post("/api/auth/logout", headers={"Origin": "https://evil.example"}).status_code == 403
    assert client.get("/api/auth/me").status_code == 200
