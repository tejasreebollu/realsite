"""Uploaded-photo ownership and residential, commercial, plot and rental workflows."""
import io
import pytest
from PIL import Image
from app.models import SessionLocal, UploadedImage
from sqlalchemy import select
from test_portal import client, register, new_listing


@pytest.fixture
def photo_client(client, monkeypatch, tmp_path):
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "photos"))
    return client


def photo_bytes(format="PNG", size=(120, 80)):
    output = io.BytesIO()
    Image.new("RGB", size, "#73aa98").save(output, format)
    return output.getvalue()


def upload(client, content=None, filename="home.png"):
    return client.post("/api/uploads", files={"file": (filename, content or photo_bytes(), "image/png")})


def plot_body(**changes):
    return new_listing() | {"kind": "Open Plot", "beds": 0, "baths": 0, "area_unit": "sqyd", "area_value": 200,
                            "plot_use": "Residential", "plot_facing": "East", "road_width_ft": 40,
                            "plot_approval": "Owner supplied sample approval", "amenities": ["Water supply", "Electricity"]} | changes


def test_upload_authentication_reencoding_and_public_photo(photo_client):
    assert upload(photo_client).status_code == 401
    register(photo_client)
    result = upload(photo_client, filename="../../photo.svg")
    assert result.status_code == 201, result.text
    photo = result.json()
    assert photo["url"].startswith("/api/uploads/") and photo["url"].endswith(".jpg")
    response = photo_client.get(photo["url"])
    assert response.status_code == 200 and response.headers["content-type"] == "image/jpeg"
    with Image.open(io.BytesIO(response.content)) as image:
        assert image.format == "JPEG" and image.size == (120, 80)
    assert photo_client.get("/api/uploads/not-a-photo.jpg").status_code == 404
    assert photo_client.get("/api/uploads/" + "a" * 32 + ".jpg").status_code == 404


def test_upload_rejects_invalid_oversized_and_unsafe_images(photo_client, monkeypatch):
    register(photo_client)
    assert upload(photo_client, b'<svg><script>alert(1)</script></svg>').status_code == 422
    assert upload(photo_client, photo_bytes("GIF")).status_code == 422
    assert upload(photo_client, b"x" * (5 * 1024 * 1024 + 1)).status_code == 413
    monkeypatch.setattr(Image, "MAX_IMAGE_PIXELS", 100)
    assert upload(photo_client).status_code == 422
    with SessionLocal() as db:
        assert db.scalars(select(UploadedImage)).all() == []


def test_upload_rotation_and_resizing(photo_client):
    register(photo_client)
    output = io.BytesIO()
    image = Image.new("RGB", (3000, 1000), "#a8c8ef")
    exif = image.getexif()
    exif[274] = 6
    image.save(output, "JPEG", exif=exif)
    result = upload(photo_client, output.getvalue())
    assert result.status_code == 201
    assert (result.json()["width"], result.json()["height"]) == (800, 2400)
    clean = Image.open(io.BytesIO(photo_client.get(result.json()["url"]).content))
    assert not clean.getexif()


def test_upload_owner_checks_create_and_edit(photo_client):
    register(photo_client)
    url = upload(photo_client).json()["url"]
    listing = photo_client.post("/api/properties", json=new_listing() | {"images": [url]})
    assert listing.status_code == 201, listing.text
    listing_id = listing.json()["id"]
    photo_client.post("/api/auth/logout")
    register(photo_client, "other-owner@example.com")
    assert photo_client.post("/api/properties", json=new_listing() | {"images": [url]}).status_code == 422
    assert photo_client.put(f"/api/properties/{listing_id}", json=new_listing() | {"images": [url]}).status_code == 404
    assert photo_client.get(url).status_code == 200
    own_url = upload(photo_client).json()["url"]
    own_listing = photo_client.post("/api/properties", json=new_listing() | {"images": [own_url]}).json()
    assert photo_client.put(f"/api/properties/{own_listing['id']}", json=new_listing() | {"images": [url]}).status_code == 422
    assert photo_client.post("/api/properties", json=new_listing() | {"images": ["/api/uploads/" + "a" * 32 + ".jpg"]}).status_code == 422


