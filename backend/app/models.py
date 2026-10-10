import os
from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


def now():
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


engine = create_engine(os.environ.get("DATABASE_URL", "postgresql+psycopg://portal:portal@db/portal"), pool_pre_ping=True)
SessionLocal = sessionmaker(engine, expire_on_commit=False)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(256))
    role: Mapped[str] = mapped_column(String(20), default="user", server_default="user")
    active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    phone: Mapped[str] = mapped_column(String(20), default="", server_default="")
    city: Mapped[str] = mapped_column(String(100), default="", server_default="")
    bio: Mapped[str] = mapped_column(Text, default="", server_default="")
    avatar_url: Mapped[str] = mapped_column(String(250), default="", server_default="")
    demo: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class AuthSession(Base):
    __tablename__ = "auth_sessions"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Property(Base):
    __tablename__ = "properties"
    id: Mapped[int] = mapped_column(primary_key=True)
    seed_key: Mapped[str | None] = mapped_column(String(120), unique=True, nullable=True)
    title: Mapped[str] = mapped_column(String(160))
    address: Mapped[str] = mapped_column(String(250))
    city: Mapped[str] = mapped_column(String(100), index=True)
    state: Mapped[str] = mapped_column(String(100))
    pincode: Mapped[str] = mapped_column(String(6))
    price: Mapped[int] = mapped_column(Integer, index=True)
    beds: Mapped[int] = mapped_column(Integer)
    baths: Mapped[int] = mapped_column(Integer)
    sqft: Mapped[int] = mapped_column(Integer)
    kind: Mapped[str] = mapped_column(String(30))
    purpose: Mapped[str] = mapped_column(String(10), index=True)
    lat: Mapped[float] = mapped_column(Float)
    lng: Mapped[float] = mapped_column(Float)
    images: Mapped[list] = mapped_column(JSON)
    amenities: Mapped[list] = mapped_column(JSON)
    description: Mapped[str] = mapped_column(Text)
    features: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    previous_price: Mapped[int | None] = mapped_column(Integer, nullable=True)
    badge: Mapped[str] = mapped_column(String(80), default="New listing")
    agent: Mapped[str] = mapped_column(String(120))
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    demo: Mapped[bool] = mapped_column(Boolean, default=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    area_unit: Mapped[str] = mapped_column(String(10), default="sqft", server_default="sqft")
    area_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    plot_use: Mapped[str] = mapped_column(String(20), default="", server_default="")
    plot_facing: Mapped[str] = mapped_column(String(20), default="", server_default="")
    road_width_ft: Mapped[int | None] = mapped_column(Integer, nullable=True)
    plot_approval: Mapped[str] = mapped_column(String(100), default="", server_default="")
    deposit: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    furnishing: Mapped[str] = mapped_column(String(20), default="Unfurnished", server_default="Unfurnished")
    available_from: Mapped[str | None] = mapped_column(String(10), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class UploadedImage(Base):
    __tablename__ = "uploaded_images"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    width: Mapped[int] = mapped_column(Integer)
    height: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Favorite(Base):
    __tablename__ = "favorites"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id", ondelete="CASCADE"), primary_key=True)


class SavedSearch(Base):
    __tablename__ = "saved_searches"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    filters: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Inquiry(Base):
    __tablename__ = "inquiries"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"))
    message: Mapped[str] = mapped_column(Text)
    phone: Mapped[str] = mapped_column(String(20))
    visit_date: Mapped[str | None] = mapped_column(String(30), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class AgentProfile(Base):
    __tablename__ = "agent_profiles"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    agency: Mapped[str] = mapped_column(String(120))
    bio: Mapped[str] = mapped_column(Text)
    service_areas: Mapped[list] = mapped_column(JSON)
    experience_years: Mapped[int] = mapped_column(Integer)
    registration_number: Mapped[str] = mapped_column(String(100), default="")
    publish_phone: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    review_note: Mapped[str] = mapped_column(String(1000), default="")
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class EmailChange(Base):
    __tablename__ = "email_changes"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    email: Mapped[str] = mapped_column(String(254))
    token_hash: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class AccountAudit(Base):
    __tablename__ = "account_audit"
    id: Mapped[int] = mapped_column(primary_key=True)
    actor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    target_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    action: Mapped[str] = mapped_column(String(60))
    reason: Mapped[str] = mapped_column(String(1000), default="")
    changes: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
