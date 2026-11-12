"""
User-owned publish state: set a slug once, publish/unpublish the
rendered static site (see app/services/site_generator.py). A user may
only choose their subdomain slug a single time — see
app/api/routes/admin_users.py for the admin-only slug reset used for
support cases.
"""
import re
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.models import (
    LayoutBlockSet,
    PublishedPortfolio,
    PublishedPortfolioStatusEnum,
    QuestionnaireResponse,
    User,
)
from app.schemas.schemas import PublishStatusOut, SetSlugIn, SlugAvailabilityOut
from app.services import site_generator
from app.services.subscription_service import require_entitled

router = APIRouter(prefix="/api/publish", tags=["publish"])

SLUG_RE = re.compile(r"^[a-z0-9-]{3,63}$")


def _content_updated_at(user: User, db: Session) -> datetime | None:
    timestamps = []
    if user.profile:
        timestamps.append(user.profile.updated_at)
    layout = db.query(LayoutBlockSet).filter_by(user_id=user.id).first()
    if layout:
        timestamps.append(layout.updated_at)
    for response in db.query(QuestionnaireResponse).filter_by(user_id=user.id).all():
        timestamps.append(response.updated_at)
    return max(timestamps) if timestamps else None


def _can_republish(row: PublishedPortfolio | None, user: User, db: Session) -> bool:
    if not row or row.status != PublishedPortfolioStatusEnum.published:
        return True
    content_updated_at = _content_updated_at(user, db)
    if not content_updated_at or not row.published_at:
        return True
    return content_updated_at > row.published_at


def _to_status_out(row: PublishedPortfolio | None, user: User, db: Session) -> PublishStatusOut:
    if not row:
        return PublishStatusOut(
            slug=None,
            status=PublishedPortfolioStatusEnum.draft.value,
            published_at=None,
            url=None,
            domain=None,
            base_domain=settings.BASE_DOMAIN,
            can_republish=True,
        )
    url = None
    if row.status == PublishedPortfolioStatusEnum.published:
        url = settings.build_public_url(f"{row.slug}.{settings.BASE_DOMAIN}")
    domain = f"{row.slug}.{settings.BASE_DOMAIN}" if row.slug else None
    return PublishStatusOut(
        slug=row.slug,
        status=row.status.value,
        published_at=row.published_at,
        url=url,
        domain=domain,
        base_domain=settings.BASE_DOMAIN,
        can_republish=_can_republish(row, user, db),
    )


@router.get("", response_model=PublishStatusOut)
def get_publish_status(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    row = db.query(PublishedPortfolio).filter_by(user_id=current_user.id).first()
    return _to_status_out(row, current_user, db)


@router.get("/slug-availability", response_model=SlugAvailabilityOut)
def check_slug_availability(
    slug: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    if not SLUG_RE.match(slug):
        return SlugAvailabilityOut(available=False, reason="format")
    taken = (
        db.query(PublishedPortfolio)
        .filter(PublishedPortfolio.slug == slug, PublishedPortfolio.user_id != current_user.id)
        .first()
    )
    if taken:
        return SlugAvailabilityOut(available=False, reason="taken")
    return SlugAvailabilityOut(available=True)


@router.put("/slug", response_model=PublishStatusOut)
def set_slug(
    payload: SetSlugIn, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    if not SLUG_RE.match(payload.slug):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Slug must be 3-63 characters: lowercase letters, digits, and hyphens only.",
        )
    row = db.query(PublishedPortfolio).filter_by(user_id=current_user.id).first()
    if row and row.slug:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Your subdomain is already set and cannot be changed. Contact support if you need it reset.",
        )
    if row:
        row.slug = payload.slug
    else:
        row = PublishedPortfolio(user_id=current_user.id, slug=payload.slug)
        db.add(row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "That slug is already taken.")
    db.refresh(row)
    return _to_status_out(row, current_user, db)


@router.post("", response_model=PublishStatusOut)
def publish(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    row = db.query(PublishedPortfolio).filter_by(user_id=current_user.id).first()
    if not row or not row.slug:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Set a slug before publishing.")
    if not _can_republish(row, current_user, db):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No changes to publish since your last update.")
    require_entitled(current_user, db)
    site_generator.publish_site(current_user, row.slug, db)
    row.status = PublishedPortfolioStatusEnum.published
    row.published_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(row)
    return _to_status_out(row, current_user, db)


@router.post("/unpublish", response_model=PublishStatusOut)
def unpublish(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    row = db.query(PublishedPortfolio).filter_by(user_id=current_user.id).first()
    if row and row.status == PublishedPortfolioStatusEnum.published:
        site_generator.unpublish_site(row.slug)
        row.status = PublishedPortfolioStatusEnum.draft
        row.published_at = None
        db.commit()
        db.refresh(row)
    return _to_status_out(row, current_user, db)
