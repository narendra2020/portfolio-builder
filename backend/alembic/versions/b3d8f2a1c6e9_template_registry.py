"""template registry

Revision ID: b3d8f2a1c6e9
Revises: a7c9e1f3b2d4
Create Date: 2026-09-23

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "b3d8f2a1c6e9"
down_revision = "a7c9e1f3b2d4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "portfolio_templates",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("slug", sa.String(100), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("preview_image", sa.String(255), nullable=True),
        sa.Column("template_file", sa.String(255), nullable=False, server_default="default_template.html.j2"),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.add_column(
        "user_profiles",
        sa.Column("template_id", sa.Integer(), sa.ForeignKey("portfolio_templates.id"), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("user_profiles", "template_id")
    op.drop_table("portfolio_templates")
