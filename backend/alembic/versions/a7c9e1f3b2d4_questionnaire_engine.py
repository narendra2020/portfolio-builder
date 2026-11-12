"""questionnaire engine

Revision ID: a7c9e1f3b2d4
Revises: f1a2b3c4d5e6
Create Date: 2026-09-23

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "a7c9e1f3b2d4"
down_revision = "f1a2b3c4d5e6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "questionnaire_schemas",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("profession_id", sa.Integer(), sa.ForeignKey("professions.id"), nullable=False),
        sa.Column("section_key", sa.String(100), nullable=False),
        sa.Column("section_title", sa.String(200), nullable=False),
        sa.Column("section_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("questions", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("profession_id", "section_key", name="uq_profession_section"),
    )

    op.create_table(
        "questionnaire_responses",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("section_key", sa.String(100), nullable=False),
        sa.Column("answers", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "section_key", name="uq_user_section"),
    )


def downgrade() -> None:
    op.drop_table("questionnaire_responses")
    op.drop_table("questionnaire_schemas")
