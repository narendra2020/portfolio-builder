"""signup redesign: full name + password on users, pending signup fields on otp_transactions

Revision ID: j5e7a9c1d3f4
Revises: i4d6f8a0b2c3
Create Date: 2026-09-26

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "j5e7a9c1d3f4"
down_revision = "i4d6f8a0b2c3"
branch_labels = None
depends_on = None

# Bcrypt hash of a random placeholder password for any pre-existing user
# rows (currently only the seeded default admin) that predate password
# auth — they cannot log in with it and must be reset by an admin.
_PLACEHOLDER_PASSWORD_HASH = "$2b$12$K8O5b2m9F1uYQ3Zo6f2h1uYh9xJ8Qe6q5wq1c9m5o0e2v9d6r3n1u"


def upgrade() -> None:
    op.add_column("users", sa.Column("full_name", sa.String(150), nullable=True))
    op.add_column("users", sa.Column("password_hash", sa.String(255), nullable=True))

    op.execute(
        f"""
        UPDATE users
        SET full_name = COALESCE(
                (SELECT display_name FROM user_profiles WHERE user_profiles.user_id = users.id),
                'User'
            ),
            password_hash = '{_PLACEHOLDER_PASSWORD_HASH}'
        WHERE full_name IS NULL
        """
    )

    op.alter_column("users", "full_name", nullable=False)
    op.alter_column("users", "password_hash", nullable=False)

    op.add_column("otp_transactions", sa.Column("pending_full_name", sa.String(150), nullable=True))
    op.add_column("otp_transactions", sa.Column("pending_password_hash", sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column("otp_transactions", "pending_password_hash")
    op.drop_column("otp_transactions", "pending_full_name")
    op.drop_column("users", "password_hash")
    op.drop_column("users", "full_name")
