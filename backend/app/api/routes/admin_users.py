"""
Super-admin user management: create/list users, reset a user's password,
delete a user, reset a user's published-portfolio subdomain.
"""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.core.config import settings
from app.core.security import hash_value, hmac_lookup_hash
from app.db.session import get_db
from app.models.models import (
    AiAssistantConfig,
    OnboardingStatusEnum,
    PublishedPortfolio,
    PublishedPortfolioStatusEnum,
    RoleEnum,
    Subscription,
    User,
    UserProfile,
)
from app.schemas.schemas import (
    AdminPasswordResetIn,
    UserAdminCreateIn,
    UserAdminDetailOut,
    UserAdminOut,
    UserAiAssistantUpdateIn,
)
from app.services import site_generator
from app.services.otp_service import OtpError, normalize_mobile_number
from app.services.user_admin_service import delete_user_cascade

router = APIRouter(
    prefix="/api/admin/users",
    tags=["admin-users"],
    dependencies=[Depends(require_role(RoleEnum.super_admin))],
)


def _to_admin_out(user: User) -> UserAdminOut:
    return UserAdminOut(
        id=user.id,
        full_name=user.full_name,
        mobile_number=user.mobile_number_encrypted,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
    )


def _to_detail_out(user: User, db: Session) -> UserAdminDetailOut:
    profile = user.profile
    published = db.query(PublishedPortfolio).filter_by(user_id=user.id).first()
    subscription = db.query(Subscription).filter_by(user_id=user.id).first()
    ai_assistant_enabled = bool(subscription and subscription.ai_assistant_enabled)
    config = db.query(AiAssistantConfig).filter_by(user_id=user.id).first()
    published_url = None
    if published and published.status == PublishedPortfolioStatusEnum.published and published.slug:
        published_url = settings.build_public_url(f"{published.slug}.{settings.BASE_DOMAIN}")

    return UserAdminDetailOut(
        id=user.id,
        full_name=user.full_name,
        mobile_number=user.mobile_number_encrypted,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        display_name=profile.display_name if profile else None,
        email=profile.email if profile else None,
        city=profile.city if profile else None,
        country=profile.country if profile else None,
        profile_image=profile.profile_image if profile else None,
        slug=published.slug if published else None,
        publish_status=published.status.value if published else None,
        published_at=published.published_at if published else None,
        published_url=published_url,
        ai_assistant_enabled=ai_assistant_enabled,
        ai_assistant_config_enabled=config.enabled if config else False,
    )


@router.post("", response_model=UserAdminOut, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserAdminCreateIn, db: Session = Depends(get_db)):
    full_name = payload.full_name.strip()
    if not full_name:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Enter a full name.")
    if len(payload.password) < 8:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Password must be at least 8 characters long.")

    try:
        normalized = normalize_mobile_number(payload.mobile_number)
    except OtpError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    mobile_hash = hmac_lookup_hash(normalized)
    if db.query(User).filter_by(mobile_number_hash=mobile_hash).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "This mobile number is already registered.")

    user = User(
        mobile_number_encrypted=normalized,
        mobile_number_hash=mobile_hash,
        full_name=full_name,
        password_hash=hash_value(payload.password),
        role=payload.role,
        is_active=payload.is_active,
    )
    db.add(user)
    db.flush()

    db.add(
        UserProfile(
            user_id=user.id,
            display_name=full_name,
            onboarding_status=OnboardingStatusEnum.resume_pending,
        )
    )
    db.add(
        Subscription(
            user_id=user.id,
            trial_ends_at=datetime.now(timezone.utc) + timedelta(days=30),
        )
    )

    db.commit()
    db.refresh(user)
    return _to_admin_out(user)


@router.get("", response_model=list[UserAdminOut])
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.created_at.desc()).all()
    return [_to_admin_out(u) for u in users]


@router.get("/{user_id}", response_model=UserAdminDetailOut)
def get_user_detail(user_id: str, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
    return _to_detail_out(user, db)


@router.put("/{user_id}/password", status_code=status.HTTP_204_NO_CONTENT)
def reset_password(user_id: str, payload: AdminPasswordResetIn, db: Session = Depends(get_db)):
    if len(payload.new_password) < 8:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Password must be at least 8 characters long.")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
    user.password_hash = hash_value(payload.new_password)
    db.commit()


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user_id == current_user.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You cannot delete your own account.")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
    try:
        delete_user_cascade(db, user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Could not delete user")


@router.put("/{user_id}/publish/slug-reset", status_code=status.HTTP_204_NO_CONTENT)
def reset_published_slug(user_id: str, db: Session = Depends(get_db)):
    """Clears a user's locked subdomain so they can choose a new one, e.g. for a support request."""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
    row = db.query(PublishedPortfolio).filter_by(user_id=user_id).first()
    if not row:
        return
    if row.status == PublishedPortfolioStatusEnum.published and row.slug:
        site_generator.unpublish_site(row.slug)
    row.slug = None
    row.status = PublishedPortfolioStatusEnum.draft
    row.published_at = None
    db.commit()


@router.put("/{user_id}/ai-assistant", response_model=UserAdminDetailOut)
def update_ai_assistant(user_id: str, payload: UserAiAssistantUpdateIn, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")

    subscription = db.query(Subscription).filter_by(user_id=user_id).first()
    if not subscription:
        subscription = Subscription(
            user_id=user_id,
            trial_ends_at=datetime.now(timezone.utc) + timedelta(days=30),
        )
        db.add(subscription)
        db.flush()

    subscription.ai_assistant_enabled = payload.enabled

    config = db.query(AiAssistantConfig).filter_by(user_id=user_id).first()
    if not config:
        config = AiAssistantConfig(user_id=user_id)
        db.add(config)
        db.flush()
    config.enabled = payload.enabled

    db.commit()
    return _to_detail_out(user, db)
