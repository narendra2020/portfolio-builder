"""
Static seed data for the audience/category/profession/specialisation
taxonomy.
"""

AUDIENCE_TYPES = [
    {"name": "Professional", "slug": "professional", "display_order": 1},
    {"name": "Student", "slug": "student", "display_order": 2},
    {"name": "Freelancer", "slug": "freelancer", "display_order": 3},
    {"name": "Entrepreneur", "slug": "entrepreneur", "display_order": 4},
    {"name": "Creator", "slug": "creator", "display_order": 5},
]

# Each category nests under its audience_type slug; each profession
# nests under its category slug.
CATEGORIES = [
    {"audience_slug": "professional", "name": "Technology", "slug": "technology", "display_order": 1},
    {"audience_slug": "professional", "name": "Healthcare", "slug": "healthcare", "display_order": 2},
    {"audience_slug": "professional", "name": "Engineering", "slug": "engineering", "display_order": 3},
    {"audience_slug": "student", "name": "Engineering", "slug": "engineering-student", "display_order": 1},
]

PROFESSIONS = [
    {
        "category_slug": "technology",
        "name": "Software Engineer",
        "slug": "software-engineer",
        "display_order": 1,
        "specialisations": ["Frontend", "Backend", "Full Stack", "DevOps"],
    },
    {
        "category_slug": "healthcare",
        "name": "Doctor",
        "slug": "doctor",
        "display_order": 1,
        "specialisations": ["General Physician", "Surgeon", "Pediatrician"],
    },
    {
        "category_slug": "engineering",
        "name": "Mechanical Engineer",
        "slug": "mechanical-engineer",
        "display_order": 1,
        "specialisations": ["Design", "Manufacturing", "Maintenance"],
    },
    {
        "category_slug": "engineering-student",
        "name": "Engineering Student",
        "slug": "engineering-student",
        "display_order": 1,
        "specialisations": ["Computer Science", "Mechanical", "Civil", "Electrical"],
    },
]

# Starter template catalog. Universal has no `audience_slug` (global —
# available to every audience); Modern sets `audience_slug` to restrict
# it to that audience only (resolved to `audience_type_id` by
# seed.py::seed_templates). Universal's preview_image is left null so
# the frontend renders a generated CSS mock-up thumbnail; Modern ships a
# real SVG thumbnail served from the template-assets static mount.
PORTFOLIO_TEMPLATES = [
    {"name": "Universal", "slug": "universal-modern", "display_order": 1,
     "template_file": "universal_modern_template.html.j2",
     "description": "Full-featured one-page template with hero, journey, work and skills "
                     "sections — works for professionals and students alike."},
    {"name": "Editorial Executive", "slug": "professional-editorial-executive", "display_order": 1,
     "template_file": "professional_editorial_executive_template.html.j2",
     "audience_slug": "professional",
     "preview_image": "/api/template-assets/editorial-executive/thumbnail.svg",
     "description": "Ivory editorial layout with serif typography, split hero and timeline journey for established professionals."},
    {"name": "Midnight Systems", "slug": "professional-midnight-systems", "display_order": 2,
     "template_file": "professional_midnight_systems_template.html.j2",
     "audience_slug": "professional",
     "preview_image": "/api/template-assets/midnight-systems/thumbnail.svg",
     "description": "Dark technical interface inspired by system dashboards with signal panels and mission-focused copy blocks."},
    {"name": "Cobalt Swiss", "slug": "professional-cobalt-swiss", "display_order": 3,
     "template_file": "professional_cobalt_swiss_template.html.j2",
     "audience_slug": "professional",
     "preview_image": "/api/template-assets/cobalt-swiss/thumbnail.svg",
     "description": "Bold numbered grid with cobalt palette and Swiss-inspired typographic rhythm for consulting portfolios."},
    {"name": "Sage Studio", "slug": "professional-sage-studio", "display_order": 4,
     "template_file": "professional_sage_studio_template.html.j2",
     "audience_slug": "professional",
     "preview_image": "/api/template-assets/sage-studio/thumbnail.svg",
     "description": "Organic sage tones, rounded cards and practice-area hierarchy suited to advisory and studio-led profiles."},
    {"name": "Aurora Personal OS", "slug": "professional-aurora-personal-os", "display_order": 5,
     "template_file": "professional_aurora_personal_os_template.html.j2",
     "audience_slug": "professional",
     "preview_image": "/api/template-assets/aurora-personal-os/thumbnail.svg",
     "description": "Persistent sidebar and layered panels evoking a personal operating system for product and systems leaders."},
    {"name": "Modern", "slug": "student-modern", "display_order": 2,
     "template_file": "student_modern_template.html.j2",
     "audience_slug": "student",
     "preview_image": "/api/template-assets/student-modern/thumbnail.svg",
     "description": "A vibrant, graduate-friendly one-page layout with a photo-led about panel, "
                     "education journey, projects and skills — built for students and new grads."},
    # Student showcase family — five visual directions sharing one Jinja
    # base (_student_showcase_base.html.j2) and one script. Every one has
    # a Classic / Dark mode toggle; Midnight defaults to dark.
    {"name": "Orbit", "slug": "student-orbit", "display_order": 3,
     "template_file": "student_showcase_orbit_template.html.j2",
     "audience_slug": "student",
     "preview_image": "/api/template-assets/student-orbit/thumbnail.svg",
     "description": "Lavender bento-inspired layout with a tilted identity panel and offset project cards."},
    {"name": "Midnight", "slug": "student-midnight", "display_order": 4,
     "template_file": "student_showcase_midnight_template.html.j2",
     "audience_slug": "student",
     "preview_image": "/api/template-assets/student-midnight/thumbnail.svg",
     "description": "Dark developer-terminal styling with lime accents and monospace details."},
    {"name": "Paper", "slug": "student-paper", "display_order": 5,
     "template_file": "student_showcase_paper_template.html.j2",
     "audience_slug": "student",
     "preview_image": "/api/template-assets/student-paper/thumbnail.svg",
     "description": "Serif editorial typography, an arch-shaped identity panel and alternating project rows."},
    {"name": "Playground", "slug": "student-playground", "display_order": 6,
     "template_file": "student_showcase_playground_template.html.j2",
     "audience_slug": "student",
     "preview_image": "/api/template-assets/student-playground/thumbnail.svg",
     "description": "Playful cobalt and yellow styling with hard shadows and tilted cards."},
    {"name": "Fieldwork", "slug": "student-fieldwork", "display_order": 7,
     "template_file": "student_showcase_fieldwork_template.html.j2",
     "audience_slug": "student",
     "preview_image": "/api/template-assets/student-fieldwork/thumbnail.svg",
     "description": "Forest-green academic direction with a wide research banner and education timeline."},
]

