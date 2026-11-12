"""deactivate legacy portfolio-pro template

Revision ID: h3c5e7f9a1b2
Revises: g2b4d6e8f1a0
Create Date: 2026-09-24

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "h3c5e7f9a1b2"
down_revision = "g2b4d6e8f1a0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # A pre-existing 'portfolio-pro' template row (never part of the seed
    # list) was left is_active=true with display_order=0, so it sorted
    # ahead of Universal in GET /api/templates and got silently picked by
    # the frontend's data[0] selection — bypassing Universal entirely and
    # rendering the bare-bones default_template.html.j2 fallback.
    op.execute("UPDATE portfolio_templates SET is_active = false WHERE slug = 'portfolio-pro'")

    op.execute(
        """
        UPDATE user_profiles
        SET template_id = (SELECT id FROM portfolio_templates WHERE slug = 'universal-modern')
        WHERE template_id IN (SELECT id FROM portfolio_templates WHERE slug = 'portfolio-pro')
        """
    )


def downgrade() -> None:
    op.execute("UPDATE portfolio_templates SET is_active = true WHERE slug = 'portfolio-pro'")
