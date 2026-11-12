"""
SQLAlchemy ORM models for the Portfolio Builder platform (Phase 1: OTP
auth, RBAC, taxonomy, and profile onboarding).
"""
import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class RoleEnum(str, enum.Enum):
    super_admin = "super_admin"
    admin = "admin"
    template_manager = "template_manager"
    content_manager = "content_manager"
    support_user = "support_user"
    registered_user = "registered_user"


class OnboardingStatusEnum(str, enum.Enum):
    mobile_verified = "mobile_verified"
    resume_pending = "resume_pending"
    audience_pending = "audience_pending"
    profile_pending = "profile_pending"
    template_pending = "template_pending"
    onboarding_complete = "onboarding_complete"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    # Encrypted-at-rest normalized mobile number (E.164). Stored as plain
    # text at the application layer for this phase — swap the column for
    # an application-level envelope-encrypted value before production use
    # with real mobile numbers.
    mobile_number_encrypted: Mapped[str] = mapped_column(String(32), nullable=False)
    # Deterministic HMAC-SHA256(lookup_key, number) used for uniqueness /
    # lookup, since the encrypted value above is not directly queryable.
    mobile_number_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[RoleEnum] = mapped_column(
        Enum(RoleEnum, name="role_enum"), nullable=False, default=RoleEnum.registered_user
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    profile: Mapped["UserProfile"] = relationship(
        "UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    sessions: Mapped[list["UserSession"]] = relationship(
        "UserSession", back_populates="user", cascade="all, delete-orphan"
    )


class AudienceType(Base):
    __tablename__ = "audience_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    categories: Mapped[list["Category"]] = relationship(
        "Category", back_populates="audience_type", order_by="Category.display_order"
    )


