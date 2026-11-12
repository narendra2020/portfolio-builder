"""
Trial/subscription entitlement checks. No payment gateway is
integrated — upgrades are confirmed by manual admin review of a
PaymentRequest (see app/api/routes/billing.py / admin_billing.py).
Expiry is evaluated lazily (no cron): any read of a user's
subscription status flips trial->expired once trial_ends_at has
passed, and unpublishes their site if it was live.
"""
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.models import (
    PaymentRequest,
    PaymentRequestStatusEnum,
    PublishedPortfolio,
    PublishedPortfolioStatusEnum,
    Subscription,
    SubscriptionStatusEnum,
    User,
)
from app.services import site_generator

TRIAL_DAYS = 30
UPGRADE_PRICE_RUPEES = settings.UPGRADE_PRICE_RUPEES
UPGRADE_DURATION_DAYS = 365


def _sync_status(subscription: Subscription, db: Session) -> Subscription:
    now = datetime.now(timezone.utc)
    is_live = (subscription.paid_until and subscription.paid_until > now) or (
        subscription.status == SubscriptionStatusEnum.trial and subscription.trial_ends_at > now
    )
    if is_live:
        new_status = SubscriptionStatusEnum.active if subscription.paid_until and subscription.paid_until > now else SubscriptionStatusEnum.trial
    else:
        new_status = SubscriptionStatusEnum.expired

    if new_status != subscription.status:
        subscription.status = new_status
        if new_status == SubscriptionStatusEnum.expired:
            row = db.query(PublishedPortfolio).filter_by(user_id=subscription.user_id).first()
            if row and row.status == PublishedPortfolioStatusEnum.published and row.slug:
                site_generator.unpublish_site(row.slug)
                row.status = PublishedPortfolioStatusEnum.draft
                row.published_at = None
        db.commit()
        db.refresh(subscription)
    return subscription


def get_subscription(user: User, db: Session) -> Subscription | None:
    subscription = db.query(Subscription).filter_by(user_id=user.id).first()
    if not subscription:
        return None
    return _sync_status(subscription, db)


def is_entitled(user: User, db: Session) -> bool:
    subscription = get_subscription(user, db)
    if not subscription:
        return True  # no subscription row (e.g. seeded admin) — not trial-gated
    return subscription.status in (SubscriptionStatusEnum.trial, SubscriptionStatusEnum.active)


def require_entitled(user: User, db: Session) -> None:
    if not is_entitled(user, db):
        raise HTTPException(
            status.HTTP_402_PAYMENT_REQUIRED,
            "Your free trial has ended. Upgrade to publish your portfolio again.",
        )


def is_ai_assistant_entitled(user: User, db: Session) -> bool:
    subscription = get_subscription(user, db)
    return bool(subscription and subscription.ai_assistant_enabled)


def require_ai_assistant_entitled(user: User, db: Session) -> None:
    if not is_ai_assistant_entitled(user, db):
        raise HTTPException(
            status.HTTP_402_PAYMENT_REQUIRED,
            "AI Assistant is not included in your current plan. Upgrade to enable it.",
        )


def require_resume_builder_entitled(user: User, db: Session) -> None:
    """
    No-op for now — the Resume Builder is not gated behind a separate
    entitlement yet. Kept as a real call site (see
    app/api/routes/resumes.py::generate/export) so a future plan tier can
    gate it here without touching route code.
    """
    return None


def confirm_payment_request(
    request: PaymentRequest, db: Session, reviewer_id: str | None = None
) -> bool:
    """
    Approves a payment claim and grants the corresponding entitlement.
    Returns False (no-op) if the request was not pending — callers
    (admin approve, Razorpay browser-verify, Razorpay webhook) should
    treat that as "already handled", not an error, since the browser
    callback and the webhook can race or redeliver.
    """
    if request.status != PaymentRequestStatusEnum.pending:
        return False

    now = datetime.now(timezone.utc)
    subscription = db.query(Subscription).filter_by(user_id=request.user_id).first()
    if not subscription:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "This user has no subscription record.")

    if request.product == "ai_assistant":
        subscription.ai_assistant_enabled = True
    elif request.product in ("qr_store_pro", "qr_split_bill", "qr_pro_split"):
        pass  # entitlement is derived from this approved row by the QR Store Builder
    else:
        base = subscription.paid_until if subscription.paid_until and subscription.paid_until > now else now
        subscription.paid_until = base + timedelta(days=UPGRADE_DURATION_DAYS)
        subscription.status = SubscriptionStatusEnum.active

    request.status = PaymentRequestStatusEnum.approved
    request.reviewed_by_id = reviewer_id
    request.reviewed_at = now
    db.commit()
    db.refresh(request)
    return True
