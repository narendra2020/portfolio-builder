"""publishing pipeline

Revision ID: d5f8b3c1a7e2
Revises: c4e7a9d2f5b1
Create Date: 2026-09-23

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "d5f8b3c1a7e2"
down_revision = "c4e7a9d2f5b1"
branch_labels = None
depends_on = None

published_portfolio_status_enum = postgresql.ENUM(
    "draft", "published", name="published_portfolio_status_enum"
)


def upgrade() -> None:
    published_portfolio_status_enum.create(op.get_bind(), checkfirst=True)
    status_column_type = postgresql.ENUM(
        "draft", "published", name="published_portfolio_status_enum", create_type=False
    )
    op.create_table(
        "published_portfolios",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id"), unique=True, nullable=False),
        sa.Column("slug", sa.String(63), unique=True, nullable=False),
        sa.Column(
            "status",
            status_column_type,
            nullable=False,
            server_default="draft",
        ),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("published_portfolios")
    published_portfolio_status_enum.drop(op.get_bind())
