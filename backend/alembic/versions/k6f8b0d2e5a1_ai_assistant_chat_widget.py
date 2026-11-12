"""ai assistant chat widget: config, qa pairs, chat log, entitlement flag

Revision ID: k6f8b0d2e5a1
Revises: f5d445408657
Create Date: 2026-10-01 09:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'k6f8b0d2e5a1'
down_revision = 'f5d445408657'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'subscriptions',
        sa.Column('ai_assistant_enabled', sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        'payment_requests',
        sa.Column('product', sa.String(length=30), nullable=False, server_default='subscription'),
    )

    op.create_table('ai_assistant_configs',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('enabled', sa.Boolean(), nullable=False, server_default=sa.false()),
    sa.Column('use_profile_data', sa.Boolean(), nullable=False, server_default=sa.true()),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id')
    )
    op.create_table('ai_assistant_qa_pairs',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('question', sa.String(length=150), nullable=False),
    sa.Column('answer', sa.String(length=500), nullable=False),
    sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ai_assistant_qa_pairs_user_id'), 'ai_assistant_qa_pairs', ['user_id'])

    op.create_table('ai_assistant_chat_logs',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ai_assistant_chat_logs_user_id'), 'ai_assistant_chat_logs', ['user_id'])


def downgrade() -> None:
    op.drop_index(op.f('ix_ai_assistant_chat_logs_user_id'), table_name='ai_assistant_chat_logs')
    op.drop_table('ai_assistant_chat_logs')
    op.drop_index(op.f('ix_ai_assistant_qa_pairs_user_id'), table_name='ai_assistant_qa_pairs')
    op.drop_table('ai_assistant_qa_pairs')
    op.drop_table('ai_assistant_configs')
    op.drop_column('payment_requests', 'product')
    op.drop_column('subscriptions', 'ai_assistant_enabled')
