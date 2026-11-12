"""audience-scoped questionnaire schemas

Revision ID: e8b1c4d7f9a3
Revises: d5f8b3c1a7e2
Create Date: 2026-09-24

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "e8b1c4d7f9a3"
down_revision = "d5f8b3c1a7e2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("questionnaire_schemas", "profession_id", nullable=True)
    op.add_column(
        "questionnaire_schemas",
        sa.Column("audience_type_id", sa.Integer(), sa.ForeignKey("audience_types.id"), nullable=True),
    )
    op.drop_constraint("uq_profession_section", "questionnaire_schemas", type_="unique")
    op.create_check_constraint(
        "ck_schema_scope_xor",
        "questionnaire_schemas",
        "(profession_id IS NOT NULL) != (audience_type_id IS NOT NULL)",
    )
    op.create_index(
        "uq_profession_section_partial",
        "questionnaire_schemas",
        ["profession_id", "section_key"],
        unique=True,
        postgresql_where=sa.text("profession_id IS NOT NULL"),
    )
    op.create_index(
        "uq_audience_section_partial",
        "questionnaire_schemas",
        ["audience_type_id", "section_key"],
        unique=True,
        postgresql_where=sa.text("audience_type_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_audience_section_partial", table_name="questionnaire_schemas")
    op.drop_index("uq_profession_section_partial", table_name="questionnaire_schemas")
    op.drop_constraint("ck_schema_scope_xor", "questionnaire_schemas", type_="check")
    op.drop_column("questionnaire_schemas", "audience_type_id")
    op.alter_column("questionnaire_schemas", "profession_id", nullable=False)
    op.create_unique_constraint(
        "uq_profession_section", "questionnaire_schemas", ["profession_id", "section_key"]
    )
