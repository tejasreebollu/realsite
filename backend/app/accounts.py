"""Self-service profiles, reviewed agent profiles and audited account administration."""
import hashlib
import hmac
import os
import re
import secrets
import smtplib
import ssl
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from sqlalchemy import String, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .models import AccountAudit, AgentProfile, AuthSession, EmailChange, Property, User
from .passwords import hash_password, verify_password
from .uploads import validate_uploaded_images


def now():
    return datetime.now(timezone.utc)


class StrictBody(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ProfileBody(StrictBody):
    name: str = Field(min_length=2, max_length=100)
    phone: str = Field(default="", max_length=20)
    city: str = Field(default="", max_length=100)
    bio: str = Field(default="", max_length=1000)
    avatar_url: str = Field(default="", max_length=250)

    @field_validator("phone")
    @classmethod
    def phone_format(cls, value):
        if value and not re.fullmatch(r"(?:\+91[ -]?)?[6-9]\d{9}", value):
            raise ValueError("Enter a 10-digit Indian mobile number, optionally with +91")
        return value


class PasswordBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=10, max_length=128)


class EmailBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr
    current_password: str = Field(min_length=1, max_length=128)


class VerifyEmailBody(StrictBody):
    token: str = Field(min_length=20, max_length=100)


class AgentBody(StrictBody):
    agency: str = Field(min_length=2, max_length=120)
    bio: str = Field(min_length=20, max_length=2000)
    service_areas: list[str] = Field(min_length=1, max_length=10)
    experience_years: int = Field(ge=0, le=60)
    registration_number: str = Field(default="", max_length=100)
    publish_phone: bool = False

    @field_validator("service_areas")
    @classmethod
    def areas(cls, values):
        values = list(dict.fromkeys(v.strip() for v in values))
        if any(len(v) < 2 or len(v) > 100 for v in values):
            raise ValueError("Each service area must contain 2 to 100 characters")
        return values


class AdminAccountBody(ProfileBody):
    active: bool
    reason: str = Field(min_length=5, max_length=1000)


class ReviewBody(StrictBody):
    status: str
    reason: str = Field(min_length=5, max_length=1000)

    @field_validator("status")
    @classmethod
    def decision(cls, value):
        if value not in {"approved", "rejected"}:
            raise ValueError("Choose approved or rejected")
        return value


def agent_dict(agent):
    if not agent:
        return None
    return {key: getattr(agent, key) for key in ("user_id", "agency", "bio", "service_areas", "experience_years", "registration_number", "publish_phone", "status", "review_note")} | {"updated_at": agent.updated_at.isoformat()}


def audit(db, actor, target, action, changes, reason=""):
    db.add(AccountAudit(actor_id=actor.id, target_id=target.id, action=action, reason=reason, changes=changes))


def lock_user(db, user_id):
    user = db.scalar(select(User).where(User.id == user_id).with_for_update().execution_options(populate_existing=True))
    if not user:
        raise HTTPException(404, "Account not found")
    return user


def revoke_other_sessions(db, user, request, all_sessions=False):
    current_hash = hashlib.sha256(request.cookies.get("portal_session", "").encode()).hexdigest()
    query = db.query(AuthSession).filter(AuthSession.user_id == user.id)
    if not all_sessions:
        query = query.filter(AuthSession.token_hash != current_hash)
    query.delete(synchronize_session=False)


def require_password(user, password):
    if not verify_password(password, user.password_hash):
        raise HTTPException(400, "Current password is incorrect")


