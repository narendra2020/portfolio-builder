"""
Maps onboarding status -> the frontend route the user should resume at,
so a page refresh or new login always lands back on the right step.
"""
from app.models.models import OnboardingStatusEnum

_NEXT_STEP = {
    OnboardingStatusEnum.mobile_verified: "/onboarding/resume",
    OnboardingStatusEnum.resume_pending: "/onboarding/resume",
    OnboardingStatusEnum.audience_pending: "/onboarding/audience",
    OnboardingStatusEnum.profile_pending: "/onboarding/profile",
    OnboardingStatusEnum.template_pending: "/template",
    OnboardingStatusEnum.onboarding_complete: "/dashboard",
}


def next_step_for(status: OnboardingStatusEnum) -> str:
    return _NEXT_STEP[status]