@pytest.mark.parametrize("kind", ["Apartment", "Villa", "House", "Building", "Commercial Building", "Office", "Shop"])
@pytest.mark.parametrize("purpose", ["sale", "rent"])
def test_residential_and_commercial_sale_and_rent(client, kind, purpose):
    register(client)
    commercial = kind in {"Commercial Building", "Office", "Shop"}
    body = new_listing() | {"kind": kind, "purpose": purpose, "beds": 0 if commercial else 3, "baths": 0 if commercial else 2}
    if purpose == "rent":
        body |= {"deposit": 90000, "furnishing": "Furnished", "available_from": "2026-12-01"}
    result = client.post("/api/properties", json=body)
    assert result.status_code == 201, result.text
    record = result.json()
    matches = client.get("/api/properties", params={"q": "Hyderabad", "kind": kind, "purpose": purpose}).json()["items"]
    assert any(item["id"] == record["id"] for item in matches)
    if purpose == "rent":
        assert (record["deposit"], record["furnishing"], record["available_from"]) == (90000, "Furnished", "2026-12-01")


@pytest.mark.parametrize("unit,value,expected", [("sqyd", 200, 1800), ("sqft", 2100, 2100), ("acre", .5, 21780)])
def test_plot_units_discovery_favourites_enquiries_and_owner_edit(client, unit, value, expected):
    owner = register(client)
    result = client.post("/api/properties", json=plot_body(area_unit=unit, area_value=value))
    assert result.status_code == 201, result.text
    plot = result.json()
    assert plot["sqft"] == expected and plot["area_unit"] == unit and plot["area_value"] == value
    assert plot["beds"] == plot["baths"] == 0 and plot["owner_id"] == owner["id"]
    assert client.get("/api/properties?kind=Open%20Plot").json()["total"] == 1
    client.post("/api/auth/logout")
    register(client, "plot-customer@example.com")
    assert client.put(f"/api/favorites/{plot['id']}").status_code == 204
    assert client.get("/api/favorites").json()[0]["kind"] == "Open Plot"
    assert client.post("/api/inquiries", json={"property_id": plot["id"], "message": "Please arrange a visit to this plot.", "phone": "9876543210"}).status_code == 201
    assert client.put(f"/api/properties/{plot['id']}", json=plot_body()).status_code == 404
    client.post("/api/auth/logout")
    client.post("/api/auth/login", json={"email": "first@example.com", "password": "long-password-123"})
    assert client.get("/api/inquiries").json()[0]["direction"] == "received"
    assert client.put(f"/api/properties/{plot['id']}", json=plot_body(area_unit=unit, area_value=value, price=1234567)).status_code == 200
    assert client.delete(f"/api/properties/{plot['id']}").status_code == 204
    assert client.get("/api/properties?kind=Open%20Plot").json()["total"] == 0


def test_plot_and_rental_business_validation(client):
    register(client)
    for changes in [{"purpose": "rent"}, {"beds": 1}, {"baths": 1}, {"area_value": 10000000, "area_unit": "acre"}, {"area_value": .0001, "area_unit": "sqft"}, {"deposit": 1000}]:
        assert client.post("/api/properties", json=plot_body(**changes)).status_code == 422
    assert client.post("/api/properties", json=new_listing() | {"kind": "Office", "beds": 3}).status_code == 422
    assert client.post("/api/properties", json=new_listing() | {"purpose": "rent", "available_from": "invalid"}).status_code == 422
    assert client.post("/api/properties", json=new_listing() | {"deposit": 90000}).status_code == 422
    assert client.post("/api/properties", json=new_listing() | {"area_unit": "sqyd"}).status_code == 422
