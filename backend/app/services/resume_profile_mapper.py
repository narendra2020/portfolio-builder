"""
Pure data transform: MePage profile (UserProfile + QuestionnaireResponse
rows) -> a resumes.content-shaped dict. No Claude call here. Every leaf
item is tagged source="mepage_import" so the editor can show provenance
and so re-imports (see merge logic used by
app/api/routes/resumes.py::import_profile) can tell which items are safe
to overwrite vs. user-edited.

Reads answers defensively (.get() throughout) since QuestionnaireResponse
.answers is free-form JSONB and a user may not have filled every section.
Never invents data: sections with no answers simply come back empty.
"""
import uuid

from sqlalchemy.orm import Session

from app.models.models import QuestionnaireResponse, User

_EDUCATION_SIGNAL_WORDS = ("education", "degree", "university", "college", "school", "academic")


def _new_id() -> str:
    return str(uuid.uuid4())


def _get_answers(db: Session, user_id: str, section_key: str) -> dict:
    row = (
        db.query(QuestionnaireResponse)
        .filter(QuestionnaireResponse.user_id == user_id, QuestionnaireResponse.section_key == section_key)
        .first()
    )
    return row.answers if row and isinstance(row.answers, dict) else {}


def _split_bullets(description: str | None) -> list[dict]:
    if not description:
        return []
    lines = [line.strip(" -•\t") for line in description.splitlines()]
    lines = [line for line in lines if line]
    if not lines:
        return []
    return [{"id": _new_id(), "text": line, "source": "mepage_import"} for line in lines]


def _looks_like_education(entry: dict) -> bool:
    haystack = " ".join(
        str(entry.get(key, "")) for key in ("category_label", "tags", "title")
    ).lower()
    return any(word in haystack for word in _EDUCATION_SIGNAL_WORDS)


def _tags_to_list(tags: str | None) -> list[str]:
    if not tags:
        return []
    return [t.strip() for t in tags.split(",") if t.strip()]


def _map_personal(user: User) -> dict:
    profile = user.profile
    contact = {}
    personal = {
        "full_name": (profile.display_name if profile else None) or user.full_name,
        "email": profile.email if profile else None,
        "phone": None,
        "city": profile.city if profile else None,
        "country": profile.country if profile else None,
        "linkedin_url": None,
        "portfolio_url": None,
        "github_url": None,
    }
    return personal, contact


def _apply_contact_socials(personal: dict, contact_answers: dict) -> list[dict]:
    """Matches contact.socials[] entries to known personal.* URL fields by
    label substring; anything unmatched is returned for additional_sections."""
    unmatched = []
    for link in contact_answers.get("socials") or []:
        label = str(link.get("label") or "").lower()
        url = link.get("url")
        if not url:
            continue
        if "linkedin" in label:
            personal["linkedin_url"] = url
        elif "github" in label:
            personal["github_url"] = url
        elif "portfolio" in label or "website" in label:
            personal["portfolio_url"] = url
        else:
            unmatched.append(link)
    if contact_answers.get("email") and not personal.get("email"):
        personal["email"] = contact_answers["email"]
    return unmatched


def build_resume_content_from_profile(user: User, db: Session) -> dict:
    about = _get_answers(db, user.id, "about")
    journey = _get_answers(db, user.id, "journey")
    work = _get_answers(db, user.id, "work")
    skills = _get_answers(db, user.id, "skills")
    contact = _get_answers(db, user.id, "contact")

    personal, _ = _map_personal(user)
    unmatched_links = _apply_contact_socials(personal, contact)

    summary_parts = [about.get("intro_large"), about.get("body")]
    summary_text = "\n\n".join(p for p in summary_parts if p)
    summary = {"text": summary_text, "source": "mepage_import"} if summary_text else {"text": "", "source": "mepage_import"}

    experience: list[dict] = []
    education: list[dict] = []
    for entry in journey.get("entries") or []:
        if not isinstance(entry, dict):
            continue
        item = {
            "id": _new_id(),
            "title": entry.get("title") or "",
            "employer": entry.get("org_location") or "",
            "location": "",
            "start_date": "",
            "end_date": "",
            "is_current": False,
            "date_range": entry.get("date_range") or "",
            "bullets": _split_bullets(entry.get("description")),
            "source": "mepage_import",
        }
        if _looks_like_education(entry):
            education.append({
                "id": item["id"],
                "institution": entry.get("org_location") or "",
                "degree": entry.get("title") or "",
                "field": "",
                "start_date": "",
                "end_date": "",
                "date_range": entry.get("date_range") or "",
                "gpa": None,
                "source": "mepage_import",
            })
        else:
            experience.append(item)

    projects: list[dict] = []
    for proj in work.get("projects") or []:
        if not isinstance(proj, dict):
            continue
        description_bullets = _split_bullets(proj.get("description"))
        projects.append({
            "id": _new_id(),
            "title": proj.get("title") or "",
            "description_bullets": description_bullets,
            "tags": _tags_to_list(proj.get("tags")),
            "link_url": proj.get("link_url") or "",
            "source": "mepage_import",
        })

    skill_groups: list[dict] = []
    for group in skills.get("groups") or []:
        if not isinstance(group, dict):
            continue
        skill_groups.append({
            "title": group.get("title") or "",
            "skills": _tags_to_list(group.get("skills")),
        })

    additional_sections: list[dict] = []
    if unmatched_links:
        additional_sections.append({
            "id": _new_id(),
            "heading": "Links",
            "items": [f"{l.get('label')}: {l.get('url')}" for l in unmatched_links],
            "source": "mepage_import",
        })

    return {
        "personal": personal,
        "summary": summary,
        "experience": experience,
        "projects": projects,
        "skills": {"groups": skill_groups, "source": "mepage_import"},
        "education": education,
        "certifications": [],
        "achievements": [],
        "additional_sections": additional_sections,
    }


def merge_profile_import(existing_content: dict, fresh_content: dict) -> dict:
    """
    Additive merge for explicit re-import: items still tagged
    source="mepage_import" in `existing_content` are replaced wholesale by
    the freshly-mapped equivalents; items the user edited
    (source="user_edited") or that AI generated (source="ai_generated")
    are left untouched and the fresh mapper output for list-type sections
    is appended after them.
    """
    merged = dict(existing_content)

    def _merge_list(key: str) -> list:
        kept = [item for item in (existing_content.get(key) or []) if item.get("source") != "mepage_import"]
        return kept + (fresh_content.get(key) or [])

    for key in ("experience", "projects", "education", "certifications", "achievements", "additional_sections"):
        merged[key] = _merge_list(key)

    if (existing_content.get("summary") or {}).get("source") == "mepage_import" or not existing_content.get("summary", {}).get("text"):
        merged["summary"] = fresh_content["summary"]

    if (existing_content.get("skills") or {}).get("source") == "mepage_import" or not (existing_content.get("skills") or {}).get("groups"):
        merged["skills"] = fresh_content["skills"]

    existing_personal = existing_content.get("personal") or {}
    merged["personal"] = {**fresh_content["personal"], **{k: v for k, v in existing_personal.items() if v}}

    return merged
