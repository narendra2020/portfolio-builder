"""
Signup / login / OTP business logic, plus mobile-number normalization.
Kept independent of the SMS/WhatsApp provider used to actually deliver
the code (see app/providers/sms_provider.py) so that swapping
DevConsoleOTPProvider for a real provider later requires no changes
here beyond get_sms_provider().
"""
import re
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_value,
    hmac_lookup_hash,
    verify_value,
)
from app.models.models import OnboardingStatusEnum, OtpTransaction, Subscription, User, UserProfile, UserSession
from app.providers.sms_provider import DevConsoleOTPProvider, SMSProvider
from app.providers.whatsapp_provider import WhatsAppBusinessProvider


class OtpError(Exception):
    """Generic, enumeration-safe OTP failure. Message is safe to show the user."""


class AuthError(Exception):
    """Signup/login failure. Message is safe to show the user."""


def get_sms_provider() -> SMSProvider:
    if settings.OTP_MODE == "provider":
        return WhatsAppBusinessProvider()
    return DevConsoleOTPProvider()


def normalize_mobile_number(raw: str) -> str:
    """Validates a 10-digit Indian mobile number and returns it as +91XXXXXXXXXX."""
    digits = re.sub(r"\D", "", raw.strip())
    if len(digits) != 10:
        raise OtpError("Enter a valid 10-digit mobile number.")
    return "+91" + digits


def _generate_otp() -> str:
    if settings.OTP_MODE == "dev_fixed":
        return settings.FIXED_DEV_OTP
    return "".join(secrets.choice("0123456789") for _ in range(6))


async def signup(full_name: str, mobile_number: str, password: str, db: Session) -> str:
    """Validates signup input, ensures the mobile isn't already registered,
    sends an OTP over WhatsApp, and stashes the pending user data on the
    OtpTransaction row until verify_otp() confirms the code. Returns the
    transaction_id."""
    full_name = full_name.strip()
    if not full_name:
        raise AuthError("Enter your full name.")
    if len(password) < 8:
        raise AuthError("Password must be at least 8 characters long.")

    normalized = normalize_mobile_number(mobile_number)
    mobile_hash = hmac_lookup_hash(normalized)

    if db.query(User).filter_by(mobile_number_hash=mobile_hash).first():
        raise AuthError("This mobile number is already registered. Please log in instead.")

    recent = (
        db.query(OtpTransaction)
        .filter_by(mobile_number_hash=mobile_hash)
        .order_by(OtpTransaction.last_sent_at.desc())
        .first()
    )
    now = datetime.now(timezone.utc)
    if recent and (now - recent.last_sent_at).total_seconds() < settings.OTP_RESEND_COOLDOWN_SECONDS:
        raise OtpError("Please wait before requesting another code.")

    otp = _generate_otp()
    transaction = OtpTransaction(
        mobile_number_hash=mobile_hash,
        otp_hash=hash_value(otp),
        attempts=0,
        expires_at=now + timedelta(minutes=settings.OTP_EXPIRE_MINUTES),
        pending_full_name=full_name,
        pending_password_hash=hash_value(password),
        pending_mobile_number=normalized,
    )
    db.add(transaction)
    db.flush()

    provider = get_sms_provider()
    result = await provider.send_otp(normalized, otp, transaction.id)
    if not result.success:
        db.rollback()
        raise OtpError("Could not send the code. Please try again.")
    transaction.provider_reference = result.provider_reference
    db.commit()

    return transaction.id


async def resend_otp(transaction_id: str, db: Session) -> str:
    transaction = db.get(OtpTransaction, transaction_id)
    if not transaction or transaction.purpose != "auth" or transaction.consumed_at is not None:
        raise OtpError("This code has expired. Please request a new one.")

    now = datetime.now(timezone.utc)
    if (now - transaction.last_sent_at).total_seconds() < settings.OTP_RESEND_COOLDOWN_SECONDS:
        raise OtpError("Please wait before requesting another code.")

    otp = _generate_otp()
    transaction.otp_hash = hash_value(otp)
    transaction.attempts = 0
    transaction.expires_at = now + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)
    transaction.last_sent_at = now
    db.flush()

    provider = get_sms_provider()
    result = await provider.send_otp("", otp, transaction.id)
    if not result.success:
        raise OtpError("Could not send the code. Please try again.")
    transaction.provider_reference = result.provider_reference
    db.commit()

    return transaction.id


async def request_password_reset(mobile_number: str, db: Session) -> str:
    """Initiates a password reset by sending an OTP over WhatsApp to the
    registered mobile number. Returns the OTP transaction id."""
    normalized = normalize_mobile_number(mobile_number)
    mobile_hash = hmac_lookup_hash(normalized)

    user = db.query(User).filter_by(mobile_number_hash=mobile_hash).first()
    if not user or not user.is_active:
        raise AuthError("This mobile number is not registered.")

    now = datetime.now(timezone.utc)
    recent = (
        db.query(OtpTransaction)
        .filter_by(mobile_number_hash=mobile_hash)
        .order_by(OtpTransaction.last_sent_at.desc())
        .first()
    )
    if recent and (now - recent.last_sent_at).total_seconds() < settings.OTP_RESEND_COOLDOWN_SECONDS:
        raise OtpError("Please wait before requesting another code.")

    otp = _generate_otp()
    transaction = OtpTransaction(
        mobile_number_hash=mobile_hash,
        otp_hash=hash_value(otp),
        attempts=0,
        expires_at=now + timedelta(minutes=settings.OTP_EXPIRE_MINUTES),
        pending_mobile_number=normalized,
    )
    db.add(transaction)
    db.flush()

    provider = get_sms_provider()
    result = await provider.send_otp(normalized, otp, transaction.id)
    if not result.success:
        db.rollback()
        raise OtpError("Could not send the code. Please try again.")
    transaction.provider_reference = result.provider_reference
    db.commit()

    return transaction.id


