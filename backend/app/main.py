import hashlib
import json
import logging
import os
import secrets
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone, date
from typing import Literal
from urllib.parse import urlsplit

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from redis import Redis, RedisError
from sqlalchemy import String, func, or_, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .models import AuthSession, Base, Favorite, Inquiry, Property, SavedSearch, SessionLocal, User, engine
from .seed import CITIES, seed
from .passwords import hash_password, verify_password
from .migrations import migrate

logger = logging.getLogger(__name__)
cache = Redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"), decode_responses=True, socket_connect_timeout=2, socket_timeout=2)
SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"


@asynccontextmanager
async def lifespan(app):
    Base.metadata.create_all(engine)
    migrate(engine)
    if os.getenv("SEED_DEMO", "true").lower() == "true":
        with SessionLocal() as db:
            seed(db)
        invalidate()
    yield
    cache.close()
    engine.dispose()


app = FastAPI(title="RealSite India Real Estate API", version="1.0.0", lifespan=lifespan, docs_url="/api/docs", openapi_url="/api/openapi.json")


@app.middleware("http")
async def security_headers(request: Request, call_next):
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        origin = request.headers.get("origin")
        if origin and urlsplit(origin).netloc != request.headers.get("host"):
            return JSONResponse({"detail": "Cross-origin request rejected"}, status_code=403)
        if request.headers.get("sec-fetch-site") == "cross-site":
            return JSONResponse({"detail": "Cross-site request rejected"}, status_code=403)
        if int(request.headers.get("content-length", "0")) > (6 * 1024 * 1024 if request.url.path.rstrip("/") == "/api/uploads" else 100_000):
            return JSONResponse({"detail": "Request too large"}, status_code=413)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if request.url.path.startswith(("/api/auth", "/api/me", "/api/admin", "/api/favorites", "/api/inquiries", "/api/saved-searches")):
        response.headers["Cache-Control"] = "no-store"
    return response


def database():
    with SessionLocal() as db:
        yield db


def current_user(request: Request, db: Session = Depends(database)):
    token = request.cookies.get("portal_session", "")
    session = db.get(AuthSession, hashlib.sha256(token.encode()).hexdigest()) if token else None
    if not session or session.expires_at.replace(tzinfo=timezone.utc) <= datetime.now(timezone.utc):
        raise HTTPException(401, "Please sign in to continue")
    user = db.get(User, session.user_id)
    if not user:
        raise HTTPException(401, "Session is no longer valid")
    if user.demo and os.getenv("DEMO_ACCOUNTS_ENABLED", "false").lower() != "true":
        raise HTTPException(401, "Demo accounts are disabled in this environment")
    return user


def user_dict(user):
    return {"id": user.id, "name": user.name, "email": user.email, "role": user.role, "demo": user.demo}


def admin_user(user: User = Depends(current_user)):
    if user.role != "admin":
        raise HTTPException(403, "Administrator access required")
    return user


def login_session(db, user, response):
    db.query(AuthSession).filter(AuthSession.expires_at < datetime.now(timezone.utc)).delete()
    token = secrets.token_urlsafe(48)
    db.add(AuthSession(token_hash=hashlib.sha256(token.encode()).hexdigest(), user_id=user.id, expires_at=datetime.now(timezone.utc) + timedelta(days=7)))
    db.commit()
    response.set_cookie("portal_session", token, max_age=604800, httponly=True, secure=SECURE, samesite="lax", path="/api")


def rate_limit(request, action, limit=20):
    # The application is only exposed through nginx, which replaces X-Real-IP.
    ip = request.headers.get("x-real-ip") or (request.client.host if request.client else "unknown")
    key = f"rate:{action}:{hashlib.sha256(ip.encode()).hexdigest()}"
    try:
        with cache.pipeline() as pipe:
            pipe.incr(key)
            pipe.expire(key, 600, nx=True)
            count, _ = pipe.execute()
        if count > limit:
            raise HTTPException(429, "Too many requests. Please try again in a few minutes.")
    except RedisError:
        raise HTTPException(503, "Sign-in is temporarily unavailable. Please try again.")


