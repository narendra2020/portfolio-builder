"""subscriptions, payment requests, upi settings, slug lock

Revision ID: f5d445408657
Revises: j5e7a9c1d3f4
Create Date: 2026-10-01 08:52:24.266423

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'f5d445408657'
down_revision = 'j5e7a9c1d3f4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('upi_settings',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('qr_image_path', sa.String(length=500), nullable=True),
    sa.Column('upi_id', sa.String(length=100), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('payment_requests',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('status', sa.Enum('pending', 'approved', 'rejected', name='payment_request_status_enum'), nullable=False),
    sa.Column('amount_rupees', sa.Integer(), nullable=False),
    sa.Column('reference_note', sa.String(length=255), nullable=True),
    sa.Column('screenshot_path', sa.String(length=500), nullable=True),
    sa.Column('reviewed_by_id', sa.UUID(as_uuid=False), nullable=True),
    sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['reviewed_by_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('subscriptions',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('status', sa.Enum('trial', 'active', 'expired', name='subscription_status_enum'), nullable=False),
    sa.Column('trial_ends_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('paid_until', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id')
    )
    op.alter_column('published_portfolios', 'slug',
               existing_type=sa.VARCHAR(length=63),
               nullable=True)

    # Backfill a trial subscription for every pre-existing user, counting
    # their 30-day trial from their original signup date.
    op.execute(
        "INSERT INTO subscriptions (user_id, status, trial_ends_at) "
        "SELECT id, 'trial', created_at + INTERVAL '30 days' FROM users"
    )


def downgrade() -> None:
    op.alter_column('published_portfolios', 'slug',
               existing_type=sa.VARCHAR(length=63),
               nullable=False)
    op.drop_table('subscriptions')
    op.drop_table('payment_requests')
    op.drop_table('upi_settings')
