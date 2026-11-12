"""audience selection step: new onboarding status + 3 new audience types

Revision ID: l7a9c1e3f5b2
Revises: k6f8b0d2e5a1
Create Date: 2026-10-01

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "l7a9c1e3f5b2"
down_revision = "k6f8b0d2e5a1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE onboarding_status_enum ADD VALUE IF NOT EXISTS 'audience_pending'")

    op.execute(
        """
        INSERT INTO audience_types (name, slug, display_order, is_active)
        VALUES
            ('Freelancer', 'freelancer', 3, true),
            ('Entrepreneur', 'entrepreneur', 4, true),
            ('Creator', 'creator', 5, true)
        ON CONFLICT (slug) DO NOTHING
        """
    )


def downgrade() -> None:
    # Postgres has no ALTER TYPE ... DROP VALUE, so the enum addition is
    # one-directional. Only the data insert is reversible.
    op.execute("DELETE FROM audience_types WHERE slug IN ('freelancer', 'entrepreneur', 'creator')")
