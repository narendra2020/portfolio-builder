"""resume upload + LLM pre-fill

Revision ID: f6a3c8d1b4e7
Revises: e8b1c4d7f9a3
Create Date: 2026-09-24

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "f6a3c8d1b4e7"
down_revision = "e8b1c4d7f9a3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ALTER TYPE ... ADD VALUE cannot run inside a transaction block in
    # Postgres. Commit the ambient migration transaction, run the DDL on
    # an AUTOCOMMIT connection, then resume — Alembic re-opens a fresh
    # transaction for whatever follows in this same upgrade().
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE onboarding_status_enum ADD VALUE IF NOT EXISTS 'resume_pending' BEFORE 'profile_pending'")

    op.add_column("user_profiles", sa.Column("resume_file_path", sa.String(500), nullable=True))
    op.add_column("user_profiles", sa.Column("resume_text", sa.Text(), nullable=True))
    op.add_column("user_profiles", sa.Column("resume_suggestions", postgresql.JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column("user_profiles", "resume_suggestions")
    op.drop_column("user_profiles", "resume_text")
    op.drop_column("user_profiles", "resume_file_path")
    # Postgres does not support removing an enum value; downgrade leaves
    # 'resume_pending' in place (harmless — no rows reference it once the
    # column changes above are reverted and the app no longer sets it).
