"""layout editor

Revision ID: c4e7a9d2f5b1
Revises: b3d8f2a1c6e9
Create Date: 2026-09-23

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "c4e7a9d2f5b1"
down_revision = "b3d8f2a1c6e9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "layout_block_sets",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id"), unique=True, nullable=False),
        sa.Column("blocks", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("layout_block_sets")
