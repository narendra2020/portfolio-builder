"""
Logged-in phone-number ownership verification, reusing the same OTP
transaction table, provider (WhatsApp Business / dev console) and
security controls (hashed OTP, expiry, attempt limit, resend cooldown)
as signup. On success it returns a short-lived signed proof token
(`type: number_proof`) bound to the user, the number and a purpose,
which sibling services (the QR Store Builder) accept as proof that the
user controls that number. No session is issued and no account is
created or changed here.
"""
import re
from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from jose import jwt
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.security import hash_value, hmac_lookup_hash, verify_value
from app.db.session import get_db
from app.models.models import OtpTransaction, User
from app.services import otp_service

router = APIRouter(prefix="/api/auth/number-verification", tags=["auth"])

PROOF_TOKEN_MINUTES = 15
_PURPOSES = ("qr_whatsapp",)


class NumberVerificationStartIn(BaseModel):
    phone: str = Field(max_length=25)
    purpose: Literal["qr_whatsapp"] = "qr_whatsapp"


class NumberVerificationConfirmIn(BaseModel):
    transaction_id: str
    otp: str = Field(max_length=10)


class NumberVerificationStartOut(BaseModel):
    transaction_id: str


class NumberVerificationProofOut(BaseModel):
    proof_token: str
    phone: str
    expires_in_seconds: int


def normalize_e164(raw: str) -> str:
    """'+<country><number>' (8-15 digits) or a 10-digit Indian mobile."""
    raw = (raw or "").strip()
    digits = re.sub(r"\D", "", raw)
    if not raw.startswith("+"):
        return otp_service.normalize_mobile_number(raw)
    if not 8 <= len(digits) <= 15 or digits.startswith("0"):
        raise otp_service.OtpError("Enter a valid phone number with country code.")
    if digits.startswith("91") and (len(digits) != 12 or digits[2] not in "6789"):
        raise otp_service.OtpError("Enter a valid 10-digit Indian mobile number.")
    return "+" + digits


@router.post("/start", response_model=NumberVerificationStartOut)
async def start(
    payload: NumberVerificationStartIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        phone = normalize_e164(payload.phone)
    except otp_service.OtpError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc))
    phone_hash = hmac_lookup_hash(phone)
    now = datetime.now(timezone.utc)

    recent = (
        db.query(OtpTransaction)
        .filter_by(mobile_number_hash=phone_hash)
        .order_by(OtpTransaction.last_sent_at.desc())
        .first()
    )
    if recent and (now - recent.last_sent_at).total_seconds() < settings.OTP_RESEND_COOLDOWN_SECONDS:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Please wait before requesting another code.")
    hour_ago = now - timedelta(hours=1)
    sent_last_hour = (
        db.query(OtpTransaction)
        .filter(OtpTransaction.requested_by_user_id == current_user.id, OtpTransaction.created_at > hour_ago)
        .count()
    )
    if sent_last_hour >= 5:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Too many verification requests. Please try again later.")

    otp = otp_service._generate_otp()
    transaction = OtpTransaction(
        mobile_number_hash=phone_hash,
        otp_hash=hash_value(otp),
        attempts=0,
        expires_at=now + timedelta(minutes=settings.OTP_EXPIRE_MINUTES),
        pending_mobile_number=phone,
        purpose="number_verification",
        requested_by_user_id=current_user.id,
    )
    db.add(transaction)
    db.flush()
    result = await otp_service.get_sms_provider().send_otp(phone, otp, transaction.id)
    if not result.success:
        db.rollback()
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Could not send the code on WhatsApp. Please try again.")
    transaction.provider_reference = result.provider_reference
    db.commit()
    return NumberVerificationStartOut(transaction_id=transaction.id)


@router.post("/confirm", response_model=NumberVerificationProofOut)
def confirm(
    payload: NumberVerificationConfirmIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    invalid = HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid or expired code.")
    try:
        transaction = db.get(OtpTransaction, payload.transaction_id)
    except Exception:
        db.rollback()
        raise invalid
    if (
        not transaction
        or transaction.purpose != "number_verification"
        or transaction.requested_by_user_id != current_user.id
        or transaction.consumed_at is not None
        or datetime.now(timezone.utc) > transaction.expires_at
    ):
        raise invalid
    if transaction.attempts >= settings.OTP_MAX_ATTEMPTS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Too many attempts. Please request a new code.")
    if not verify_value(payload.otp, transaction.otp_hash):
        transaction.attempts += 1
        db.commit()
        raise invalid

    transaction.consumed_at = datetime.now(timezone.utc)
    db.commit()
    expires = datetime.now(timezone.utc) + timedelta(minutes=PROOF_TOKEN_MINUTES)
    token = jwt.encode(
        {"sub": current_user.id, "type": "number_proof", "purpose": "qr_whatsapp",
         "num": transaction.pending_mobile_number, "exp": expires},
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return NumberVerificationProofOut(
        proof_token=token, phone=transaction.pending_mobile_number, expires_in_seconds=PROOF_TOKEN_MINUTES * 60
    )
