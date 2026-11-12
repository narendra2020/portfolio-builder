"""
Profile retrieval/update and the final template-confirm onboarding step.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.models import AudienceType, OnboardingStatusEnum, PortfolioTemplate, User
from app.schemas.schemas import ProfileUpdateIn, SetAudienceIn, SetTemplateIn, UserProfileOut

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("", response_model=UserProfileOut)
def get_profile(current_user: User = Depends(get_current_user)):
    return current_user.profile


@router.put("", response_model=UserProfileOut)
def update_profile(
    payload: ProfileUpdateIn, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    profile = current_user.profile
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    if profile.onboarding_status == OnboardingStatusEnum.profile_pending:
        profile.onboarding_status = OnboardingStatusEnum.template_pending
    db.commit()
    return profile


@router.put("/audience", response_model=UserProfileOut)
def set_audience(
    payload: SetAudienceIn, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    audience = db.query(AudienceType).filter_by(id=payload.audience_type_id, is_active=True).first()
    if not audience:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Audience type not found")
    profile = current_user.profile
    profile.audience_type_id = payload.audience_type_id
    if profile.onboarding_status == OnboardingStatusEnum.audience_pending:
        profile.onboarding_status = OnboardingStatusEnum.profile_pending
    db.commit()
    return profile


@router.put("/template", response_model=UserProfileOut)
def set_template(
    payload: SetTemplateIn, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    template = db.get(PortfolioTemplate, payload.template_id)
    if not template or not template.is_active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Template not found")
    profile = current_user.profile
    profile.template_id = payload.template_id
    if profile.onboarding_status == OnboardingStatusEnum.template_pending:
        profile.onboarding_status = OnboardingStatusEnum.onboarding_complete
    db.commit()
    return profile
