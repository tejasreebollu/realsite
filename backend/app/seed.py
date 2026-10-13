import random
from sqlalchemy import select
from .models import AuthSession, Favorite, Inquiry, Property, SavedSearch, UploadedImage, User
from .passwords import hash_password
from .demo_pricing import scenario_price

CITIES = {
    "Hyderabad": {"state": "Telangana", "lat": 17.4401, "lng": 78.3910, "pin": "500032", "areas": ["Gachibowli", "Jubilee Hills", "Kondapur", "Banjara Hills", "Kokapet", "Madhapur"]},
    "Bengaluru": {"state": "Karnataka", "lat": 12.9716, "lng": 77.5946, "pin": "560001", "areas": ["Whitefield", "Indiranagar", "Sarjapur Road", "Koramangala", "HSR Layout", "Hebbal"]},
    "Mumbai": {"state": "Maharashtra", "lat": 19.0760, "lng": 72.8777, "pin": "400001", "areas": ["Bandra West", "Powai", "Andheri West", "Worli", "Juhu", "Goregaon"]},
    "Pune": {"state": "Maharashtra", "lat": 18.5204, "lng": 73.8567, "pin": "411001", "areas": ["Baner", "Koregaon Park", "Hinjewadi", "Kharadi", "Wakad", "Viman Nagar"]},
    "New Delhi": {"state": "Delhi", "lat": 28.6139, "lng": 77.2090, "pin": "110001", "areas": ["Greater Kailash", "Vasant Kunj", "Dwarka", "Hauz Khas", "Defence Colony", "Saket"]},
}


def seed(db):
    """Create 100 stable demo rows; preserve edits, archives and customer records."""
    import os
    accounts = {}
    initialise_user = False
    if os.getenv("DEMO_ACCOUNTS_ENABLED", "false").lower() == "true":
        _, had_legacy = consolidate_demo_users(db)
        for role, name, email, password in DEMO_ACCOUNTS:
            user = db.scalar(select(User).where(User.email == email))
            if user is None:
                user = User(name=name, email=email, role=role, demo=True, password_hash=hash_password(password))
                db.add(user)
                db.flush()
                if role == "user" and not had_legacy:
                    initialise_user = True
            elif not user.demo or (user.role != role and not (role == "user" and user.role == "agent")):
                raise RuntimeError(f"Reserved demo email already belongs to another account: {email}")
            accounts[role] = user
    rng = random.Random(42)
    badges = ["Beautifully renovated", "Spacious balcony", "Move-in ready", "Garden views", "Gated community", "New listing", "Open terrace", "Modern finishes"]
    sample = {}
    for city, info in CITIES.items():
        for i in range(24):
            rent = i >= 16
            area = info["areas"][i % 6]
            beds = [3, 4, 2, 3, 4, 2, 3, 5][i % 8]
            sqft = beds * 450 + rng.randrange(100, 600, 50)
            # Retain the old random draw so seeded coordinates and sizes stay stable.
            rng.randrange(24, 95) if rent else rng.randrange(65, 380)
            price = scenario_price(city, i, sqft, ["Apartment", "Villa", "House"][i % 3], "rent" if rent else "sale")
            image = i % 12 + 1
            values = dict(title=f"{beds} BHK {['Apartment', 'Villa', 'Independent house'][i % 3]} in {area}", address=f"{12 + i}, {area} Road, {area}", city=city, state=info["state"], pincode=info["pin"], price=price, beds=beds, baths=max(2, beds - 1), sqft=sqft, kind=["Apartment", "Villa", "House"][i % 3], purpose="rent" if rent else "sale", lat=info["lat"] + rng.uniform(-0.07, 0.07), lng=info["lng"] + rng.uniform(-0.07, 0.07), images=[f"/images/home-{image}.jpg", f"/images/home-{(image + 2) % 12 + 1}.jpg", "/images/interior.jpg"], amenities=["Parking", "Security", "Power backup", "Balcony"] + (["Swimming pool", "Gym"] if i % 2 == 0 else ["Garden"]), description=f"Discover a beautifully designed {beds}-bedroom home in {area}, {city}. Bright living spaces, thoughtful finishes, and a spacious layout make room for everything you love. Enjoy easy access to local shops, schools, and everyday essentials. This is a fictional demonstration listing; photos are illustrative and are not photographs of an actual property at this address.", badge=badges[i % len(badges)], agent=["Ananya Sharma", "Arjun Reddy", "Priya Mehta", "Vikram Rao"][i % 4], demo=True)
            key = f"india-demo-v2:{city}:{i}"
            item = db.scalar(select(Property).where(Property.seed_key == key))
            if item is None:
                # Adopt only recognisable, unowned rows from the old 120-home seed.
                item = db.scalar(select(Property).where(Property.seed_key.is_(None), Property.demo.is_(True), Property.owner_id.is_(None), Property.city == city, Property.address == values["address"], Property.title == values["title"], Property.agent == values["agent"]))
                if item is not None:
                    item.seed_key = key
            if 12 <= i < 16:
                # Archive the old surplus without deleting favourites or enquiries.
                if item is not None:
                    item.active = False
                continue
            if item is None:
                item = Property(**values, seed_key=key)
                db.add(item)
            if item.features is None:
                # Populate new demo attributes once; retain owner edits on restarts.
                item.features = {
                    "posted_by": ["Owner", "Broker", "Builder"][i % 3],
                    "listing_status": ["Available", "Available", "Coming soon", "Under offer"][i % 4],
                    "sale_type": "" if rent else ["Resale", "New project", "Resale", "Bank auction"][i % 4],
                    "possession": "Under construction" if not rent and i % 4 == 2 else "Ready to move",
                    "ownership": "Leasehold" if i % 7 == 0 else "Freehold",
                    "maintenance": [0, 1500, 3000, 5000][i % 4], "parking": i % 3,
                    "covered_parking": i % 2 == 0, "carpet_sqft": round(item.sqft * .75),
                    "plot_sqft": item.sqft * 2 if item.kind != "Apartment" else None,
                    "year_built": 2005 + i % 20, "floors": 1 if i % 3 == 2 else 2 + i % 4,
                    "basement": i % 6 == 0, "senior_living": i % 9 == 0,
                    "facing": ["North", "East", "West", "South"][i % 4],
                    "views": [["City"], ["Park"], ["Hills"], ["Water"]][i % 4],
                    "site_visit": i % 2 == 0,
                    "tour_3d_url": "/tours/demo-3d.html" if i % 3 == 0 else "",
                    "video_url": "", "rera_id": f"DEMO-{city[:3].upper()}-{i:03}" if i % 4 == 1 else "",
                }
                if item.previous_price is None and i % 5 == 0:
                    item.previous_price = round(item.price * 1.05)
            if "user" in accounts and item.owner_id is None:
                item.owner_id = accounts["user"].id
            db.flush()
            sample.setdefault(city, []).append(item)
    if initialise_user:
        user = accounts["user"]
        for city, listings in sample.items():
            item = listings[0]
            if db.get(Favorite, (user.id, item.id)) is None:
                # Initial workspace only; restarts retain later user choices.
                if not db.scalar(select(SavedSearch.id).where(SavedSearch.user_id == user.id, SavedSearch.name == f"Demo: {city}")):
                    db.add(Favorite(user_id=user.id, property_id=item.id))
            if not db.scalar(select(SavedSearch.id).where(SavedSearch.user_id == user.id, SavedSearch.name == f"Demo: {city}")):
                db.add(SavedSearch(user_id=user.id, name=f"Demo: {city}", filters={"q": city, "purpose": "sale", "beds": 3, "sort": "price_asc"}))
            message = f"Demo enquiry: I would like to learn more about this home in {city}. Please share the layout and arrange a viewing."
            if not db.scalar(select(Inquiry.id).where(Inquiry.user_id == user.id, Inquiry.property_id == item.id, Inquiry.message == message)):
                db.add(Inquiry(user_id=user.id, property_id=item.id, message=message, phone="9000000000"))
    db.commit()
    return sample


