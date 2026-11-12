"""baseline schema

Revision ID: f1a2b3c4d5e6
Revises:
Create Date: 2026-09-23

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "f1a2b3c4d5e6"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    role_enum = postgresql.ENUM(
        "super_admin", "admin", "template_manager", "content_manager", "support_user", "registered_user",
        name="role_enum",
    )
    onboarding_status_enum = postgresql.ENUM(
        "mobile_verified", "profile_pending", "audience_pending", "category_pending",
        "profession_pending", "specialisation_pending", "onboarding_complete",
        name="onboarding_status_enum",
    )
    # Not created explicitly here — create_table() below creates each
    # enum type as a side effect of the first column that uses it.

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("mobile_number_encrypted", sa.String(32), nullable=False),
        sa.Column("mobile_number_hash", sa.String(64), nullable=False),
        sa.Column("role", role_enum, nullable=False, server_default="registered_user"),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_unique_constraint("uq_users_mobile_number_hash", "users", ["mobile_number_hash"])
    op.create_index("ix_users_mobile_number_hash", "users", ["mobile_number_hash"])

    op.create_table(
        "audience_types",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("slug", sa.String(100), nullable=False, unique=True),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true()),
    )

    op.create_table(
        "portfolio_categories",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("audience_type_id", sa.Integer(), sa.ForeignKey("audience_types.id"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true()),
        sa.UniqueConstraint("audience_type_id", "slug", name="uq_audience_category_slug"),
    )

    op.create_table(
        "professions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("category_id", sa.Integer(), sa.ForeignKey("portfolio_categories.id"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true()),
        sa.UniqueConstraint("category_id", "slug", name="uq_category_profession_slug"),
    )

    op.create_table(
        "specialisations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("profession_id", sa.Integer(), sa.ForeignKey("professions.id"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true()),
        sa.UniqueConstraint("profession_id", "slug", name="uq_profession_specialisation_slug"),
    )

    op.create_table(
        "user_profiles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id"), nullable=False, unique=True),
        sa.Column("display_name", sa.String(150), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("country", sa.String(100), nullable=True),
        sa.Column("profile_image", sa.String(500), nullable=True),
        sa.Column("audience_type_id", sa.Integer(), sa.ForeignKey("audience_types.id"), nullable=True),
        sa.Column("category_id", sa.Integer(), sa.ForeignKey("portfolio_categories.id"), nullable=True),
        sa.Column("profession_id", sa.Integer(), sa.ForeignKey("professions.id"), nullable=True),
        sa.Column("specialisation_id", sa.Integer(), sa.ForeignKey("specialisations.id"), nullable=True),
        sa.Column("onboarding_status", onboarding_status_enum, nullable=False, server_default="profile_pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "otp_transactions",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("mobile_number_hash", sa.String(64), nullable=False),
        sa.Column("otp_hash", sa.String(255), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("provider_reference", sa.String(255), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_sent_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_otp_transactions_mobile_number_hash", "otp_transactions", ["mobile_number_hash"])

    op.create_table(
        "user_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("refresh_token_hash", sa.String(255), nullable=False),
        sa.Column("is_revoked", sa.Boolean(), server_default=sa.false()),
        sa.Column("replaced_by_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("user_sessions.id"), nullable=True),
        sa.Column("user_agent", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("actor_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("meta", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("user_sessions")
    op.drop_table("otp_transactions")
    op.drop_table("user_profiles")
    op.drop_table("specialisations")
    op.drop_table("professions")
    op.drop_table("portfolio_categories")
    op.drop_table("audience_types")
    op.drop_table("users")
    postgresql.ENUM(name="onboarding_status_enum").drop(op.get_bind())
    postgresql.ENUM(name="role_enum").drop(op.get_bind())
