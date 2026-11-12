"""add AI resume builder tables (resumes, resume_versions, resume_generations, resume_exports)

Revision ID: o1d3f5a7b9c4
Revises: n9c1e3f5a7b8
Create Date: 2026-10-08 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "o1d3f5a7b9c4"
down_revision = "n9c1e3f5a7b8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "resumes",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False, server_default="Untitled Resume"),
        sa.Column("template_key", sa.String(length=50), nullable=False, server_default="ats_professional"),
        sa.Column("content", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("source", sa.String(length=30), nullable=False, server_default="scratch"),
        sa.Column("target_role", sa.String(length=200), nullable=True),
        sa.Column("ats_score", sa.Integer(), nullable=True),
        sa.Column("ats_analysis", postgresql.JSONB(), nullable=True),
        sa.Column("tailoring_job_description", sa.Text(), nullable=True),
        sa.Column("tailoring_match_scores", postgresql.JSONB(), nullable=True),
        sa.Column("tailoring_gap_analysis", postgresql.JSONB(), nullable=True),
        sa.Column("last_profile_import_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_resumes_user_id", "resumes", ["user_id"])

    op.create_table(
        "resume_versions",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("resume_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("content", postgresql.JSONB(), nullable=False),
        sa.Column("reason", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_resume_versions_resume_id", "resume_versions", ["resume_id"])

    op.create_table(
        "resume_generations",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("resume_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("stage", sa.String(length=30), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=False),
        sa.Column("prompt_version", sa.String(length=20), nullable=False, server_default="v1"),
        sa.Column("input_summary", postgresql.JSONB(), nullable=True),
        sa.Column("output_summary", postgresql.JSONB(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="success"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_resume_generations_resume_id", "resume_generations", ["resume_id"])

    op.create_table(
        "resume_exports",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("resume_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("template_key", sa.String(length=50), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("page_size", sa.String(length=10), nullable=False, server_default="A4"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_resume_exports_resume_id", "resume_exports", ["resume_id"])


def downgrade() -> None:
    op.drop_index("ix_resume_exports_resume_id", table_name="resume_exports")
    op.drop_table("resume_exports")
    op.drop_index("ix_resume_generations_resume_id", table_name="resume_generations")
    op.drop_table("resume_generations")
    op.drop_index("ix_resume_versions_resume_id", table_name="resume_versions")
    op.drop_table("resume_versions")
    op.drop_index("ix_resumes_user_id", table_name="resumes")
    op.drop_table("resumes")
