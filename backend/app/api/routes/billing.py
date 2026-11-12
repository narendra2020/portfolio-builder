"""
User-facing billing: trial/subscription status, UPI upgrade details,
submitting a payment claim for manual admin review, and the Razorpay
auto-verified gateway flow (order creation, browser-signature verify,
and a webhook) — see app/services/subscription_service.py,
app/services/razorpay_client.py, and app/api/routes/admin_billing.py.
"""
import os
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.models import PaymentRequest, PaymentRequestStatusEnum, UpiSettings, User
from app.schemas.schemas import (
    BillingStatusOut,
    PaymentRequestIn,
    PaymentRequestOut,
    RazorpayOrderIn,
    RazorpayOrderOut,
    RazorpayVerifyRequest,
)
from app.services.razorpay_client import (
    get_razorpay_client,
    razorpay_configured,
    verify_payment_signature,
    verify_webhook_signature,
)
from app.services.subscription_service import (
    UPGRADE_PRICE_RUPEES,
    confirm_payment_request,
    get_subscription,
)

_PRODUCT_PRICES_RUPEES = {
    "subscription": UPGRADE_PRICE_RUPEES,
    "ai_assistant": settings.AI_ASSISTANT_ADD_ON_PRICE_RUPEES,
}
# QR Store Builder "Pro" plan: offered only when a price is configured.
# Approval just marks the PaymentRequest approved; the QR Store Builder
# derives the plan from that row (see qrcode-builder services/plans.py).
if settings.QR_STORE_PRO_PRICE_RUPEES > 0:
    _PRODUCT_PRICES_RUPEES["qr_store_pro"] = settings.QR_STORE_PRO_PRICE_RUPEES
if settings.QR_SPLIT_BILL_PRICE_RUPEES > 0:
    _PRODUCT_PRICES_RUPEES["qr_split_bill"] = settings.QR_SPLIT_BILL_PRICE_RUPEES
if settings.QR_PRO_SPLIT_PRICE_RUPEES > 0:
    _PRODUCT_PRICES_RUPEES["qr_pro_split"] = settings.QR_PRO_SPLIT_PRICE_RUPEES

router = APIRouter(prefix="/api/billing", tags=["billing"])

_ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
_MAX_BYTES = 5 * 1024 * 1024