def deliver_verification(email, token):
    mode = os.getenv("ACCOUNT_EMAIL_MODE", "smtp")
    if mode == "demo":
        if os.getenv("COOKIE_SECURE", "false").lower() == "true" or os.getenv("DEMO_ACCOUNTS_ENABLED", "false").lower() != "true":
            raise HTTPException(503, "Local email demo mode is unavailable in this environment")
        return {"delivery": "demo", "demo_token": token, "message": "Local demo only: no email was sent. Use the displayed verification code."}
    if mode != "smtp" or not os.getenv("SMTP_HOST") or not os.getenv("SMTP_FROM"):
        raise HTTPException(503, "Email delivery is not configured. Contact portal support.")
    message = EmailMessage()
    message["Subject"] = "Verify your RealSite email change"
    message["From"] = os.environ["SMTP_FROM"]
    message["To"] = email
    message.set_content(f"Enter this code in RealSite Account Settings to verify your new email:\n\n{token}\n\nIt expires in 30 minutes and can be used only once. If you did not request this, ignore this message.")
    try:
        port = int(os.getenv("SMTP_PORT", "587"))
        factory = smtplib.SMTP_SSL if port == 465 else smtplib.SMTP
        options = {"timeout": 15}
        if port == 465:
            options["context"] = ssl.create_default_context()
        with factory(os.environ["SMTP_HOST"], port, **options) as smtp:
            if port != 465:
                smtp.starttls(context=ssl.create_default_context())
            if os.getenv("SMTP_USER"):
                smtp.login(os.environ["SMTP_USER"], os.environ.get("SMTP_PASSWORD", ""))
            smtp.send_message(message)
    except (OSError, smtplib.SMTPException, ValueError):
        raise HTTPException(503, "Verification email could not be sent. Please try again later.")
    return {"delivery": "smtp", "message": "A verification code was sent to your new email address."}