DEMO_ACCOUNTS = [
    ("user", "demouser", "demouser@demo.example.com", "DemoUser@2026"),
    ("admin", "Demo Admin", "admin@demo.example.com", "AdminDemo@2026"),
]


def consolidate_demo_users(db):
    """Merge old demo logins atomically; retain seller ID, listings and activity."""
    target = db.scalar(select(User).where(User.email == "demouser@demo.example.com"))
    legacy = []
    for email in ("seller@demo.example.com", "buyer@demo.example.com"):
        user = db.scalar(select(User).where(User.email == email))
        if user is not None:
            if not user.demo or user.role not in {"user", "buyer", "seller"}:
                raise RuntimeError(f"Reserved demo email already belongs to another account: {email}")
            legacy.append(user)
    if target is not None and (not target.demo or target.role not in {"user", "agent"}):
        raise RuntimeError("Reserved demo email already belongs to another account: demouser@demo.example.com")
    if not legacy:
        return target, False
    if target is None:
        # Reuse the old seller row so inventory ownership keeps the same ID.
        target = next((u for u in legacy if u.email == "seller@demo.example.com"), None)
        if target is None:
            target = User(name="demouser", email="demouser@demo.example.com", role="user",
                          demo=True, password_hash=hash_password("DemoUser@2026"))
            db.add(target)
            db.flush()
        else:
            previous_name = target.name
            db.query(Property).filter(Property.owner_id == target.id, Property.agent == previous_name).update(
                {Property.agent: "demouser"}, synchronize_session="fetch")
            target.name = "demouser"
            target.email = "demouser@demo.example.com"
            target.role = "user"
            target.password_hash = hash_password("DemoUser@2026")
            db.query(AuthSession).filter(AuthSession.user_id == target.id).delete()
            db.flush()
    for source in legacy:
        if source.id == target.id:
            continue
        db.query(Property).filter(Property.owner_id == source.id, Property.agent == source.name).update(
            {Property.agent: target.name}, synchronize_session="fetch")
        db.query(Property).filter(Property.owner_id == source.id).update(
            {Property.owner_id: target.id}, synchronize_session="fetch")
        for favorite in db.scalars(select(Favorite).where(Favorite.user_id == source.id)).all():
            if db.get(Favorite, (target.id, favorite.property_id)) is None:
                db.add(Favorite(user_id=target.id, property_id=favorite.property_id))
            db.delete(favorite)
        db.query(SavedSearch).filter(SavedSearch.user_id == source.id).update(
            {SavedSearch.user_id: target.id}, synchronize_session="fetch")
        db.query(UploadedImage).filter(UploadedImage.owner_id == source.id).update(
            {UploadedImage.owner_id: target.id}, synchronize_session="fetch")
        db.query(Inquiry).filter(Inquiry.user_id == source.id).update(
            {Inquiry.user_id: target.id}, synchronize_session="fetch")
        db.query(AuthSession).filter(AuthSession.user_id == source.id).delete()
        db.flush()
        db.delete(source)
        db.flush()
    return target, True