@router.get("/status", response_model=BillingStatusOut)
def get_billing_status(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    subscription = get_subscription(current_user, db)
    now = datetime.now(timezone.utc)
    if subscription:
        deadline = subscription.paid_until or subscription.trial_ends_at
        days_remaining = max((deadline - now).days, 0) if deadline > now else 0
        sub_status = subscription.status.value
        trial_ends_at = subscription.trial_ends_at
        paid_until = subscription.paid_until
    else:
        days_remaining = 0
        sub_status = "active"
        trial_ends_at = None
        paid_until = None

    upi = db.query(UpiSettings).first()
    # Only a pending *UPI* claim actually blocks the UI with "awaiting admin
    # review" — a pending Razorpay row is just an abandoned/failed checkout
    # attempt (no admin ever reviews those) and must not block retrying.
    pending = (
        db.query(PaymentRequest)
        .filter_by(user_id=current_user.id, status=PaymentRequestStatusEnum.pending, method="upi")
        .first()
        is not None
    )
    upi_enabled = upi.upi_enabled if upi else True
    razorpay_enabled = upi.razorpay_enabled if upi else False
    razorpay_ready = razorpay_enabled and razorpay_configured()
    return BillingStatusOut(
        subscription_status=sub_status,
        trial_ends_at=trial_ends_at,
        paid_until=paid_until,
        days_remaining=days_remaining,
        amount_rupees=UPGRADE_PRICE_RUPEES,
        upi_id=upi.upi_id if upi else None,
        qr_image_url=f"/api/uploads/{upi.qr_image_path}" if upi and upi.qr_image_path else None,
        pending_request=pending,
        upi_enabled=upi_enabled,
        razorpay_enabled=razorpay_ready,
        razorpay_key_id=settings.RAZORPAY_KEY_ID if razorpay_ready else None,
    )


@router.post("/payment-requests", response_model=PaymentRequestOut)
def create_payment_request(
    payload: PaymentRequestIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.product not in _PRODUCT_PRICES_RUPEES:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Unknown product.")
    existing_pending = (
        db.query(PaymentRequest)
        .filter_by(user_id=current_user.id, product=payload.product, status=PaymentRequestStatusEnum.pending, method="upi")
        .first()
    )
    if existing_pending:
        raise HTTPException(status.HTTP_409_CONFLICT, "You already have a payment claim pending review.")
    request = PaymentRequest(
        user_id=current_user.id,
        product=payload.product,
        amount_rupees=_PRODUCT_PRICES_RUPEES[payload.product],
        reference_note=payload.reference_note,
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return request


@router.post("/payment-requests/{request_id}/screenshot", response_model=PaymentRequestOut)
def upload_payment_screenshot(
    request_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    request = db.get(PaymentRequest, request_id)
    if not request or request.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
    if request.status != PaymentRequestStatusEnum.pending:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "This claim has already been reviewed.")

    ext = file.filename.rsplit(".", 1)[-1].lower() if file.filename and "." in file.filename else ""
    if ext not in _ALLOWED_EXTENSIONS:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Unsupported file type.")
    raw_bytes = file.file.read()
    if len(raw_bytes) > _MAX_BYTES:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Image must be 5MB or smaller.")

    upload_dir = os.path.join(settings.UPLOADS_DIR, "payment-screenshots", current_user.id)
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"pay-{uuid.uuid4().hex}.{ext}"
    with open(os.path.join(upload_dir, filename), "wb") as f:
        f.write(raw_bytes)

    request.screenshot_path = f"payment-screenshots/{current_user.id}/{filename}"
    db.commit()
    db.refresh(request)
    return request


@router.post("/razorpay/order", response_model=RazorpayOrderOut)
def create_razorpay_order(
    payload: RazorpayOrderIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.product not in _PRODUCT_PRICES_RUPEES:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Unknown product.")

    upi = db.query(UpiSettings).first()
    if not (upi and upi.razorpay_enabled and razorpay_configured()):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Razorpay payments are not enabled.")

    existing_pending = (
        db.query(PaymentRequest)
        .filter_by(user_id=current_user.id, product=payload.product, status=PaymentRequestStatusEnum.pending, method="upi")
        .first()
    )
    if existing_pending:
        raise HTTPException(status.HTTP_409_CONFLICT, "You already have a payment claim pending review.")

    amount_rupees = _PRODUCT_PRICES_RUPEES[payload.product]
    amount_paise = amount_rupees * 100
    client = get_razorpay_client()
    order = client.order.create({
        "amount": amount_paise,
        "currency": "INR",
        "receipt": f"{current_user.id}:{payload.product}",
    })

    request = PaymentRequest(
        user_id=current_user.id,
        product=payload.product,
        method="razorpay",
        amount_rupees=amount_rupees,
        razorpay_order_id=order["id"],
    )
    db.add(request)
    db.commit()

    return RazorpayOrderOut(
        order_id=order["id"],
        amount=amount_paise,
        currency="INR",
        key_id=settings.RAZORPAY_KEY_ID,
    )


@router.post("/razorpay/verify", response_model=PaymentRequestOut)
def verify_razorpay_payment(
    payload: RazorpayVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    request = (
        db.query(PaymentRequest)
        .filter_by(user_id=current_user.id, razorpay_order_id=payload.razorpay_order_id)
        .first()
    )
    if not request:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No matching Razorpay order found.")

    if not verify_payment_signature(
        payload.razorpay_order_id, payload.razorpay_payment_id, payload.razorpay_signature
    ):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Payment signature verification failed.")

    request.razorpay_payment_id = payload.razorpay_payment_id
    request.razorpay_signature = payload.razorpay_signature
    db.commit()

    confirm_payment_request(request, db)
    db.refresh(request)
    return request


@router.post("/razorpay/webhook", include_in_schema=False)
async def razorpay_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Unauthenticated endpoint (Razorpay cannot send a JWT) — authenticated
    instead via the X-Razorpay-Signature header, HMAC-verified against
    RAZORPAY_WEBHOOK_SECRET. Idempotent: redelivery of an already-handled
    event is a no-op (see confirm_payment_request).
    """
    body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")
    if not verify_webhook_signature(body, signature):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid webhook signature.")

    payload = await request.json()
    event = payload.get("event", "")
    if event in ("payment.captured", "order.paid"):
        order_id = (
            payload.get("payload", {}).get("payment", {}).get("entity", {}).get("order_id")
            or payload.get("payload", {}).get("order", {}).get("entity", {}).get("id")
        )
        if order_id:
            payment_request = db.query(PaymentRequest).filter_by(razorpay_order_id=order_id).first()
            if payment_request:
                payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
                if payment_entity.get("id"):
                    payment_request.razorpay_payment_id = payment_entity["id"]
                    db.commit()
                confirm_payment_request(payment_request, db)

    return {"status": "ok"}
