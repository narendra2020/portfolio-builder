"""student modern template: audience-scoped templates + student schema

Revision ID: m8b0d2f4a6c3
Revises: l7a9c1e3f5b2
Create Date: 2026-10-02

"""
import json

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "m8b0d2f4a6c3"
down_revision = "l7a9c1e3f5b2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "portfolio_templates",
        sa.Column("audience_type_id", sa.Integer(), sa.ForeignKey("audience_types.id"), nullable=True),
    )

    op.execute(
        """
        INSERT INTO portfolio_templates
            (name, slug, description, preview_image, template_file, audience_type_id, display_order, is_active)
        SELECT
            'Modern',
            'student-modern',
            'A vibrant, graduate-friendly one-page layout with a photo-led about panel, '
            'education journey, projects and skills — built for students and new grads.',
            '/api/template-assets/student-modern/thumbnail.svg',
            'student_modern_template.html.j2',
            audience_types.id,
            2,
            true
        FROM audience_types
        WHERE audience_types.slug = 'student'
        ON CONFLICT (slug) DO NOTHING
        """
    )

    conn = op.get_bind()
    student_id = conn.execute(
        sa.text("SELECT id FROM audience_types WHERE slug = 'student'")
    ).scalar()
    if student_id is not None:
        for section in _STUDENT_SECTIONS:
            exists = conn.execute(
                sa.text(
                    "SELECT 1 FROM questionnaire_schemas "
                    "WHERE audience_type_id = :aid AND section_key = :key"
                ),
                {"aid": student_id, "key": section["section_key"]},
            ).scalar()
            if not exists:
                conn.execute(
                    sa.text(
                        "INSERT INTO questionnaire_schemas "
                        "(audience_type_id, section_key, section_title, section_order, questions, is_active) "
                        "VALUES (:aid, :key, :title, :order, :questions, true)"
                    ),
                    {
                        "aid": student_id,
                        "key": section["section_key"],
                        "title": section["section_title"],
                        "order": section["section_order"],
                        "questions": json.dumps(section["questions"]),
                    },
                )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM questionnaire_schemas
        WHERE audience_type_id = (SELECT id FROM audience_types WHERE slug = 'student')
        """
    )
    op.execute("DELETE FROM portfolio_templates WHERE slug = 'student-modern'")
    op.drop_column("portfolio_templates", "audience_type_id")


_STUDENT_SECTIONS = [
    {
        "section_key": "hero",
        "section_title": "Hero",
        "section_order": 1,
        "questions": [
            {"key": "eyebrow_text", "label": "Eyebrow text", "type": "text",
             "placeholder": "e.g. Open to internships & grad roles"},
            {"key": "headline", "label": "Headline", "type": "text", "required": True,
             "placeholder": "e.g. Learning by building"},
            {"key": "headline_highlight", "label": "Headline (emphasized phrase)", "type": "text",
             "placeholder": "e.g. real projects."},
            {"key": "lead", "label": "Lead paragraph", "type": "textarea", "required": True},
            {"key": "primary_cta_label", "label": "Primary button label", "type": "text",
             "placeholder": "e.g. View my projects"},
            {"key": "primary_cta_target", "label": "Primary button target (anchor)", "type": "text",
             "placeholder": "e.g. #work"},
            {"key": "secondary_cta_label", "label": "Secondary button label", "type": "text",
             "placeholder": "e.g. Get in touch"},
            {"key": "secondary_cta_target", "label": "Secondary button target (anchor)", "type": "text",
             "placeholder": "e.g. #contact"},
            {"key": "hero_image_url", "label": "Hero image", "type": "image", "required": False},
            {"key": "quick_facts", "label": "Quick facts", "type": "repeater", "item_label": "fact",
             "fields": [
                 {"key": "value", "label": "Value", "type": "text", "required": True,
                  "placeholder": "e.g. 3"},
                 {"key": "label", "label": "Label", "type": "text", "required": True,
                  "placeholder": "e.g. Hackathons"},
             ]},
        ],
    },
    {
        "section_key": "about",
        "section_title": "About",
        "section_order": 2,
        "questions": [
            {"key": "kicker", "label": "Kicker", "type": "text", "placeholder": "e.g. 01 / About"},
            {"key": "heading_lead", "label": "Heading", "type": "text"},
            {"key": "heading_highlight", "label": "Heading (emphasized phrase)", "type": "text"},
            {"key": "intro_large", "label": "Intro paragraph (large)", "type": "textarea", "required": True},
            {"key": "body", "label": "Body paragraph", "type": "textarea"},
            {"key": "about_photo", "label": "About photo", "type": "image", "required": False},
            {"key": "info_items", "label": "Personal info", "type": "repeater", "item_label": "item",
             "fields": [
                 {"key": "label", "label": "Label", "type": "text", "required": True,
                  "placeholder": "e.g. Studying"},
                 {"key": "value", "label": "Value", "type": "text", "required": True},
             ]},
        ],
    },
    {
        "section_key": "journey",
        "section_title": "Journey",
        "section_order": 3,
        "questions": [
            {"key": "kicker", "label": "Kicker", "type": "text", "placeholder": "e.g. 02 / Journey"},
            {"key": "heading", "label": "Heading", "type": "text", "placeholder": "e.g. Education & journey"},
            {"key": "intro", "label": "Intro paragraph", "type": "textarea"},
            {"key": "entries", "label": "Timeline entries", "type": "repeater", "item_label": "entry",
             "fields": [
                 {"key": "date_range", "label": "Date range", "type": "text", "required": True,
                  "placeholder": "e.g. 2023 — Present"},
                 {"key": "category_label", "label": "Category label", "type": "text",
                  "placeholder": "e.g. Education"},
                 {"key": "title", "label": "Title", "type": "text", "required": True},
                 {"key": "org_location", "label": "Organisation / location", "type": "text"},
                 {"key": "description", "label": "Description", "type": "textarea"},
                 {"key": "tags", "label": "Tags (comma-separated)", "type": "text",
                  "placeholder": "e.g. Coursework, Research, Clubs"},
             ]},
        ],
    },
    {
        "section_key": "work",
        "section_title": "Work",
        "section_order": 4,
        "questions": [
            {"key": "kicker", "label": "Kicker", "type": "text", "placeholder": "e.g. 03 / Work"},
            {"key": "heading", "label": "Heading", "type": "text", "placeholder": "e.g. Projects"},
            {"key": "intro", "label": "Intro paragraph", "type": "textarea"},
            {"key": "projects", "label": "Projects", "type": "repeater", "item_label": "project",
             "fields": [
                 {"key": "type_label", "label": "Project type label", "type": "text",
                  "placeholder": "e.g. Academic project"},
                 {"key": "title", "label": "Title", "type": "text", "required": True},
                 {"key": "description", "label": "Description", "type": "textarea"},
                 {"key": "image_url", "label": "Project image", "type": "image", "required": False},
                 {"key": "tags", "label": "Tags (comma-separated)", "type": "text"},
                 {"key": "link_label", "label": "Link label", "type": "text",
                  "placeholder": "e.g. View on GitHub"},
                 {"key": "link_url", "label": "Link URL", "type": "text", "required": False},
                 {"key": "featured", "label": "Featured project?", "type": "boolean"},
             ]},
        ],
    },
    {
        "section_key": "skills",
        "section_title": "Skills",
        "section_order": 5,
        "questions": [
            {"key": "kicker", "label": "Kicker", "type": "text", "placeholder": "e.g. 04 / Skills"},
            {"key": "heading_lead", "label": "Heading", "type": "text", "placeholder": "e.g. Core"},
            {"key": "heading_highlight", "label": "Heading (emphasized phrase)", "type": "text",
             "placeholder": "e.g. skills"},
            {"key": "intro", "label": "Intro paragraph", "type": "textarea"},
            {"key": "groups", "label": "Skill groups", "type": "repeater", "item_label": "group",
             "fields": [
                 {"key": "icon", "label": "Icon (single glyph/emoji)", "type": "text"},
                 {"key": "title", "label": "Title", "type": "text", "required": True},
                 {"key": "description", "label": "Description", "type": "textarea"},
                 {"key": "skills", "label": "Skills (comma-separated)", "type": "text"},
             ]},
        ],
    },
    {
        "section_key": "contact",
        "section_title": "Contact",
        "section_order": 6,
        "questions": [
            {"key": "kicker", "label": "Kicker", "type": "text", "placeholder": "e.g. 05 / Contact"},
            {"key": "heading", "label": "Heading", "type": "text", "placeholder": "e.g. Let's connect"},
            {"key": "description", "label": "Description", "type": "textarea"},
            {"key": "email", "label": "Contact email", "type": "email", "required": True},
            {"key": "socials", "label": "Social links", "type": "repeater", "item_label": "link",
             "fields": [
                 {"key": "label", "label": "Label", "type": "text", "required": True,
                  "placeholder": "e.g. LinkedIn"},
                 {"key": "url", "label": "URL", "type": "text", "required": True},
             ]},
        ],
    },
]
