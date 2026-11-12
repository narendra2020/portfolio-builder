"""
Static site generation for published portfolios. Renders a user's
profile + layout blocks into a self-contained site written to
PUBLISHED_SITES_DIR/<slug>/ (index.html + assets/style.css [+ assets/
script.js] + assets/images/<file>), served by the portfolio-sites-preview
nginx container via wildcard *.localhost subdomain routing.
"""
import re
import shutil
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.models import AiAssistantConfig, LayoutBlockSet, QuestionnaireResponse, User

# Imported lazily inside publish_site (not at module level) because
# subscription_service imports this module too (for unpublish_site on
# expiry) — a top-level import here would be circular.

BACKEND_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = BACKEND_DIR / "templates"
DEFAULT_TEMPLATE_FILE = "default_template.html.j2"

_env = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=select_autoescape(["html", "j2"]),
    trim_blocks=True,
    lstrip_blocks=True,
)

# Matches the /api/uploads/images/<user_id>/<filename> URLs handed out by
# app/api/routes/media.py, wherever they appear in rendered HTML attributes.
_UPLOADED_IMAGE_RE = re.compile(r"/api/uploads/images/[^\"'\s]+")


def _initials(display_name: str | None) -> str:
    if not display_name:
        return ""
    parts = display_name.split()
    return "".join(p[0].upper() for p in parts[:2])


# Template families that share a base stylesheet/script. A template whose
# stem starts with the prefix gets the shared CSS prepended to its own CSS
# and uses the shared JS (unless it ships its own <stem>.js).
SHARED_TEMPLATE_ASSETS = {
    "student_showcase_": ("_student_showcase_base.css", "_student_showcase.js"),
}


def _template_asset_files(template_file: str) -> tuple[list[Path], Path | None]:
    stem = template_file.rsplit(".html.j2", 1)[0]
    css_files: list[Path] = []
    js_path: Path | None = None
    for prefix, (shared_css, shared_js) in SHARED_TEMPLATE_ASSETS.items():
        if stem.startswith(prefix):
            css_files.append(TEMPLATE_DIR / shared_css)
            js_path = TEMPLATE_DIR / shared_js
    own_css = TEMPLATE_DIR / f"{stem}.css"
    own_js = TEMPLATE_DIR / f"{stem}.js"
    if own_css.exists():
        css_files.append(own_css)
    if own_js.exists():
        js_path = own_js
    return [p for p in css_files if p.exists()], (js_path if js_path and js_path.exists() else None)


def _render_html(user: User, db: Session) -> tuple[str, str]:
    profile = user.profile
    template_file = (profile.template.template_file if profile and profile.template else None) or DEFAULT_TEMPLATE_FILE
    layout = db.query(LayoutBlockSet).filter_by(user_id=user.id).first()
    blocks = layout.blocks if layout else []
    responses = db.query(QuestionnaireResponse).filter_by(user_id=user.id).all()
    answers = {r.section_key: r.answers for r in responses}
    initials = _initials(profile.display_name if profile else None)
    template = _env.get_template(template_file)
    html = template.render(profile=profile, blocks=blocks, answers=answers, initials=initials)
    return html, template_file


def _localize_images(html: str, dest_root: Path) -> str:
    """
    Copies every uploaded image referenced in the rendered HTML into
    dest_root/assets/images/ and rewrites its URL to the relative path,
    so the published site has no runtime dependency on the backend's
    /api/uploads route.
    """
    images_dir = dest_root / "assets" / "images"

    def _copy_and_rewrite(match: re.Match) -> str:
        url = match.group(0)
        filename = url.rsplit("/", 1)[-1]
        src_path = Path(settings.UPLOADS_DIR) / url.removeprefix("/api/uploads/")
        if not src_path.is_file():
            return url
        images_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_path, images_dir / filename)
        return f"assets/images/{filename}"

    return _UPLOADED_IMAGE_RE.sub(_copy_and_rewrite, html)


def _inject_ai_assistant_widget(html: str, user: User, slug: str, db: Session) -> str:
    from app.services.subscription_service import is_ai_assistant_entitled

    config = db.query(AiAssistantConfig).filter_by(user_id=user.id).first()
    if not config or not config.enabled or not is_ai_assistant_entitled(user, db):
        return html
    script_tag = f'<script src="/api/ai-assistant-widget.js" data-slug="{slug}" defer></script>'
    if "</body>" in html:
        return html.replace("</body>", script_tag + "</body>")
    return html + script_tag


def publish_site(user: User, slug: str, db: Session) -> None:
    html, template_file = _render_html(user, db)
    html = _inject_ai_assistant_widget(html, user, slug, db)
    dest_root = Path(settings.PUBLISHED_SITES_DIR) / slug
    if dest_root.exists():
        shutil.rmtree(dest_root)
    dest_root.mkdir(parents=True)

    html = _localize_images(html, dest_root)
    (dest_root / "index.html").write_text(html, encoding="utf-8")

    assets_dir = dest_root / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    css_files, js_file = _template_asset_files(template_file)
    if css_files:
        css = "\n".join(p.read_text(encoding="utf-8") for p in css_files)
        (assets_dir / "style.css").write_text(css, encoding="utf-8")
    if js_file:
        shutil.copy2(js_file, assets_dir / "script.js")


def unpublish_site(slug: str) -> None:
    dest_root = Path(settings.PUBLISHED_SITES_DIR) / slug
    if dest_root.exists():
        shutil.rmtree(dest_root)
