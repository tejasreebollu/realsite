"""Create a local environment file and fetch illustrative photos (only if missing)."""
from pathlib import Path
import secrets
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
env = ROOT / ".env"
if not env.exists():
    env.write_text((ROOT / ".env.example").read_text().replace("replace-with-a-long-random-password", secrets.token_hex(24)), encoding="utf-8")
    print("Created .env with a random local database password")

photos = [
    "photo-1600596542815-ffad4c1539a9",
    "photo-1600585154340-be6161a56a0c",
    "photo-1600047509807-ba8f99d2cdde",
    "photo-1600566753086-00f18fb6b3ea",
    "photo-1600607687939-ce8a6c25118c",
    "photo-1600607687920-4e2a09cf159d",
    "photo-1600047509782-20d39509f26d",
    "photo-1600585154526-990dced4db0d",
    "photo-1570129477492-45c003edd2be",
    "photo-1564013799919-ab600027ffc6",
    "photo-1512917774080-9991f1c4c750",
    "photo-1600566753190-17f0baa2a6c3",
]
images = ROOT / "frontend" / "public" / "images"
images.mkdir(parents=True, exist_ok=True)
assets = [(f"home-{i + 1}.jpg", photo, 900) for i, photo in enumerate(photos)]
assets += [("hero.jpg", photos[1], 2200), ("interior.jpg", "photo-1600210492486-724fe5c67fb0", 1200)]
for name, photo, width in assets:
    destination = images / name
    if destination.exists() and destination.stat().st_size > 1000:
        continue
    url = f"https://images.unsplash.com/{photo}?auto=format&fit=crop&w={width}&q=85"
    request = urllib.request.Request(url, headers={"User-Agent": "IndiaRealEstateDemo/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        data = response.read()
        if not response.headers.get("Content-Type", "").startswith("image/"):
            raise RuntimeError(f"Not an image: {name}")
    destination.write_bytes(data)
    print(f"Downloaded {name}: {len(data)} bytes")
print("Local configuration and assets ready")
