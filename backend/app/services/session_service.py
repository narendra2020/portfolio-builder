"""
Refresh-token rotation, reuse detection, and session management.
"""
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, decode_token, hash_value, verify_value
from app.models.models import User, UserSession


class SessionError(Exception):
    """Generic refresh/session failure. Message is safe to show the user."""


def _revoke_chain(session: UserSession, db: Session) -> None:
    """Reuse detection: revokes every session for this user, since an
    already-rotated refresh token being presented again means it was
    likely stolen."""
    db.query(UserSession).filter_by(user_id=session.user_id, is_revoked=False).update({"is_revoked": True})
    db.commit()


def rotate_refresh_token(refresh_token: str, db: Session, user_agent: str | None = None) -> tuple[str, str]:
    try:
        payload = decode_token(refresh_token)
    except ValueError:
        raise SessionError("Invalid or expired session. Please log in again.")

    if payload.get("type") != "refresh":
        raise SessionError("Invalid or expired session. Please log in again.")

    session = db.get(UserSession, payload.get("sid"))
    if not session or not verify_value(refresh_token, session.refresh_token_hash):
        raise SessionError("Invalid or expired session. Please log in again.")

    if session.is_revoked:
        _revoke_chain(session, db)
        raise SessionError("Invalid or expired session. Please log in again.")

    if datetime.now(timezone.utc) > session.expires_at:
        raise SessionError("Invalid or expired session. Please log in again.")

    user = db.get(User, session.user_id)
    if not user or not user.is_active:
        raise SessionError("Invalid or expired session. Please log in again.")

    new_session = UserSession(
        user_id=user.id,
        refresh_token_hash="",
        user_agent=user_agent,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(new_session)
    db.flush()

    new_refresh_token = create_refresh_token(user.id, new_session.id)
    new_session.refresh_token_hash = hash_value(new_refresh_token)

    session.is_revoked = True
    session.replaced_by_id = new_session.id

    new_access_token = create_access_token(user.id, user.role.value)
    db.commit()
    return new_access_token, new_refresh_token


def logout(refresh_token: str, db: Session) -> None:
    try:
        payload = decode_token(refresh_token)
    except ValueError:
        return
    session = db.get(UserSession, payload.get("sid"))
    if session:
        session.is_revoked = True
        db.commit()


def logout_all(user_id: str, db: Session) -> None:
    db.query(UserSession).filter_by(user_id=user_id, is_revoked=False).update({"is_revoked": True})
    db.commit()


def revoke_session(user_id: str, session_id: str, db: Session) -> None:
    session = db.get(UserSession, session_id)
    if session and session.user_id == user_id:
        session.is_revoked = True
        db.commit()
