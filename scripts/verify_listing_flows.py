"""Live sale, plot, commercial rental, image and map-picker verification."""
import json
import hashlib
import secrets
import sys
import time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".tools"))
from playwright.sync_api import sync_playwright, expect

BASE = "http://localhost:8090"
ARTIFACTS = ROOT / "artifacts"
ARTIFACTS.mkdir(exist_ok=True)
checks, errors, created, photos = [], [], [], []


def check(label):
    checks.append(label)
    print("PASS:", label, flush=True)


with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe", headless=True)
    context = browser.new_context(viewport={"width": 1440, "height": 1000})
    page = context.new_page()
    page.on("pageerror", lambda error: errors.append(str(error)))
    response = context.request.post(BASE + "/api/auth/register", data={"name": "Listing Browser Test", "email": "listing-browser-" + str(int(time.time())) + "@example.com", "password": "ListingTest-" + secrets.token_hex(12)})
    assert response.ok and response.json()["role"] == "user"
    owner_id = response.json()["id"]
    check("One regular user account handles all listing forms")
    suffix = str(int(time.time()))
    try:
        for mode, choice, kind in [("sale", "Sell a property", "Commercial Building"),
                                   ("plot", "Sell an open plot", "Open Plot"),
                                   ("rent", "Rent a property", "Office")]:
            page.goto(BASE + "/manage", wait_until="networkidle")
            page.get_by_role("button", name="Add a listing", exact=True).click()
            expect(page.locator(".listing-type-card")).to_have_count(3)
            page.get_by_role("button", name=choice, exact=True).click()
            title = "Browser " + mode + " property " + suffix
            page.get_by_label("Listing title", exact=True).fill(title)
            page.get_by_label("What makes this property special?", exact=True).fill("Fictional browser demonstration property with good road access and clear boundaries.")
            if mode == "plot":
                expect(page.get_by_label("Bedrooms", exact=True)).to_have_count(0)
                expect(page.get_by_label("Bathrooms", exact=True)).to_have_count(0)
                page.get_by_label("Plot area", exact=True).fill("200")
                page.get_by_label("Area unit", exact=True).select_option("sqyd")
                page.get_by_label("Facing (optional)", exact=True).select_option("East")
                page.get_by_label("Road width in feet (optional)", exact=True).fill("40")
                page.get_by_label("Layout / authority approval (optional)", exact=True).fill("Owner supplied sample approval")
                page.get_by_label("Selling price (₹)", exact=True).fill("6500000")
            else:
                options = page.get_by_label("Property type", exact=True).locator("option").all_text_contents()
                assert options == ["Apartment", "Villa", "House", "Building", "Commercial Building", "Office", "Shop"], options
                page.get_by_label("Property type", exact=True).select_option(kind)
                expect(page.get_by_label("Bedrooms", exact=True)).to_have_count(0)
                page.get_by_label("Built-up area (sqft)", exact=True).fill("1800")
                if mode == "rent":
                    page.get_by_label("Monthly rent (₹)", exact=True).fill("65000")
                    page.get_by_label("Security deposit (₹)", exact=True).fill("130000")
                    page.get_by_label("Furnishing", exact=True).select_option("Furnished")
                    page.get_by_label("Available from (optional)", exact=True).fill("2026-12-01")
                else:
                    page.get_by_label("Selling price (₹)", exact=True).fill("12500000")
            check(choice + " shows the appropriate property-specific fields")
            page.get_by_role("button", name="Next: location", exact=True).click()
            page.get_by_label("Address", exact=True).fill("22, Demo Road, Gachibowli")
            page.get_by_label("PIN code", exact=True).fill("500032")
            expect(page.get_by_label("Latitude", exact=True)).to_have_count(0)
            expect(page.get_by_label("Longitude", exact=True)).to_have_count(0)
            page.get_by_role("button", name="Next: photos", exact=True).click()
            expect(page.get_by_text("Please select your property location on the map.", exact=True)).to_be_visible()
            page.locator(".listing-location-map .leaflet-container").click(position={"x": 270, "y": 120})
            expect(page.locator(".listing-pin-icon")).to_have_count(1)
            page.get_by_role("button", name="Move pin north", exact=True).click()
            page.get_by_role("button", name="Next: photos", exact=True).click()
            page.get_by_role("button", name="Back", exact=True).click()
            expect(page.locator(".listing-pin-icon")).to_have_count(1)
            page.get_by_role("button", name="Next: photos", exact=True).click()
            upload = page.get_by_label("Upload property photos", exact=True)
            upload.set_input_files({"name": "bad.svg", "mimeType": "image/svg+xml", "buffer": b"<svg/>"})
            expect(page.get_by_text("Choose JPEG, PNG or WebP photos, each 5 MB or smaller.", exact=True)).to_be_visible()
            upload.set_input_files([str(ROOT / "frontend/public/images/home-1.jpg"), str(ROOT / "frontend/public/images/home-2.jpg")])
            expect(page.locator(".listing-photo-grid figure")).to_have_count(2)
            expect(page.get_by_role("button", name="Next: review", exact=True)).to_be_enabled()
            second = page.locator(".listing-photo-grid figure img").nth(1).get_attribute("src")
            page.get_by_role("button", name="Set photo 2 as cover", exact=True).click()
            expect(page.locator(".listing-photo-grid figure img").first).to_have_attribute("src", second)
            page.get_by_role("button", name="Remove photo 2", exact=True).click()
            expect(page.locator(".listing-photo-grid figure")).to_have_count(1)
            page.get_by_role("button", name="Next: review", exact=True).click()
            expect(page.get_by_role("region", name="Review your listing")).to_contain_text(title)
            page.screenshot(path=str(ARTIFACTS / ("listing-" + mode + "-review.png")))
            with page.expect_response(lambda result: result.url.endswith("/api/properties") and result.request.method == "POST") as published:
                page.get_by_role("button", name="Publish listing", exact=True).click()
            result = published.value
            assert result.status == 201, result.text()
            listing = result.json()
            created.append(listing["id"])
            photos.extend(listing["images"])
            assert listing["kind"] == kind and listing["images"] == [second]
            assert 6 <= listing["lat"] <= 38 and 68 <= listing["lng"] <= 98
            if mode == "plot":
                assert listing["sqft"] == 1800 and listing["area_unit"] == "sqyd" and listing["area_value"] == 200
            if mode == "rent":
                assert listing["deposit"] == 130000 and listing["furnishing"] == "Furnished"
            check(choice + " publishes with a selected map pin and uploaded cover image")
            page.goto(BASE + "/homes?q=Hyderabad&purpose=" + ("rent" if mode == "rent" else "sale") + "&kind=" + kind.replace(" ", "%20"), wait_until="networkidle")
            card = page.locator('.results-grid .property-card[data-property-id="' + str(listing["id"]) + '"]')
            expect(card).to_be_visible()
            expect(card.locator(".property-spec")).not_to_contain_text("bds")
            if mode == "plot":
                expect(card.locator(".property-spec")).to_contain_text("200 sq yd")
                expect(page.get_by_role("button", name="Beds & baths", exact=True)).to_have_count(0)
            card.locator(".image-open").click()
            page.get_by_role("button", name="Facts & features", exact=True).click()
            if mode == "plot":
                expect(page.locator(".facts")).to_contain_text("Owner supplied sample approval")
                expect(page.locator(".detail-specs")).not_to_contain_text("beds")
                assert "BHK" not in page.locator(".contact-card textarea[name=message]").input_value()
            elif mode == "rent":
                expect(page.locator(".facts")).to_contain_text("Furnished")
                expect(page.locator(".facts")).to_contain_text("1,30,000")
            else:
                expect(page.locator(".facts")).to_contain_text("Commercial Building")
            page.get_by_role("button", name="Close dialog", exact=True).click()
            check(choice + " appears in search with correct cards and facts")
        for width in [1280, 1101, 390, 360]:
            page.set_viewport_size({"width": width, "height": 844})
            page.goto(BASE + "/manage", wait_until="networkidle")
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            if width > 1100:
                left = page.locator(".header-left").bounding_box()
                right = page.locator(".header-right").bounding_box()
                assert left["x"] + left["width"] <= right["x"], (width, left, right)
            page.get_by_role("button", name="Add a listing", exact=True).click()
            expect(page.locator(".listing-type-card")).to_have_count(3)
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            page.screenshot(path=str(ARTIFACTS / f"listing-choices-{width}.png"))
            page.get_by_role("button", name="Sell an open plot", exact=True).click()
            expect(page.get_by_label("Plot area", exact=True)).to_be_visible()
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            page.get_by_role("button", name="Close dialog", exact=True).click()
        check("Listing choices and plot forms fit desktop and mobile widths")
        assert not errors, errors
        check("No JavaScript errors in the new listing flows")
        photo_hashes = {url: hashlib.sha256(context.request.get(BASE + url).body()).hexdigest() for url in photos}
    finally:
        for listing_id in created:
            result = context.request.delete(BASE + f"/api/properties/{listing_id}")
            assert result.status == 204
        browser.close()
(ARTIFACTS / "listing-results.json").write_text(json.dumps({"checks": checks, "errors": errors, "created_then_archived": created, "photo_urls": photos, "photo_hashes": photo_hashes, "owner_id": owner_id}, indent=2), encoding="utf-8")
print(f"{len(checks)} listing checks passed")
