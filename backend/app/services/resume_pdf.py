"""
Server-side resume PDF rendering via WeasyPrint (HTML -> PDF). Templates
live in app/templates/resume_pdf/*.html (Jinja2, already a dependency).
All templates must stay ATS-compliant: single column, no icons/progress
bars/skill meters, plain <ul><li> bullets, selectable/searchable text,
web-safe fonts only (no runtime font fetches).
"""
import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates" / "resume_pdf"

_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html"]),
)

_PAGE_SIZES = {"A4": "A4", "Letter": "Letter"}

_VALID_TEMPLATE_KEYS = {"ats_professional", "modern", "executive"}


def _template_file(template_key: str) -> str:
    key = template_key if template_key in _VALID_TEMPLATE_KEYS else "ats_professional"
    return f"{key}.html"


def render_resume_pdf(content: dict, template_key: str, page_size: str = "A4") -> bytes:
    template = _env.get_template(_template_file(template_key))
    size = _PAGE_SIZES.get(page_size, "A4")
    html = template.render(content=content, page_size=size)
    return HTML(string=html).write_pdf()


def build_export_filename(content: dict) -> str:
    full_name = (content.get("personal") or {}).get("full_name") or ""
    slug = re.sub(r"[^A-Za-z0-9]+", "-", full_name).strip("-")
    if not slug:
        return "Resume.pdf"
    return f"{slug}-Resume.pdf"
