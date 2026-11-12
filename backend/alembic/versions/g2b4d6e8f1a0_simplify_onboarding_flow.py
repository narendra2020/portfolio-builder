"""simplify onboarding flow (remove taxonomy pickers, Universal-only template)

Revision ID: g2b4d6e8f1a0
Revises: f6a3c8d1b4e7
Create Date: 2026-09-24

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "g2b4d6e8f1a0"
down_revision = "f6a3c8d1b4e7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ALTER TYPE ... ADD VALUE cannot run inside a transaction block in
    # Postgres — same autocommit_block() pattern as f6a3c8d1b4e7.
    with op.get_context().autocommit_block():
        op.execute(
            "ALTER TYPE onboarding_status_enum ADD VALUE IF NOT EXISTS 'template_pending' BEFORE 'onboarding_complete'"
        )

    # Pre-production data fixup: force any in-flight rows sitting in a
    # now-removed taxonomy-picker state onto the new linear path. Postgres
    # cannot remove enum values, so 'audience_pending'/'category_pending'/
    # 'profession_pending'/'specialisation_pending' continue to physically
    # exist in the enum type but the app never sets them again.
    op.execute(
        """
        UPDATE user_profiles
        SET onboarding_status = 'template_pending'
        WHERE onboarding_status IN
            ('audience_pending', 'category_pending', 'profession_pending', 'specialisation_pending')
        """
    )

    # Deactivate the 5 non-Universal templates and rename Universal Modern -> Universal.
    op.execute(
        "UPDATE portfolio_templates SET is_active = false "
        "WHERE slug IN ('minimal', 'bold', 'classic', 'creative', 'academic')"
    )
    op.execute("UPDATE portfolio_templates SET name = 'Universal' WHERE slug = 'universal-modern'")

    # Reassign any UserProfile pointed at a deactivated template to Universal.
    op.execute(
        """
        UPDATE user_profiles
        SET template_id = (SELECT id FROM portfolio_templates WHERE slug = 'universal-modern')
        WHERE template_id IN (
            SELECT id FROM portfolio_templates
            WHERE slug IN ('minimal', 'bold', 'classic', 'creative', 'academic')
        )
        """
    )


def downgrade() -> None:
    op.execute(
        "UPDATE portfolio_templates SET is_active = true "
        "WHERE slug IN ('minimal', 'bold', 'classic', 'creative', 'academic')"
    )
    op.execute("UPDATE portfolio_templates SET name = 'Universal Modern' WHERE slug = 'universal-modern'")
    # Postgres does not support removing an enum value; downgrade leaves
    # 'template_pending' in place (harmless — no rows reference it once
    # app code stops setting it), consistent with f6a3c8d1b4e7's precedent.
