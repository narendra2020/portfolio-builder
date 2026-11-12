"""
Password/OTP hashing, mobile-number lookup hashing, and JWT token utilities.
"""
import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_value(value: str) -> str:
    """Bcrypt-hashes an at-rest secret (e.g. an OTP). Never store plaintext."""
    return pwd_context.hash(value)


def verify_value(plain_value: str, hashed_value: str) -> bool:
    return pwd_context.verify(plain_value, hashed_value)


def hmac_lookup_hash(value: str) -> str:
    """
    Deterministic keyed hash used for lookup/uniqueness of the normalized
    mobile number (mobile_number_hash = HMAC-SHA256(lookup_key, number)).
    Deterministic so the same number always hashes to the same value
    (required for a unique-index lookup), unlike bcrypt.
    """
    return hmac.new(
        settings.MOBILE_LOOKUP_KEY.encode(), value.encode(), hashlib.sha256
    ).hexdigest()


def create_access_token(subject: str, role: str, extra: Optional[dict] = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload: dict[str, Any] = {"sub": subject, "role": role, "exp": expire, "type": "access"}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(subject: str, session_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {"sub": subject, "sid": session_id, "exp": expire, "type": "refresh"}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError as exc:
        raise ValueError("Invalid or expired token") from exc
