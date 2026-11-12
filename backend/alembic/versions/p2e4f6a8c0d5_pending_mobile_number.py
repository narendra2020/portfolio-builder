"""otp_transactions: capture the real mobile number at signup time

Revision ID: p2e4f6a8c0d5
Revises: o1d3f5a7b9c4
Create Date: 2026-10-10

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "p2e4f6a8c0d5"
down_revision = "o1d3f5a7b9c4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("otp_transactions", sa.Column("pending_mobile_number", sa.String(32), nullable=True))


def downgrade() -> None:
    op.drop_column("otp_transactions", "pending_mobile_number")
