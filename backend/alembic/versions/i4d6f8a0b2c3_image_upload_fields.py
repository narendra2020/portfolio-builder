"""switch hero/project image fields from text-url to image upload type

Revision ID: i4d6f8a0b2c3
Revises: h3c5e7f9a1b2
Create Date: 2026-09-24

"""
import json

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "i4d6f8a0b2c3"
down_revision = "h3c5e7f9a1b2"
branch_labels = None
depends_on = None

_IMAGE_KEYS = {"hero_image_url", "image_url"}


def _flip(questions, from_type: str, to_type: str):
    changed = False
    for question in questions:
        if question.get("key") in _IMAGE_KEYS and question.get("type") == from_type:
            question["type"] = to_type
            changed = True
        if question.get("type") == "repeater":
            for field in question.get("fields", []):
                if field.get("key") in _IMAGE_KEYS and field.get("type") == from_type:
                    field["type"] = to_type
                    changed = True
    return changed


def _migrate(from_type: str, to_type: str) -> None:
    conn = op.get_bind()
    rows = conn.execute(
        sa.text("SELECT id, questions FROM questionnaire_schemas")
    ).fetchall()
    for row in rows:
        questions = row.questions if isinstance(row.questions, list) else json.loads(row.questions)
        if _flip(questions, from_type, to_type):
            conn.execute(
                sa.text("UPDATE questionnaire_schemas SET questions = :q WHERE id = :id"),
                {"q": json.dumps(questions), "id": row.id},
            )


def upgrade() -> None:
    _migrate("text", "image")


def downgrade() -> None:
    _migrate("image", "text")