class RegisterBody(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    role: Literal["user"] = "user"


class LoginBody(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


@app.get("/api/health")
def health(db: Session = Depends(database)):
    try:
        db.execute(text("SELECT 1"))
        cache.ping()
    except Exception:
        logger.exception("Readiness dependency failed")
        raise HTTPException(503, "A dependency is unavailable")
    return {"status": "ok", "database": "connected", "redis": "connected", "market": "India"}


@app.post("/api/auth/register", status_code=201)
def register(body: RegisterBody, request: Request, response: Response, db: Session = Depends(database)):
    rate_limit(request, "auth")
    user = User(name=body.name.strip(), email=str(body.email).lower(), password_hash=hash_password(body.password), role=body.role)
    if len(user.name) < 2:
        raise HTTPException(422, "Please enter your name")
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "An account with this email already exists")
    login_session(db, user, response)
    return user_dict(user)


@app.post("/api/auth/login")
def login(body: LoginBody, request: Request, response: Response, db: Session = Depends(database)):
    rate_limit(request, "auth")
    user = db.scalar(select(User).where(User.email == str(body.email).lower()))
    stored = user.password_hash if user else hash_password("dummy-password", "00000000000000000000000000000000")
    valid = verify_password(body.password, stored)
    if not user or not valid:
        raise HTTPException(401, "Email or password is incorrect")
    if user.demo and os.getenv("DEMO_ACCOUNTS_ENABLED", "false").lower() != "true":
        raise HTTPException(403, "Demo accounts are disabled in this environment")
    login_session(db, user, response)
    return user_dict(user)


@app.get("/api/auth/me")
def me(user: User = Depends(current_user)):
    return user_dict(user)


@app.post("/api/auth/logout", status_code=204)
def logout(request: Request, response: Response, db: Session = Depends(database)):
    token = request.cookies.get("portal_session", "")
    if token:
        session = db.get(AuthSession, hashlib.sha256(token.encode()).hexdigest())
        if session:
            db.delete(session)
            db.commit()
    response.delete_cookie("portal_session", path="/api", secure=SECURE, httponly=True, samesite="lax")


def property_dict(p):
    return {key: getattr(p, key) for key in ("id", "title", "address", "city", "state", "pincode", "price", "beds", "baths", "sqft", "kind", "purpose", "lat", "lng", "images", "amenities", "description", "badge", "agent", "demo", "owner_id", "active", "area_unit", "area_value", "plot_use", "plot_facing", "road_width_ft", "plot_approval", "deposit", "furnishing", "available_from")} | {"created_at": p.created_at.isoformat()}


@app.get("/api/cities")
def cities():
    return [{"name": city, **info} for city, info in CITIES.items()]


class SearchFilters(BaseModel):
    q: str = Field(default="", max_length=150)
    agent: str = Field(default="", max_length=120)
    purpose: Literal["sale", "rent"] = "sale"
    min_price: int = Field(default=0, ge=0, le=2_000_000_000)
    max_price: int | None = Field(default=None, ge=0, le=2_000_000_000)
    beds: int = Field(default=0, ge=0, le=20)
    baths: int = Field(default=0, ge=0, le=20)
    kind: Literal["", "Apartment", "Villa", "House", "Building", "Commercial Building", "Office", "Shop", "Open Plot"] = ""
    min_sqft: int = Field(default=0, ge=0, le=10_000_000)
    amenity: Literal["", "Parking", "Swimming pool", "Gym", "Garden", "Balcony", "Water supply", "Electricity", "Boundary wall", "Gated community"] = ""
    sort: Literal["recommended", "price_asc", "price_desc", "newest", "sqft"] = "recommended"


@app.get("/api/properties")
def properties(filters: SearchFilters = Depends(), page: int = Query(1, ge=1, le=10000), page_size: int = Query(24, ge=1, le=100), north: float | None = Query(None, ge=-90, le=90), south: float | None = Query(None, ge=-90, le=90), east: float | None = Query(None, ge=-180, le=180), west: float | None = Query(None, ge=-180, le=180), db: Session = Depends(database)):
    payload = filters.model_dump() | {"page": page, "page_size": page_size, "north": north, "south": south, "east": east, "west": west}
    key = None
    try:
        revision = cache.get("listings:revision") or "0"
        key = "search:" + revision + ":" + hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        found = cache.get(key)
        if found:
            return json.loads(found)
    except RedisError:
        pass
    query = select(Property).where(Property.active.is_(True), Property.purpose == filters.purpose)
    if filters.q:
        cleaned = filters.q.strip().replace("%", "\\%").replace("_", "\\_")
        if cleaned.lower() == "bangalore":
            cleaned = "Bengaluru"
        needle = f"%{cleaned}%"
        query = query.where(or_(*[getattr(Property, col).ilike(needle, escape="\\") for col in ("city", "address", "pincode", "title", "state")]))
    query = query.where(Property.price >= filters.min_price, Property.beds >= filters.beds, Property.baths >= filters.baths, Property.sqft >= filters.min_sqft)
    if filters.max_price is not None:
        query = query.where(Property.price <= filters.max_price)
    if filters.kind:
        query = query.where(Property.kind == filters.kind)
    if filters.agent:
        query = query.where(Property.agent == filters.agent)
    if filters.amenity:
        query = query.where(Property.amenities.cast(String).like(f'%"{filters.amenity}"%'))
    if None not in (north, south, east, west):
        query = query.where(Property.lat.between(south, north), Property.lng.between(west, east))
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    ordering = {"recommended": Property.id.asc(), "price_asc": Property.price.asc(), "price_desc": Property.price.desc(), "newest": Property.created_at.desc(), "sqft": Property.sqft.desc()}[filters.sort]
    records = db.scalars(query.order_by(ordering, Property.id).offset((page - 1) * page_size).limit(page_size)).all()
    result = {"items": [property_dict(p) for p in records], "total": total, "page": page, "page_size": page_size}
    if key:
        try:
            cache.setex(key, 60, json.dumps(result))
        except RedisError:
            pass
    return result


@app.get("/api/properties/{property_id}")
def property_detail(property_id: int, db: Session = Depends(database)):
    item = db.get(Property, property_id)
    if not item or not item.active:
        raise HTTPException(404, "This listing is no longer available")
    return property_dict(item)


@app.get("/api/favorites")
def favorites(user: User = Depends(current_user), db: Session = Depends(database)):
    items = db.scalars(select(Property).join(Favorite).where(Favorite.user_id == user.id, Property.active.is_(True)).order_by(Property.id)).all()
    return [property_dict(p) for p in items]


@app.put("/api/favorites/{property_id}", status_code=204)
def add_favorite(property_id: int, user: User = Depends(current_user), db: Session = Depends(database)):
    item = db.get(Property, property_id)
    if not item or not item.active:
        raise HTTPException(404, "Listing not found")
    if not db.get(Favorite, (user.id, property_id)):
        db.add(Favorite(user_id=user.id, property_id=property_id))
        try:
            db.commit()
        except IntegrityError:
            db.rollback()


@app.delete("/api/favorites/{property_id}", status_code=204)
def delete_favorite(property_id: int, user: User = Depends(current_user), db: Session = Depends(database)):
    favorite = db.get(Favorite, (user.id, property_id))
    if favorite:
        db.delete(favorite)
        db.commit()


class SavedSearchBody(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    filters: SearchFilters


@app.get("/api/saved-searches")
def saved_searches(user: User = Depends(current_user), db: Session = Depends(database)):
    items = db.scalars(select(SavedSearch).where(SavedSearch.user_id == user.id).order_by(SavedSearch.id.desc())).all()
    return [{"id": s.id, "name": s.name, "filters": s.filters, "created_at": s.created_at.isoformat()} for s in items]


@app.post("/api/saved-searches", status_code=201)
def save_search(body: SavedSearchBody, user: User = Depends(current_user), db: Session = Depends(database)):
    count = db.scalar(select(func.count()).select_from(SavedSearch).where(SavedSearch.user_id == user.id))
    if count >= 50:
        raise HTTPException(422, "You can save up to 50 searches. Remove an older search first.")
    item = SavedSearch(user_id=user.id, name=body.name, filters=body.filters.model_dump())
    db.add(item)
    db.commit()
    return {"id": item.id, "name": item.name, "filters": item.filters}


@app.delete("/api/saved-searches/{search_id}", status_code=204)
def remove_search(search_id: int, user: User = Depends(current_user), db: Session = Depends(database)):
    item = db.get(SavedSearch, search_id)
    if not item or item.user_id != user.id:
        raise HTTPException(404, "Saved search not found")
    db.delete(item)
    db.commit()


class InquiryBody(BaseModel):
    property_id: int
    message: str = Field(min_length=10, max_length=2000)
    phone: str = Field(pattern=r"^(\+91[ -]?)?[6-9]\d{9}$")
    visit_date: date | None = None


@app.post("/api/inquiries", status_code=201)
def create_inquiry(body: InquiryBody, request: Request, user: User = Depends(current_user), db: Session = Depends(database)):
    rate_limit(request, "inquiry", 30)
    item = db.get(Property, body.property_id)
    if not item or not item.active:
        raise HTTPException(404, "Listing not found")
    if body.visit_date and body.visit_date < date.today():
        raise HTTPException(422, "Choose a future visit date")
    inquiry = Inquiry(user_id=user.id, property_id=body.property_id, message=body.message, phone=body.phone, visit_date=body.visit_date.isoformat() if body.visit_date else None)
    db.add(inquiry)
    db.commit()
    return {"id": inquiry.id, "demo": item.demo, "status": "recorded"}


@app.get("/api/inquiries")
def inquiries(user: User = Depends(current_user), db: Session = Depends(database)):
    rows = db.execute(select(Inquiry, Property, User).join(Property, Property.id == Inquiry.property_id).join(User, User.id == Inquiry.user_id).where(or_(Inquiry.user_id == user.id, Property.owner_id == user.id)).order_by(Inquiry.created_at.desc())).all()
    return [{"id": i.id, "message": i.message, "phone": i.phone, "visit_date": i.visit_date, "created_at": i.created_at.isoformat(), "property": property_dict(p), "sender_name": sender.name, "direction": "received" if p.owner_id == user.id and i.user_id != user.id else "sent"} for i, p, sender in rows]


class PropertyBody(BaseModel):
    title: str = Field(min_length=5, max_length=160)
    address: str = Field(min_length=5, max_length=250)
    city: str = Field(min_length=2, max_length=100)
    state: str = Field(min_length=2, max_length=100)
    pincode: str = Field(pattern=r"^[1-9]\d{5}$")
    price: int = Field(gt=0, le=2_000_000_000)
    beds: int = Field(default=0, ge=0, le=20)
    baths: int = Field(default=0, ge=0, le=20)
    sqft: int = Field(gt=0, le=10_000_000)
    kind: Literal["Apartment", "Villa", "House", "Building", "Commercial Building", "Office", "Shop", "Open Plot"]
    purpose: Literal["sale", "rent"]
    lat: float = Field(ge=6, le=38)
    lng: float = Field(ge=68, le=98)
    images: list[str] = Field(min_length=1, max_length=10)
    amenities: list[Literal["Parking", "Security", "Power backup", "Balcony", "Swimming pool", "Gym", "Garden", "Water supply", "Electricity", "Boundary wall", "Gated community"]] = Field(default_factory=list, max_length=11)
    description: str = Field(min_length=30, max_length=5000)
    area_unit: Literal["sqft", "sqyd", "acre"] = "sqft"
    area_value: float | None = Field(default=None, gt=0, le=10_000_000, allow_inf_nan=False)
    plot_use: Literal["", "Residential", "Commercial", "Agricultural"] = ""
    plot_facing: Literal["", "North", "South", "East", "West", "North-East", "North-West", "South-East", "South-West"] = ""
    road_width_ft: int | None = Field(default=None, ge=1, le=300)
    plot_approval: str = Field(default="", max_length=100)
    deposit: int = Field(default=0, ge=0, le=2_000_000_000)
    furnishing: Literal["Unfurnished", "Semi-furnished", "Furnished"] = "Unfurnished"
    available_from: str | None = None

    @field_validator("available_from")
    @classmethod
    def valid_available_date(cls, value):
        if value is not None:
            if date.fromisoformat(value).isoformat() != value:
                raise ValueError("Use a valid availability date in YYYY-MM-DD format")
        return value

    @model_validator(mode="after")
    def valid_listing_type(self):
        if self.kind == "Open Plot":
            if self.purpose != "sale":
                raise ValueError("Open plots are supported for sale")
            if self.beds or self.baths:
                raise ValueError("Open plots do not have bedrooms or bathrooms")
            self.area_value = self.area_value if self.area_value is not None else self.sqft
            converted = round(self.area_value * {"sqft": 1, "sqyd": 9, "acre": 43560}[self.area_unit])
            if not 1 <= converted <= 10_000_000:
                raise ValueError("Plot area must be between 1 and 10,000,000 sqft")
            self.sqft = converted
            if self.deposit or self.available_from:
                raise ValueError("Rental details do not apply to plots")
        else:
            commercial = self.kind in {"Commercial Building", "Office", "Shop"}
            if commercial and self.beds:
                raise ValueError("Commercial properties do not use bedroom counts")
            if (not commercial and self.baths < 1) or self.area_unit != "sqft":
                raise ValueError("Residential properties need at least one bathroom; use square feet for built-up area")
            if self.plot_use or self.plot_facing or self.road_width_ft or self.plot_approval:
                raise ValueError("Plot details apply only to open plots")
            self.area_value = None
        if self.purpose != "rent" and (self.deposit or self.available_from):
            raise ValueError("Deposit and availability apply only to rental listings")
        return self

    @field_validator("images")
    @classmethod
    def valid_images(cls, images):
        for image in images:
            if len(image) > 2000:
                raise ValueError("Image URL is too long")
            import re
            if re.fullmatch(r"/api/uploads/[0-9a-f]{32}\.jpg", image):
                continue
            if image.startswith("/images/") and ".." not in image:
                continue
            parts = urlsplit(image)
            if parts.scheme != "https" or not parts.hostname or parts.username or parts.password:
                raise ValueError("Use uploaded photos, HTTPS image URLs or local /images/ paths")
        return images


def invalidate():
    try:
        cache.incr("listings:revision")
    except RedisError:
        pass  # Cached results expire within 60 seconds if Redis was unavailable.


@app.get("/api/me/listings")
def my_listings(user: User = Depends(current_user), db: Session = Depends(database)):
    return [property_dict(p) for p in db.scalars(select(Property).where(Property.owner_id == user.id).order_by(Property.id.desc())).all()]


@app.post("/api/properties", status_code=201)
def create_property(body: PropertyBody, request: Request, user: User = Depends(current_user), db: Session = Depends(database)):
    rate_limit(request, "publish", 30)
    validate_uploaded_images(db, user, body.images)
    item = Property(**body.model_dump(), owner_id=user.id, agent=user.name, badge="New listing", demo=False)
    db.add(item)
    db.commit()
    invalidate()
    return property_dict(item)


@app.put("/api/properties/{property_id}")
def update_property(property_id: int, body: PropertyBody, user: User = Depends(current_user), db: Session = Depends(database)):
    item = db.get(Property, property_id)
    if not item or item.owner_id != user.id:
        raise HTTPException(404, "Your listing was not found")
    validate_uploaded_images(db, user, body.images)
    for key, value in body.model_dump().items():
        setattr(item, key, value)
    db.commit()
    invalidate()
    return property_dict(item)


@app.delete("/api/properties/{property_id}", status_code=204)
def archive_property(property_id: int, user: User = Depends(current_user), db: Session = Depends(database)):
    item = db.get(Property, property_id)
    if not item or item.owner_id != user.id:
        raise HTTPException(404, "Your listing was not found")
    item.active = False
    db.commit()
    invalidate()


@app.get("/api/admin/summary")
def admin_summary(user: User = Depends(admin_user), db: Session = Depends(database)):
    count = lambda model, *conditions: db.scalar(select(func.count()).select_from(model).where(*conditions))
    city_rows = db.execute(select(Property.city, func.count()).where(Property.active.is_(True)).group_by(Property.city).order_by(Property.city)).all()
    return {"active_properties": count(Property, Property.active.is_(True)), "archived_properties": count(Property, Property.active.is_(False)), "synthetic_properties": count(Property, Property.active.is_(True), Property.seed_key.like("india-demo-v2:%")), "sale": count(Property, Property.active.is_(True), Property.purpose == "sale"), "rent": count(Property, Property.active.is_(True), Property.purpose == "rent"), "users": count(User), "inquiries": count(Inquiry), "cities": [{"city": city, "properties": total} for city, total in city_rows]}


@app.get("/api/admin/properties")
def admin_properties(q: str = Query("", max_length=150), city: str = Query("", max_length=100), status: Literal["all", "active", "archived"] = "active", page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), user: User = Depends(admin_user), db: Session = Depends(database)):
    statement = select(Property)
    if q:
        statement = statement.where(or_(Property.title.ilike(f"%{q}%"), Property.address.ilike(f"%{q}%")))
    if city:
        statement = statement.where(Property.city == city)
    if status != "all":
        statement = statement.where(Property.active.is_(status == "active"))
    total = db.scalar(select(func.count()).select_from(statement.subquery()))
    rows = db.scalars(statement.order_by(Property.id).offset((page - 1) * page_size).limit(page_size)).all()
    return {"items": [property_dict(p) for p in rows], "total": total, "page": page, "page_size": page_size}


class ModerationBody(BaseModel):
    active: bool


@app.patch("/api/admin/properties/{property_id}")
def moderate_property(property_id: int, body: ModerationBody, user: User = Depends(admin_user), db: Session = Depends(database)):
    item = db.get(Property, property_id)
    if item is None:
        raise HTTPException(404, "Listing not found")
    item.active = body.active
    db.commit()
    invalidate()
    return property_dict(item)


@app.get("/api/admin/users")
def admin_users(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), user: User = Depends(admin_user), db: Session = Depends(database)):
    rows = db.scalars(select(User).order_by(User.id).offset((page - 1) * page_size).limit(page_size)).all()
    return {"items": [user_dict(u) | {"created_at": u.created_at.isoformat()} for u in rows], "total": db.scalar(select(func.count()).select_from(User))}


@app.get("/api/admin/inquiries")
def admin_inquiries(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), user: User = Depends(admin_user), db: Session = Depends(database)):
    rows = db.execute(select(Inquiry, Property, User).join(Property, Property.id == Inquiry.property_id).join(User, User.id == Inquiry.user_id).order_by(Inquiry.id.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return {"items": [{"id": i.id, "message": i.message, "phone": i.phone, "visit_date": i.visit_date, "created_at": i.created_at.isoformat(), "property": property_dict(p), "sender_name": sender.name} for i, p, sender in rows], "total": db.scalar(select(func.count()).select_from(Inquiry))}

# Photo storage is kept in a persistent Docker volume and shares session rules.
from .uploads import create_upload_router, validate_uploaded_images
app.include_router(create_upload_router(current_user, database, rate_limit))
