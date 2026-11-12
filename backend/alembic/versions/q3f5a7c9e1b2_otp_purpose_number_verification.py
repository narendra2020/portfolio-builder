"""otp_transactions: purpose + requesting user, for logged-in number verification

Revision ID: q3f5a7c9e1b2
Revises: p2e4f6a8c0d5
Create Date: 2026-10-25

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "q3f5a7c9e1b2"
down_revision = "p2e4f6a8c0d5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("otp_transactions", sa.Column("purpose", sa.String(30), nullable=False, server_default="auth"))
    op.add_column(
        "otp_transactions",
        sa.Column("requested_by_user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id"), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("otp_transactions", "requested_by_user_id")
    op.drop_column("otp_transactions", "purpose")