# Audience-level questionnaire pair (Professional / Student), scoped by
# `audience_type_id` rather than `profession_id` — applies universally
# across every profession under that audience. Section shape mirrors the
# "Universal Modern" template's sections 1:1 (hero, about, journey, work,
# skills, contact) so the same Jinja template can render either audience's
# answers. Both audiences share the exact same field keys/types — only
# copy/placeholder tone differs — which is what makes one shared template
# possible.
AUDIENCE_QUESTIONNAIRE_SECTIONS = {
    "professional": [
        {
            "section_key": "hero",
            "section_title": "Hero",
            "section_order": 1,
            "questions": [
                {"key": "eyebrow_text", "label": "Eyebrow text", "type": "text",
                 "placeholder": "e.g. Available for opportunities"},
                {"key": "headline", "label": "Headline", "type": "text", "required": True,
                 "placeholder": "e.g. Turning curiosity into"},
                {"key": "headline_highlight", "label": "Headline (emphasized phrase)", "type": "text",
                 "placeholder": "e.g. meaningful impact."},
                {"key": "lead", "label": "Lead paragraph", "type": "textarea", "required": True},
                {"key": "primary_cta_label", "label": "Primary button label", "type": "text",
                 "placeholder": "e.g. View my work"},
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
                      "placeholder": "e.g. 12+"},
                     {"key": "label", "label": "Label", "type": "text", "required": True,
                      "placeholder": "e.g. Projects"},
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
                {"key": "info_items", "label": "Personal info", "type": "repeater", "item_label": "item",
                 "fields": [
                     {"key": "label", "label": "Label", "type": "text", "required": True,
                      "placeholder": "e.g. Based in"},
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
                {"key": "heading", "label": "Heading", "type": "text", "placeholder": "e.g. Career journey"},
                {"key": "intro", "label": "Intro paragraph", "type": "textarea"},
                {"key": "entries", "label": "Timeline entries", "type": "repeater", "item_label": "entry",
                 "fields": [
                     {"key": "date_range", "label": "Date range", "type": "text", "required": True,
                      "placeholder": "e.g. 2025 — Present"},
                     {"key": "category_label", "label": "Category label", "type": "text",
                      "placeholder": "e.g. Professional experience"},
                     {"key": "title", "label": "Title", "type": "text", "required": True},
                     {"key": "org_location", "label": "Organisation / location", "type": "text"},
                     {"key": "description", "label": "Description", "type": "textarea"},
                     {"key": "tags", "label": "Tags (comma-separated)", "type": "text",
                      "placeholder": "e.g. Leadership, Research, Delivery"},
                 ]},
            ],
        },
        {
            "section_key": "work",
            "section_title": "Work",
            "section_order": 4,
            "questions": [
                {"key": "kicker", "label": "Kicker", "type": "text", "placeholder": "e.g. 03 / Work"},
                {"key": "heading", "label": "Heading", "type": "text", "placeholder": "e.g. Selected work"},
                {"key": "intro", "label": "Intro paragraph", "type": "textarea"},
                {"key": "projects", "label": "Projects", "type": "repeater", "item_label": "project",
                 "fields": [
                     {"key": "type_label", "label": "Project type label", "type": "text",
                      "placeholder": "e.g. Product design"},
                     {"key": "title", "label": "Title", "type": "text", "required": True},
                     {"key": "description", "label": "Description", "type": "textarea"},
                     {"key": "image_url", "label": "Project image", "type": "image", "required": False},
                     {"key": "tags", "label": "Tags (comma-separated)", "type": "text"},
                     {"key": "link_label", "label": "Link label", "type": "text",
                      "placeholder": "e.g. View case study"},
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
                {"key": "heading", "label": "Heading", "type": "text", "placeholder": "e.g. Let's work together"},
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
    ],
    "student": [
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
    ],
}
