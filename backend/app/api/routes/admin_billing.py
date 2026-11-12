"""
Super-admin billing management: review payment claims and configure the
UPI QR code / ID and payment-method toggles shown to users on the
upgrade page.
"""
import os
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.core.config import settings
from app.db.session import get_db
from app.models.models import (
    PaymentRequest,
    PaymentRequestStatusEnum,
    RoleEnum,
    UpiSettings,
    User,
)
from app.schemas.schemas import PaymentRequestAdminOut, UpiSettingsIn, UpiSettingsOut
from app.services.razorpay_client import razorpay_configured
from app.services.subscription_service import confirm_payment_request

router = APIRouter(
    prefix="/api/admin/billing",
    tags=["admin-billing"],
    dependencies=[Depends(require_role(RoleEnum.super_admin))],
)

_ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
_MAX_BYTES = 2 * 1024 * 1024


def _to_admin_out(request: PaymentRequest) -> PaymentRequestAdminOut:
    return PaymentRequestAdminOut(
        id=request.id,
        status=request.status.value,
        product=request.product,
        method=request.method,
        amount_rupees=request.amount_rupees,
        reference_note=request.reference_note,
        created_at=request.created_at,
        reviewed_at=request.reviewed_at,
        user_id=request.user_id,
        user_full_name=request.user.full_name,
        screenshot_url=f"/api/uploads/{request.screenshot_path}" if request.screenshot_path else None,
    )


@router.get("/payment-requests", response_model=list[PaymentRequestAdminOut])
def list_payment_requests(status_filter: str | None = None, db: Session = Depends(get_db)):
    query = db.query(PaymentRequest)
    if status_filter:
        query = query.filter(PaymentRequest.status == PaymentRequestStatusEnum(status_filter))
    else:
        # Razorpay is auto-verified and auto-approved on success — a Razorpay
        # row still "pending" is just an abandoned/failed checkout attempt,
        # not something an admin can manually review (there's no screenshot
        # or reference to eyeball). Hide those from the default listing so
        # they don't clutter "pending payment claims".
        query = query.filter(
            ~((PaymentRequest.status == PaymentRequestStatusEnum.pending) & (PaymentRequest.method == "razorpay"))
        )
    requests = query.order_by(PaymentRequest.created_at.desc()).all()
    return [_to_admin_out(r) for r in requests]


@router.post("/payment-requests/{request_id}/approve", response_model=PaymentRequestAdminOut)
def approve_payment_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    request = db.get(PaymentRequest, request_id)
    if not request:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
    if request.status != PaymentRequestStatusEnum.pending:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "This claim has already been reviewed.")

    confirm_payment_request(request, db, reviewer_id=current_user.id)
    return _to_admin_out(request)


@router.post("/payment-requests/{request_id}/reject", response_model=PaymentRequestAdminOut)
def reject_payment_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    request = db.get(PaymentRequest, request_id)
    if not request:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
    if request.status != PaymentRequestStatusEnum.pending:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "This claim has already been reviewed.")

    request.status = PaymentRequestStatusEnum.rejected
    request.reviewed_by_id = current_user.id
    request.reviewed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(request)
    return _to_admin_out(request)


def _to_upi_settings_out(upi: UpiSettings | None) -> UpiSettingsOut:
    if not upi:
        return UpiSettingsOut()
    return UpiSettingsOut(
        upi_id=upi.upi_id,
        qr_image_url=f"/api/uploads/{upi.qr_image_path}" if upi.qr_image_path else None,
        upi_enabled=upi.upi_enabled,
        razorpay_enabled=upi.razorpay_enabled,
    )


@router.get("/upi-settings", response_model=UpiSettingsOut)
def get_upi_settings(db: Session = Depends(get_db)):
    upi = db.query(UpiSettings).first()
    return _to_upi_settings_out(upi)


@router.put("/upi-settings", response_model=UpiSettingsOut)
def update_upi_settings(payload: UpiSettingsIn, db: Session = Depends(get_db)):
    upi = db.query(UpiSettings).first()
    if not upi:
        upi = UpiSettings()
        db.add(upi)
    upi.upi_id = payload.upi_id
    db.commit()
    db.refresh(upi)
    return _to_upi_settings_out(upi)


@router.post("/payment-settings", response_model=UpiSettingsOut)
def update_payment_settings(
    upi_enabled: bool | None = Form(None),
    razorpay_enabled: bool | None = Form(None),
    db: Session = Depends(get_db),
):
    if razorpay_enabled and not razorpay_configured():
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET in the server environment before enabling Razorpay.",
        )
    upi = db.query(UpiSettings).first()
    if not upi:
        upi = UpiSettings()
        db.add(upi)
    if upi_enabled is not None:
        upi.upi_enabled = upi_enabled
    if razorpay_enabled is not None:
        upi.razorpay_enabled = razorpay_enabled
    db.commit()
    db.refresh(upi)
    return _to_upi_settings_out(upi)


@router.put("/upi-settings/qr-image", response_model=UpiSettingsOut)
def update_upi_qr_image(file: UploadFile = File(...), db: Session = Depends(get_db)):
    ext = file.filename.rsplit(".", 1)[-1].lower() if file.filename and "." in file.filename else ""
    if ext not in _ALLOWED_EXTENSIONS:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Unsupported file type.")
    raw_bytes = file.file.read()
    if len(raw_bytes) > _MAX_BYTES:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Image must be 2MB or smaller.")

    upload_dir = os.path.join(settings.UPLOADS_DIR, "admin")
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"upi-qr-{uuid.uuid4().hex}.{ext}"
    with open(os.path.join(upload_dir, filename), "wb") as f:
        f.write(raw_bytes)

    upi = db.query(UpiSettings).first()
    if not upi:
        upi = UpiSettings()
        db.add(upi)
    upi.qr_image_path = f"admin/{filename}"
    db.commit()
    db.refresh(upi)
    return _to_upi_settings_out(upi)