def verify_password_reset(
    transaction_id: str,
    otp: str,
    new_password: str,
    db: Session,
    user_agent: str | None = None,
) -> tuple[User, str, str]:
    """Verifies the OTP and updates the user's password. Returns
    (user, access_token, refresh_token) so the caller can sign the user
    in immediately after resetting the password."""
    if len(new_password) < 8:
        raise AuthError("Password must be at least 8 characters long.")

    transaction = db.get(OtpTransaction, transaction_id)
    if not transaction or transaction.purpose != "auth":
        raise OtpError("Invalid or expired code.")
    if transaction.consumed_at is not None:
        raise OtpError("Invalid or expired code.")
    if datetime.now(timezone.utc) > transaction.expires_at:
        raise OtpError("Invalid or expired code.")
    if transaction.attempts >= settings.OTP_MAX_ATTEMPTS:
        raise OtpError("Too many attempts. Please request a new code.")

    if not verify_value(otp, transaction.otp_hash):
        transaction.attempts += 1
        db.commit()
        raise OtpError("Invalid or expired code.")

    user = db.query(User).filter_by(mobile_number_hash=transaction.mobile_number_hash).first()
    if not user or not user.is_active:
        raise AuthError("This mobile number is not registered.")

    transaction.consumed_at = datetime.now(timezone.utc)
    user.password_hash = hash_value(new_password)
    db.commit()

    access_token, refresh_token = issue_session(user, db, user_agent)
    return user, access_token, refresh_token


def issue_session(user: User, db: Session, user_agent: str | None = None) -> tuple[str, str]:
    """Creates a new UserSession row and returns (access_token, refresh_token)."""
    session = UserSession(
        user_id=user.id,
        refresh_token_hash="",
        user_agent=user_agent,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(session)
    db.flush()

    refresh_token = create_refresh_token(user.id, session.id)
    session.refresh_token_hash = hash_value(refresh_token)
    access_token = create_access_token(user.id, user.role.value)
    db.commit()
    return access_token, refresh_token


def verify_otp(transaction_id: str, otp: str, db: Session, user_agent: str | None = None) -> tuple[User, str, str]:
    """Verifies the OTP, creates the User from the pending signup data, and
    returns (user, access_token, refresh_token). Raises OtpError with a
    generic, enumeration-safe message on any failure (unknown transaction,
    expired, locked, or wrong code)."""
    transaction = db.get(OtpTransaction, transaction_id)
    if not transaction or transaction.purpose != "auth":
        raise OtpError("Invalid or expired code.")
    if transaction.consumed_at is not None:
        raise OtpError("Invalid or expired code.")
    if datetime.now(timezone.utc) > transaction.expires_at:
        raise OtpError("Invalid or expired code.")
    if transaction.attempts >= settings.OTP_MAX_ATTEMPTS:
        raise OtpError("Too many attempts. Please request a new code.")

    if not verify_value(otp, transaction.otp_hash):
        transaction.attempts += 1
        db.commit()
        raise OtpError("Invalid or expired code.")

    transaction.consumed_at = datetime.now(timezone.utc)

    user = db.query(User).filter_by(mobile_number_hash=transaction.mobile_number_hash).first()
    if not user:
        user = User(
            mobile_number_encrypted=transaction.pending_mobile_number or transaction.mobile_number_hash[:32],
            mobile_number_hash=transaction.mobile_number_hash,
            full_name=transaction.pending_full_name or "User",
            password_hash=transaction.pending_password_hash,
        )
        db.add(user)
        db.flush()
        db.add(UserProfile(user_id=user.id, onboarding_status=OnboardingStatusEnum.resume_pending))
        db.add(
            Subscription(
                user_id=user.id,
                trial_ends_at=datetime.now(timezone.utc) + timedelta(days=30),
            )
        )

    db.commit()

    access_token, refresh_token = issue_session(user, db, user_agent)
    return user, access_token, refresh_token


def login(mobile_number: str, password: str, db: Session, user_agent: str | None = None) -> tuple[User, str, str]:
    """Verifies mobile+password and returns (user, access_token, refresh_token).
    Raises AuthError with a generic, enumeration-safe message on any
    failure (unknown mobile, wrong password, or inactive account)."""
    normalized = normalize_mobile_number(mobile_number)
    mobile_hash = hmac_lookup_hash(normalized)

    user = db.query(User).filter_by(mobile_number_hash=mobile_hash).first()
    if not user or not user.is_active or not verify_value(password, user.password_hash):
        raise AuthError("Invalid mobile number or password.")

    access_token, refresh_token = issue_session(user, db, user_agent)
    return user, access_token, refresh_token