def create_account_router(current_user, admin_user, database, rate_limit, user_dict, invalidate):
    router = APIRouter()

    def profile_dict(db, user):
        pending = db.get(EmailChange, user.id)
        pending_email = pending.email if pending and pending.expires_at.replace(tzinfo=timezone.utc) > now() else None
        return user_dict(user) | {"agent_profile": agent_dict(db.get(AgentProfile, user.id)), "pending_email": pending_email}

    @router.get("/api/me/profile")
    def profile(user: User = Depends(current_user), db: Session = Depends(database)):
        return profile_dict(db, user)

    @router.patch("/api/me/profile")
    def update_profile(body: ProfileBody, user: User = Depends(current_user), db: Session = Depends(database)):
        user = lock_user(db, user.id)
        if body.avatar_url:
            if not re.fullmatch(r"/api/uploads/[0-9a-f]{32}\.jpg", body.avatar_url):
                raise HTTPException(422, "Upload your profile photo using this account")
            validate_uploaded_images(db, user, [body.avatar_url])
        changes = {key: {"before": getattr(user, key), "after": value} for key, value in body.model_dump().items() if getattr(user, key) != value}
        for key, value in body.model_dump().items():
            setattr(user, key, value)
        if changes:
            audit(db, user, user, "profile_updated", changes)
        db.commit()
        return profile_dict(db, user)

    @router.post("/api/me/password", status_code=204)
    def change_password(body: PasswordBody, request: Request, user: User = Depends(current_user), db: Session = Depends(database)):
        rate_limit(request, f"account-security:{user.id}", 10)
        user = lock_user(db, user.id)
        if user.demo:
            raise HTTPException(422, "Demo login credentials are fixed. Use a registered account for this setting.")
        require_password(user, body.current_password)
        if body.new_password == body.current_password:
            raise HTTPException(422, "Choose a different new password")
        user.password_hash = hash_password(body.new_password)
        pending = db.get(EmailChange, user.id)
        if pending:
            db.delete(pending)
        revoke_other_sessions(db, user, request)
        audit(db, user, user, "password_changed", {"other_sessions_revoked": True})
        db.commit()

    @router.post("/api/me/email-change")
    def request_email(body: EmailBody, request: Request, user: User = Depends(current_user), db: Session = Depends(database)):
        rate_limit(request, f"account-security:{user.id}", 10)
        user = lock_user(db, user.id)
        if user.demo:
            raise HTTPException(422, "Demo login credentials are fixed. Use a registered account for this setting.")
        require_password(user, body.current_password)
        email = str(body.email).lower()
        if email == user.email:
            raise HTTPException(422, "Enter a different email address")
        if db.scalar(select(User.id).where(User.email == email)):
            raise HTTPException(409, "This email is already in use")
        token = secrets.token_urlsafe(24)
        delivery = deliver_verification(email, token)
        pending = db.get(EmailChange, user.id)
        if not pending:
            pending = EmailChange(user_id=user.id)
            db.add(pending)
        pending.email = email
        pending.token_hash = hashlib.sha256(token.encode()).hexdigest()
        pending.expires_at = now() + timedelta(minutes=30)
        audit(db, user, user, "email_change_requested", {"new_email": email})
        db.commit()
        return delivery | {"pending_email": email}

    @router.post("/api/me/email-change/verify")
    def verify_email(body: VerifyEmailBody, request: Request, user: User = Depends(current_user), db: Session = Depends(database)):
        rate_limit(request, f"account-security:{user.id}", 10)
        user = lock_user(db, user.id)
        pending = db.get(EmailChange, user.id)
        if not pending or pending.expires_at.replace(tzinfo=timezone.utc) <= now() or not hmac.compare_digest(pending.token_hash, hashlib.sha256(body.token.encode()).hexdigest()):
            raise HTTPException(400, "Verification code is invalid or expired")
        old_email = user.email
        user.email = pending.email
        db.delete(pending)
        revoke_other_sessions(db, user, request)
        audit(db, user, user, "email_changed", {"email": {"before": old_email, "after": user.email}})
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(409, "This email is now in use. Request verification for another address.")
        return profile_dict(db, user)

    @router.delete("/api/me/email-change", status_code=204)
    def cancel_email(user: User = Depends(current_user), db: Session = Depends(database)):
        user = lock_user(db, user.id)
        pending = db.get(EmailChange, user.id)
        if pending:
            db.delete(pending)
            audit(db, user, user, "email_change_cancelled", {})
            db.commit()

    @router.put("/api/me/agent-profile")
    def apply_agent(body: AgentBody, user: User = Depends(current_user), db: Session = Depends(database)):
        user = lock_user(db, user.id)
        if body.publish_phone and not user.phone:
            raise HTTPException(422, "Save your mobile number in My Profile before publishing it")
        agent = db.get(AgentProfile, user.id)
        if not agent:
            agent = AgentProfile(user_id=user.id)
            db.add(agent)
        for key, value in body.model_dump().items():
            setattr(agent, key, value)
        agent.status = "pending"
        agent.review_note = ""
        agent.reviewed_by = None
        agent.updated_at = now()
        if user.role == "agent":
            user.role = "user"
        audit(db, user, user, "agent_application_submitted", {"status": "pending"})
        db.commit()
        return profile_dict(db, user)

    @router.get("/api/agents")
    def agents(city: str = Query("", max_length=100), page: int = Query(1, ge=1), page_size: int = Query(12, ge=1, le=50), db: Session = Depends(database)):
        query = select(AgentProfile, User).join(User, User.id == AgentProfile.user_id).where(AgentProfile.status == "approved", User.active.is_(True))
        if city:
            term = city.strip().casefold()
            # Service areas are bounded lists; exact city membership avoids substring matches.
            query = query.where(func.lower(AgentProfile.service_areas.cast(String)).contains(term, autoescape=True))
        rows = db.execute(query.order_by(User.name, User.id)).all()
        if city:
            rows = [(a,u) for a,u in rows if city.strip().casefold() in {area.casefold() for area in a.service_areas}]
        total = len(rows)
        items = []
        for agent, account in rows[(page-1)*page_size:page*page_size]:
            items.append({"id": account.id, "name": account.name, "avatar_url": account.avatar_url, "agency": agent.agency, "bio": agent.bio, "service_areas": agent.service_areas, "experience_years": agent.experience_years, "registration_number": agent.registration_number, "phone": account.phone if agent.publish_phone else "", "listing_count": db.scalar(select(func.count()).select_from(Property).where(Property.owner_id == account.id, Property.active.is_(True)))})
        return {"items": items, "total": total, "page": page, "page_size": page_size}

    @router.get("/api/admin/users")
    def admin_accounts(q: str = Query("", max_length=150), role: str = Query("", pattern="^(|user|agent|admin)$"), status: str = Query("all", pattern="^(all|active|suspended)$"), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), user: User = Depends(admin_user), db: Session = Depends(database)):
        query = select(User)
        if q.strip():
            query = query.where(or_(User.name.ilike(f"%{q.strip()}%"), User.email.ilike(f"%{q.strip()}%")))
        if role:
            query = query.where(User.role == role)
        if status != "all":
            query = query.where(User.active.is_(status == "active"))
        total = db.scalar(select(func.count()).select_from(query.subquery()))
        rows = db.scalars(query.order_by(User.id).offset((page-1)*page_size).limit(page_size)).all()
        return {"items": [profile_dict(db, u) | {"created_at": u.created_at.isoformat()} for u in rows], "total": total}

    @router.patch("/api/admin/users/{user_id}")
    def admin_update(user_id: int, body: AdminAccountBody, request: Request, actor: User = Depends(admin_user), db: Session = Depends(database)):
        # Lock administrator rows first so concurrent suspension cannot remove every administrator.
        admins = db.scalars(select(User).where(User.role == "admin", User.active.is_(True)).order_by(User.id).with_for_update()).all()
        target = lock_user(db, user_id)
        if not body.active and target.id == actor.id:
            raise HTTPException(422, "You cannot suspend your own account")
        if not body.active and target.role == "admin" and target.active and len(admins) <= 1:
            raise HTTPException(422, "At least one active administrator must remain")
        if body.avatar_url != target.avatar_url:
            raise HTTPException(422, "Profile photos can only be changed by their account owner")
        changes = {key: {"before": getattr(target, key), "after": value} for key, value in body.model_dump(exclude={"reason"}).items() if getattr(target, key) != value}
        for key, value in body.model_dump(exclude={"reason"}).items():
            setattr(target, key, value)
        if not target.active:
            revoke_other_sessions(db, target, request, all_sessions=True)
            pending = db.get(EmailChange, target.id)
            if pending:
                db.delete(pending)
        audit(db, actor, target, "admin_account_updated", changes, body.reason)
        db.commit()
        return profile_dict(db, target)

    @router.get("/api/admin/agents")
    def applications(status: str = Query("pending", pattern="^(all|pending|approved|rejected)$"), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), user: User = Depends(admin_user), db: Session = Depends(database)):
        query = select(AgentProfile, User).join(User, User.id == AgentProfile.user_id)
        if status != "all":
            query = query.where(AgentProfile.status == status)
        total = db.scalar(select(func.count()).select_from(query.subquery()))
        rows = db.execute(query.order_by(AgentProfile.updated_at.desc()).offset((page-1)*page_size).limit(page_size)).all()
        return {"items": [agent_dict(a) | {"account": user_dict(u)} for a,u in rows], "total": total}

    @router.patch("/api/admin/agents/{user_id}")
    def review(user_id: int, body: ReviewBody, actor: User = Depends(admin_user), db: Session = Depends(database)):
        target = lock_user(db, user_id)
        if target.id == actor.id:
            raise HTTPException(422, "Another administrator must review your application")
        agent = db.get(AgentProfile, user_id)
        if not agent:
            raise HTTPException(404, "Agent application not found")
        if not target.active and body.status == "approved":
            raise HTTPException(422, "Reactivate the account before approving its agent profile")
        previous = agent.status
        agent.status, agent.review_note, agent.reviewed_by, agent.updated_at = body.status, body.reason, actor.id, now()
        if target.role != "admin":
            target.role = "agent" if body.status == "approved" else "user"
        audit(db, actor, target, "agent_reviewed", {"status": {"before": previous, "after": agent.status}}, body.reason)
        db.commit()
        return agent_dict(agent)

    @router.get("/api/admin/account-audit")
    def audit_log(user_id: int | None = Query(None, ge=1), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), user: User = Depends(admin_user), db: Session = Depends(database)):
        query = select(AccountAudit)
        if user_id:
            query = query.where(AccountAudit.target_id == user_id)
        total = db.scalar(select(func.count()).select_from(query.subquery()))
        rows = db.scalars(query.order_by(AccountAudit.id.desc()).offset((page-1)*page_size).limit(page_size)).all()
        return {"items": [{"id": a.id, "actor_id": a.actor_id, "target_id": a.target_id, "action": a.action, "reason": a.reason, "changes": a.changes, "created_at": a.created_at.isoformat()} for a in rows], "total": total}

    return router
