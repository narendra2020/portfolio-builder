"""
Pydantic request/response schemas.
"""
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict

from app.models.models import OnboardingStatusEnum, RoleEnum


# ---- Auth / OTP ----

class SignupIn(BaseModel):
    full_name: str
    mobile_number: str
    password: str


class LoginIn(BaseModel):
    mobile_number: str
    password: str


class OtpRequestOut(BaseModel):
    transaction_id: str


class OtpVerifyIn(BaseModel):
    transaction_id: str
    otp: str


class OtpResendIn(BaseModel):
    transaction_id: str


class PasswordResetRequestIn(BaseModel):
    mobile_number: str


class PasswordResetVerifyIn(BaseModel):
    transaction_id: str
    otp: str
    new_password: str


class TokenRefreshIn(BaseModel):
    refresh_token: str


class LogoutIn(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    full_name: str
    role: RoleEnum
    is_active: bool
    created_at: datetime


class AuthTokensOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserOut
    onboarding_status: OnboardingStatusEnum
    next_step: str


class SessionOut(BaseModel):
    user: UserOut
    onboarding_status: OnboardingStatusEnum
    next_step: str


class UserAdminOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    full_name: str
    mobile_number: str
    role: RoleEnum
    is_active: bool
    created_at: datetime


class UserAdminDetailOut(BaseModel):
    id: str
    full_name: str
    mobile_number: str
    role: RoleEnum
    is_active: bool
    created_at: datetime

    display_name: Optional[str] = None
    email: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    profile_image: Optional[str] = None

    slug: Optional[str] = None
    publish_status: Optional[str] = None
    published_at: Optional[datetime] = None
    published_url: Optional[str] = None
    ai_assistant_enabled: bool = False
    ai_assistant_config_enabled: bool = False


class AdminPasswordResetIn(BaseModel):
    new_password: str


class UserAiAssistantUpdateIn(BaseModel):
    enabled: bool


class UserAdminCreateIn(BaseModel):
    full_name: str
    mobile_number: str
    password: str
    role: RoleEnum = RoleEnum.registered_user
    is_active: bool = True


class UserSessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    is_revoked: bool
    user_agent: Optional[str] = None
    created_at: datetime
    expires_at: datetime


# ---- Taxonomy ----

class AudienceTypeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    display_order: int


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    audience_type_id: int
    name: str
    slug: str
    display_order: int


class ProfessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category_id: int
    name: str
    slug: str
    display_order: int


class SpecialisationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    profession_id: int
    name: str
    slug: str
    display_order: int


class TaxonomyNodeIn(BaseModel):
    name: str
    slug: str
    display_order: int = 0


class AudienceTypeCreateIn(TaxonomyNodeIn):
    pass


class CategoryCreateIn(TaxonomyNodeIn):
    audience_type_id: int


class ProfessionCreateIn(TaxonomyNodeIn):
    category_id: int


class SpecialisationCreateIn(TaxonomyNodeIn):
    profession_id: int


# ---- Profile ----

class UserProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    display_name: Optional[str] = None
    email: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    profile_image: Optional[str] = None
    audience_type_id: Optional[int] = None
    category_id: Optional[int] = None
    profession_id: Optional[int] = None
    specialisation_id: Optional[int] = None
    template_id: Optional[int] = None
    resume_suggestions: Optional[dict[str, Any]] = None
    onboarding_status: OnboardingStatusEnum


class ImageUploadOut(BaseModel):
    url: str


class ResumeUploadOut(BaseModel):
    suggestions: Optional[dict[str, Any]] = None
    llm_available: bool
    onboarding_status: OnboardingStatusEnum
    next_step: str


class ProfileUpdateIn(BaseModel):
    display_name: Optional[str] = None
    email: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    profile_image: Optional[str] = None


# ---- Questionnaire ----

class QuestionnaireSectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    section_key: str
    section_title: str
    section_order: int
    questions: list[dict[str, Any]]
    profession_id: Optional[int] = None
    audience_type_id: Optional[int] = None


class QuestionnaireAnswerIn(BaseModel):
    section_key: str
    answers: dict[str, Any]


class QuestionnaireResponseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    section_key: str
    answers: dict[str, Any]
    updated_at: datetime


class QuestionnaireSchemaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    profession_id: Optional[int] = None
    audience_type_id: Optional[int] = None
    section_key: str
    section_title: str
    section_order: int
    questions: list[dict[str, Any]]
    is_active: bool


class QuestionnaireSchemaCreateIn(BaseModel):
    profession_id: Optional[int] = None
    audience_type_id: Optional[int] = None
    section_key: str
    section_title: str
    section_order: int = 0
    questions: list[dict[str, Any]] = []


class QuestionnaireSchemaUpdateIn(BaseModel):
    section_title: Optional[str] = None
    section_order: Optional[int] = None
    questions: Optional[list[dict[str, Any]]] = None
    is_active: Optional[bool] = None


# ---- Templates ----

class PortfolioTemplateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    description: Optional[str] = None
    preview_image: Optional[str] = None
    display_order: int
    audience_type_id: Optional[int] = None


class PortfolioTemplateAdminOut(PortfolioTemplateOut):
    template_file: str
    is_active: bool


class PortfolioTemplateCreateIn(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    preview_image: Optional[str] = None
    template_file: str = "default_template.html.j2"
    display_order: int = 0
    audience_type_id: Optional[int] = None


class PortfolioTemplateUpdateIn(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    preview_image: Optional[str] = None
    template_file: Optional[str] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None
    audience_type_id: Optional[int] = None


class SetTemplateIn(BaseModel):
    template_id: int


class SetAudienceIn(BaseModel):
    audience_type_id: int


# ---- Layout ----

class LayoutBlocksOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    blocks: list[dict[str, Any]]
    updated_at: datetime


class LayoutBlocksIn(BaseModel):
    blocks: list[dict[str, Any]]


# ---- Publishing ----

class PublishStatusOut(BaseModel):
    slug: Optional[str] = None
    status: str
    published_at: Optional[datetime] = None
    url: Optional[str] = None
    domain: Optional[str] = None
    base_domain: str
    can_republish: bool = True


class SetSlugIn(BaseModel):
    slug: str


class SlugAvailabilityOut(BaseModel):
    available: bool
    reason: Optional[str] = None


# ---- Billing ----

class BillingStatusOut(BaseModel):
    subscription_status: str
    trial_ends_at: Optional[datetime] = None
    paid_until: Optional[datetime] = None
    days_remaining: int
    amount_rupees: int
    upi_id: Optional[str] = None
    qr_image_url: Optional[str] = None
    pending_request: bool = False
    upi_enabled: bool = True
    razorpay_enabled: bool = False
    razorpay_key_id: Optional[str] = None


class PaymentRequestIn(BaseModel):
    reference_note: Optional[str] = None
    product: str = "subscription"


class PaymentRequestOut(BaseModel):
    id: int
    status: str
    product: str
    method: str = "upi"
    amount_rupees: int
    reference_note: Optional[str] = None
    created_at: datetime
    reviewed_at: Optional[datetime] = None


class PaymentRequestAdminOut(PaymentRequestOut):
    user_id: str
    user_full_name: str
    screenshot_url: Optional[str] = None


class UpiSettingsOut(BaseModel):
    upi_id: Optional[str] = None
    qr_image_url: Optional[str] = None
    upi_enabled: bool = True
    razorpay_enabled: bool = False


class UpiSettingsIn(BaseModel):
    upi_id: Optional[str] = None


class RazorpayOrderIn(BaseModel):
    product: str = "subscription"


class RazorpayOrderOut(BaseModel):
    order_id: str
    amount: int
    currency: str
    key_id: str


class RazorpayVerifyRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


# ---- AI Assistant ----

class AiAssistantLimitsOut(BaseModel):
    max_qa_pairs: int
    question_max_length: int
    answer_max_length: int
    add_on_price_rupees: int


class AiAssistantConfigOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    enabled: bool
    use_profile_data: bool


class AiAssistantConfigUpdateIn(BaseModel):
    enabled: bool
    use_profile_data: bool = True


class AiAssistantStatusOut(BaseModel):
    entitled: bool
    config: AiAssistantConfigOut
    qa_pair_count: int


class QaPairOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    question: str
    answer: str
    display_order: int


class QaPairCreateIn(BaseModel):
    question: str
    answer: str


class ChatRequestIn(BaseModel):
    message: str


class ChatResponseOut(BaseModel):
    answer: str


class AiAssistantPublicInfoOut(BaseModel):
    owner_name: str


# ---- Resume Builder ----

class ResumeCreateIn(BaseModel):
    title: str = "Untitled Resume"
    source: str = "scratch"  # mepage_import | upload_import | scratch
    template_key: str = "ats_professional"


class ResumeListItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    template_key: str
    source: str
    target_role: Optional[str] = None
    ats_score: Optional[int] = None
    updated_at: datetime
    created_at: datetime


class ResumeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    template_key: str
    content: dict[str, Any]
    source: str
    target_role: Optional[str] = None
    ats_score: Optional[int] = None
    ats_analysis: Optional[dict[str, Any]] = None
    tailoring_job_description: Optional[str] = None
    tailoring_match_scores: Optional[dict[str, Any]] = None
    tailoring_gap_analysis: Optional[list[dict[str, Any]]] = None
    last_profile_import_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class ResumeUpdateIn(BaseModel):
    title: Optional[str] = None
    template_key: Optional[str] = None
    content: Optional[dict[str, Any]] = None
    target_role: Optional[str] = None


class ResumeGenerateIn(BaseModel):
    target_role: Optional[str] = None
    job_description: Optional[str] = None


class ResumeGenerateOut(BaseModel):
    resume: ResumeOut
    analysis: dict[str, Any]
    critique: dict[str, Any]
    retried: bool


class ImproveFieldIn(BaseModel):
    current_text: str
    action: str
    context: Optional[str] = None


class ImproveFieldOut(BaseModel):
    revised_text: str


class AtsAnalysisOut(BaseModel):
    categories: dict[str, Any]
    overall_score: int


class JobDescriptionIn(BaseModel):
    job_description: str


class TailoringOut(BaseModel):
    match_scores: dict[str, Any]
    gap_analysis: list[dict[str, Any]]
    suggested_bullet_rewrites: list[dict[str, Any]]


class ResumeVersionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    reason: str
    created_at: datetime