class Category(Base):
    __tablename__ = "portfolio_categories"
    __table_args__ = (UniqueConstraint("audience_type_id", "slug", name="uq_audience_category_slug"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    audience_type_id: Mapped[int] = mapped_column(Integer, ForeignKey("audience_types.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    audience_type: Mapped["AudienceType"] = relationship("AudienceType", back_populates="categories")
    professions: Mapped[list["Profession"]] = relationship(
        "Profession", back_populates="category", order_by="Profession.display_order"
    )


class Profession(Base):
    __tablename__ = "professions"
    __table_args__ = (UniqueConstraint("category_id", "slug", name="uq_category_profession_slug"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("portfolio_categories.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    category: Mapped["Category"] = relationship("Category", back_populates="professions")
    specialisations: Mapped[list["Specialisation"]] = relationship(
        "Specialisation", back_populates="profession", order_by="Specialisation.display_order"
    )
    questionnaire_schemas: Mapped[list["QuestionnaireSchema"]] = relationship(
        "QuestionnaireSchema", back_populates="profession", order_by="QuestionnaireSchema.section_order"
    )


class Specialisation(Base):
    __tablename__ = "specialisations"
    __table_args__ = (UniqueConstraint("profession_id", "slug", name="uq_profession_specialisation_slug"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    profession_id: Mapped[int] = mapped_column(Integer, ForeignKey("professions.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    profession: Mapped["Profession"] = relationship("Profession", back_populates="specialisations")


class PortfolioTemplate(Base):
    """
    Catalog of visual templates, mirroring the sibling app's `Theme`
    model. `template_file` and `preview_image` are metadata only for now;
    there is no rendering pipeline yet beyond app/services/site_generator.py.
    `audience_type_id` is nullable: null means the template is available
    to every audience (e.g. "Universal"); set it to restrict a template
    to one audience (e.g. "Modern" -> student).
    """
    __tablename__ = "portfolio_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    preview_image: Mapped[str | None] = mapped_column(String(255), nullable=True)
    template_file: Mapped[str] = mapped_column(String(255), nullable=False, default="default_template.html.j2")
    audience_type_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("audience_types.id"), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    audience_type: Mapped["AudienceType | None"] = relationship("AudienceType")


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), unique=True, nullable=False)

    display_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    profile_image: Mapped[str | None] = mapped_column(String(500), nullable=True)

    audience_type_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("audience_types.id"), nullable=True)
    category_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("portfolio_categories.id"), nullable=True)
    profession_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("professions.id"), nullable=True)
    specialisation_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("specialisations.id"), nullable=True)
    template_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("portfolio_templates.id"), nullable=True)

    resume_file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    resume_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    resume_suggestions: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    onboarding_status: Mapped[OnboardingStatusEnum] = mapped_column(
        Enum(OnboardingStatusEnum, name="onboarding_status_enum"),
        nullable=False,
        default=OnboardingStatusEnum.resume_pending,
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="profile")
    audience_type: Mapped["AudienceType | None"] = relationship("AudienceType")
    category: Mapped["Category | None"] = relationship("Category")
    profession: Mapped["Profession | None"] = relationship("Profession")
    specialisation: Mapped["Specialisation | None"] = relationship("Specialisation")
    template: Mapped["PortfolioTemplate | None"] = relationship("PortfolioTemplate")


class OtpTransaction(Base):
    __tablename__ = "otp_transactions"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    mobile_number_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    otp_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    provider_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Signup data captured at /auth/signup time, applied to the new User
    # row only once the OTP is successfully verified (see otp_service.verify_otp).
    pending_full_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    pending_password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    pending_mobile_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    # "auth" (signup / password reset) or "number_verification" (an
    # already-logged-in user proving control of another number, e.g. a
    # QR store's business WhatsApp — see app/api/routes/number_verification.py).
    # verify_otp / verify_password_reset only accept "auth" transactions.
    purpose: Mapped[str] = mapped_column(String(30), nullable=False, server_default="auth")
    requested_by_user_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id"), nullable=True
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class UserSession(Base):
    """
    One row per issued refresh token, enabling rotation, reuse detection,
    and per-session revocation (§5 of the source spec). On each successful
    /token/refresh call the current session is revoked and a new one is
    created with `replaced_by_id` pointing forward; presenting an
    already-revoked refresh token is treated as token reuse and revokes
    the whole chain for that user.
    """
    __tablename__ = "user_sessions"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    refresh_token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    replaced_by_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("user_sessions.id"), nullable=True
    )
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="sessions")


class QuestionnaireSchema(Base):
    """
    Admin/content-manager-authored questions grouped into ordered
    sections, scoped to EITHER a Profession OR an AudienceType (exactly
    one of `profession_id`/`audience_type_id` is set — enforced by
    `ck_schema_scope_xor`) — audience-scoped schemas apply universally
    across every profession under that audience, instead of being
    duplicated per profession. `questions` holds a list of question dicts
    (`key`, `label`, `type`, `options`, `required`, `placeholder`, and for
    `type: "repeater"` a nested `fields` sub-schema + `item_label`) — the
    schema is intentionally free-form JSON rather than normalized rows,
    mirroring the sibling app's `QuestionnaireSchema` pattern.
    """
    __tablename__ = "questionnaire_schemas"
    __table_args__ = (
        CheckConstraint(
            "(profession_id IS NOT NULL) != (audience_type_id IS NOT NULL)",
            name="ck_schema_scope_xor",
        ),
        Index(
            "uq_profession_section_partial",
            "profession_id",
            "section_key",
            unique=True,
            postgresql_where=text("profession_id IS NOT NULL"),
        ),
        Index(
            "uq_audience_section_partial",
            "audience_type_id",
            "section_key",
            unique=True,
            postgresql_where=text("audience_type_id IS NOT NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    profession_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("professions.id"), nullable=True)
    audience_type_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("audience_types.id"), nullable=True)
    section_key: Mapped[str] = mapped_column(String(100), nullable=False)
    section_title: Mapped[str] = mapped_column(String(200), nullable=False)
    section_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    questions: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    profession: Mapped["Profession | None"] = relationship("Profession", back_populates="questionnaire_schemas")
    audience_type: Mapped["AudienceType | None"] = relationship("AudienceType")


class QuestionnaireResponse(Base):
    """
    A user's saved answers for one questionnaire section. Keyed directly
    to the user (not a Website/Portfolio entity, which doesn't exist yet)
    since each user currently has exactly one profile-in-progress.
    """
    __tablename__ = "questionnaire_responses"
    __table_args__ = (UniqueConstraint("user_id", "section_key", name="uq_user_section"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    section_key: Mapped[str] = mapped_column(String(100), nullable=False)
    answers: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class LayoutBlockSet(Base):
    """
    A user's freeform drag-and-drop portfolio layout: an ordered list of
    content blocks (heading/text/image/skills/links), array position
    encodes order. Keyed directly to the user (no Website/Portfolio
    entity exists yet), one layout per user, mirroring
    `QuestionnaireResponse`/`UserProfile.template_id`.
    """
    __tablename__ = "layout_block_sets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), unique=True, nullable=False)
    blocks: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class PublishedPortfolioStatusEnum(str, enum.Enum):
    draft = "draft"
    published = "published"


class PublishedPortfolio(Base):
    """
    Publish state for a user's portfolio: one row per user, mirroring
    LayoutBlockSet. `slug` is the user-chosen subdomain (e.g. "janedoe"
    -> janedoe.localhost:8081), unique across all users. A user may set
    it exactly once (see app/api/routes/publish.py::set_slug); it is
    nullable only so an admin can clear it via the slug-reset endpoint
    in app/api/routes/admin_users.py for support cases.
    """
    __tablename__ = "published_portfolios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), unique=True, nullable=False)
    slug: Mapped[str | None] = mapped_column(String(63), unique=True, nullable=True)
    status: Mapped[PublishedPortfolioStatusEnum] = mapped_column(
        Enum(PublishedPortfolioStatusEnum, name="published_portfolio_status_enum"),
        nullable=False,
        default=PublishedPortfolioStatusEnum.draft,
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class SubscriptionStatusEnum(str, enum.Enum):
    trial = "trial"
    active = "active"
    expired = "expired"


class Subscription(Base):
    """
    One row per user: a 30-day free trial from signup, extendable by a
    year at a time via an admin-approved UPI PaymentRequest. See
    app/services/subscription_service.py for entitlement logic.
    """
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), unique=True, nullable=False)
    status: Mapped[SubscriptionStatusEnum] = mapped_column(
        Enum(SubscriptionStatusEnum, name="subscription_status_enum"),
        nullable=False,
        default=SubscriptionStatusEnum.trial,
    )
    trial_ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    paid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Separate paid add-on: AI Assistant is not included by default in the
    # base trial/subscription, and is granted independently via its own
    # admin-approved PaymentRequest (product="ai_assistant").
    ai_assistant_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class PaymentRequestStatusEnum(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class PaymentRequest(Base):
    """
    A user's claim of having paid the ₹999/year UPI upgrade, manually
    reviewed by an admin (no payment gateway integration — see
    app/api/routes/billing.py and admin_billing.py).
    """
    __tablename__ = "payment_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    status: Mapped[PaymentRequestStatusEnum] = mapped_column(
        Enum(PaymentRequestStatusEnum, name="payment_request_status_enum"),
        nullable=False,
        default=PaymentRequestStatusEnum.pending,
    )
    # "subscription" (the base ₹999/yr upgrade) or "ai_assistant" (the
    # chat-widget add-on) — see admin_billing.py for how approval branches.
    product: Mapped[str] = mapped_column(String(30), nullable=False, server_default="subscription")
    # "upi" (manual claim, reviewed via screenshot/reference below) or
    # "razorpay" (auto-verified via signature — see app/services/razorpay_client.py).
    method: Mapped[str] = mapped_column(String(20), nullable=False, server_default="upi")
    amount_rupees: Mapped[int] = mapped_column(Integer, nullable=False, default=999)
    reference_note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    screenshot_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    razorpay_order_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    razorpay_payment_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    razorpay_signature: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reviewed_by_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])


class UpiSettings(Base):
    """
    Single-row admin-configured UPI payment target shown to users on the
    billing/upgrade page, plus toggles for which payment methods are
    offered (UPI manual-claim, Razorpay auto-verified).
    """
    __tablename__ = "upi_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    qr_image_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    upi_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    upi_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    razorpay_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    actor_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    meta: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AiAssistantConfig(Base):
    """
    One row per user: the owner's own on/off switch and knowledge-source
    choice for their public AI Assistant chat widget. Independent of plan
    entitlement (see Subscription.ai_assistant_enabled) — a user can be
    entitled but have the widget switched off, or vice versa was granted
    then revoked.
    """
    __tablename__ = "ai_assistant_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), unique=True, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    use_profile_data: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class AiAssistantQaPair(Base):
    """
    A user-authored question/answer pair fed into the chat widget's
    knowledge context. Up to settings.AI_ASSISTANT_MAX_QA_PAIRS per user,
    enforced in app/api/routes/ai_assistant.py (not at the DB level).
    """
    __tablename__ = "ai_assistant_qa_pairs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), index=True, nullable=False)
    question: Mapped[str] = mapped_column(String(150), nullable=False)
    answer: Mapped[str] = mapped_column(String(500), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class AiAssistantChatLog(Base):
    """
    One row per answered chat message, used only to enforce
    settings.AI_ASSISTANT_DAILY_MESSAGE_LIMIT per portfolio owner on the
    public chat endpoint (see app/api/routes/ai_assistant.py).
    """
    __tablename__ = "ai_assistant_chat_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Resume(Base):
    """
    AI Resume Builder: one row per resume document a user is building.
    `content` is a single JSONB blob (mirrors the house convention set by
    QuestionnaireResponse.answers — no normalized Experience/Project/Skill
    tables exist elsewhere in this app). Every leaf item in `content`
    carries its own "source" tag (mepage_import|ai_generated|user_edited)
    for provenance display and to drive non-destructive re-imports (see
    app/services/resume_profile_mapper.py). Distinct from
    UserProfile.resume_file_path/resume_text/resume_suggestions, which
    belong to the separate, pre-existing resume-upload-to-profile-prefill
    flow (app/api/routes/resume.py) and are not reused here.
    """
    __tablename__ = "resumes"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False, default="Untitled Resume")
    template_key: Mapped[str] = mapped_column(String(50), nullable=False, default="ats_professional")
    content: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    # "mepage_import" | "upload_import" | "scratch"
    source: Mapped[str] = mapped_column(String(30), nullable=False, default="scratch")
    target_role: Mapped[str | None] = mapped_column(String(200), nullable=True)
    ats_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ats_analysis: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    tailoring_job_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    tailoring_match_scores: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    tailoring_gap_analysis: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    last_profile_import_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    versions: Mapped[list["ResumeVersion"]] = relationship(
        "ResumeVersion", cascade="all, delete-orphan", order_by="ResumeVersion.created_at.desc()"
    )
    generations: Mapped[list["ResumeGeneration"]] = relationship(
        "ResumeGeneration", cascade="all, delete-orphan"
    )
    exports: Mapped[list["ResumeExport"]] = relationship("ResumeExport", cascade="all, delete-orphan")


class ResumeVersion(Base):
    """
    Whole-document snapshot of a Resume.content, taken before a
    destructive AI operation (generate/import-profile) or on manual save,
    so every change is undoable. Pruned to the last 20 rows per resume
    inline on insert (no cron infra exists in this app).
    """
    __tablename__ = "resume_versions"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    resume_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("resumes.id", ondelete="CASCADE"), index=True, nullable=False
    )
    content: Mapped[dict] = mapped_column(JSONB, nullable=False)
    # "pre_generate" | "pre_tailor" | "manual_save" | "pre_import"
    reason: Mapped[str] = mapped_column(String(30), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ResumeGeneration(Base):
    """
    Audit trail of AI calls made against a resume (never raw prompts or
    full conversations — summaries only). High-frequency improve-field
    calls are only logged here on failure.
    """
    __tablename__ = "resume_generations"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    resume_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("resumes.id", ondelete="CASCADE"), index=True, nullable=False
    )
    # "analysis" | "generation" | "critique" | "ats_analysis" | "tailor"
    stage: Mapped[str] = mapped_column(String(30), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(20), nullable=False, default="v1")
    input_summary: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    output_summary: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="success")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ResumeExport(Base):
    """Audit record + file copy of each PDF export of a Resume."""
    __tablename__ = "resume_exports"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    resume_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("resumes.id", ondelete="CASCADE"), index=True, nullable=False
    )
    template_key: Mapped[str] = mapped_column(String(50), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    page_size: Mapped[str] = mapped_column(String(10), nullable=False, default="A4")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
