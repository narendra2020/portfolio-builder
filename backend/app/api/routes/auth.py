"""
Auth: signup (name + password + WhatsApp OTP verification), password
login, OTP resend/verify, token refresh, logout, and session
introspection/management.
"""
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.models import User, UserSession
from app.schemas.schemas import (
    AuthTokensOut,
    LoginIn,
    LogoutIn,
    OtpRequestOut,
    OtpResendIn,
    OtpVerifyIn,
    PasswordResetRequestIn,
    PasswordResetVerifyIn,
    SessionOut,
    SignupIn,
    TokenRefreshIn,
    UserSessionOut,
)
from app.services import otp_service, session_service
from app.services.onboarding import next_step_for

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/signup", response_model=OtpRequestOut)
async def signup(payload: SignupIn, db: Session = Depends(get_db)):
    try:
        transaction_id = await otp_service.signup(
            payload.full_name, payload.mobile_number, payload.password, db
        )
    except otp_service.AuthError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc))
    except otp_service.OtpError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))
    return OtpRequestOut(transaction_id=transaction_id)


@router.post("/login", response_model=AuthTokensOut)
def login(
    payload: LoginIn,
    db: Session = Depends(get_db),
    user_agent: str | None = Header(default=None),
):
    try:
        user, access_token, refresh_token = otp_service.login(
            payload.mobile_number, payload.password, db, user_agent
        )
    except otp_service.AuthError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc))

    status_ = user.profile.onboarding_status
    return AuthTokensOut(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user,
        onboarding_status=status_,
        next_step=next_step_for(status_),
    )


@router.post("/otp/resend", response_model=OtpRequestOut)
async def resend_otp(payload: OtpResendIn, db: Session = Depends(get_db)):
    try:
        transaction_id = await otp_service.resend_otp(payload.transaction_id, db)
    except otp_service.OtpError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))
    return OtpRequestOut(transaction_id=transaction_id)


@router.post("/otp/verify", response_model=AuthTokensOut)
def verify_otp(
    payload: OtpVerifyIn,
    db: Session = Depends(get_db),
    user_agent: str | None = Header(default=None),
):
    try:
        user, access_token, refresh_token = otp_service.verify_otp(
            payload.transaction_id, payload.otp, db, user_agent
        )
    except otp_service.OtpError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))

    status_ = user.profile.onboarding_status
    return AuthTokensOut(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user,
        onboarding_status=status_,
        next_step=next_step_for(status_),
    )


@router.post("/password-reset/request", response_model=OtpRequestOut)
async def password_reset_request(payload: PasswordResetRequestIn, db: Session = Depends(get_db)):
    try:
        transaction_id = await otp_service.request_password_reset(payload.mobile_number, db)
    except otp_service.AuthError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc))
    except otp_service.OtpError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))
    return OtpRequestOut(transaction_id=transaction_id)


@router.post("/password-reset/verify", response_model=AuthTokensOut)
def password_reset_verify(
    payload: PasswordResetVerifyIn,
    db: Session = Depends(get_db),
    user_agent: str | None = Header(default=None),
):
    try:
        user, access_token, refresh_token = otp_service.verify_password_reset(
            payload.transaction_id, payload.otp, payload.new_password, db, user_agent
        )
    except otp_service.OtpError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))
    except otp_service.AuthError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))

    status_ = user.profile.onboarding_status
    return AuthTokensOut(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user,
        onboarding_status=status_,
        next_step=next_step_for(status_),
    )


@router.post("/token/refresh")
def refresh_token(
    payload: TokenRefreshIn,
    db: Session = Depends(get_db),
    user_agent: str | None = Header(default=None),
):
    try:
        access_token, new_refresh_token = session_service.rotate_refresh_token(
            payload.refresh_token, db, user_agent
        )
    except session_service.SessionError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc))
    return {"access_token": access_token, "refresh_token": new_refresh_token, "token_type": "bearer"}


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(payload: LogoutIn, db: Session = Depends(get_db)):
    session_service.logout(payload.refresh_token, db)


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
def logout_all(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    session_service.logout_all(current_user.id, db)


@router.get("/session", response_model=SessionOut)
def get_session(current_user: User = Depends(get_current_user)):
    status_ = current_user.profile.onboarding_status
    return SessionOut(user=current_user, onboarding_status=status_, next_step=next_step_for(status_))


@router.get("/sessions", response_model=list[UserSessionOut])
def list_sessions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(UserSession).filter_by(user_id=current_user.id).order_by(UserSession.created_at.desc()).all()


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(
    session_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    session_service.revoke_session(current_user.id, session_id, db)
