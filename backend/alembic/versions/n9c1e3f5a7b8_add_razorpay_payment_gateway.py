"""add razorpay payment gateway + payment method toggles

Revision ID: n9c1e3f5a7b8
Revises: m8b0d2f4a6c3
Create Date: 2026-10-08 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "n9c1e3f5a7b8"
down_revision = "m8b0d2f4a6c3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    requests_columns = {c["name"] for c in inspector.get_columns("payment_requests")}
    if "method" not in requests_columns:
        op.add_column("payment_requests", sa.Column("method", sa.String(length=20), server_default="upi", nullable=False))
    if "razorpay_order_id" not in requests_columns:
        op.add_column("payment_requests", sa.Column("razorpay_order_id", sa.String(length=100), nullable=True))
        op.create_index("ix_payment_requests_razorpay_order_id", "payment_requests", ["razorpay_order_id"])
    if "razorpay_payment_id" not in requests_columns:
        op.add_column("payment_requests", sa.Column("razorpay_payment_id", sa.String(length=100), nullable=True))
    if "razorpay_signature" not in requests_columns:
        op.add_column("payment_requests", sa.Column("razorpay_signature", sa.String(length=255), nullable=True))

    upi_settings_columns = {c["name"] for c in inspector.get_columns("upi_settings")}
    if "upi_enabled" not in upi_settings_columns:
        op.add_column("upi_settings", sa.Column("upi_enabled", sa.Boolean(), server_default="true", nullable=False))
    if "razorpay_enabled" not in upi_settings_columns:
        op.add_column("upi_settings", sa.Column("razorpay_enabled", sa.Boolean(), server_default="false", nullable=False))


def downgrade() -> None:
    op.drop_column("upi_settings", "razorpay_enabled")
    op.drop_column("upi_settings", "upi_enabled")
    op.drop_index("ix_payment_requests_razorpay_order_id", table_name="payment_requests")
    op.drop_column("payment_requests", "razorpay_signature")
    op.drop_column("payment_requests", "razorpay_payment_id")
    op.drop_column("payment_requests", "razorpay_order_id")
    op.drop_column("payment_requests", "method")
