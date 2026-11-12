"""
One-shot idempotent seeding script.

Usage:
    python -m app.db.seed
"""
from slugify import slugify
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_value, hmac_lookup_hash
from app.db.seed_data import (
    AUDIENCE_QUESTIONNAIRE_SECTIONS,
    AUDIENCE_TYPES,
    CATEGORIES,
    PORTFOLIO_TEMPLATES,
    PROFESSIONS,
)
from app.db.session import Base, SessionLocal, engine
from app.models.models import (
    AudienceType,
    Category,
    PortfolioTemplate,
    Profession,
    QuestionnaireSchema,
    RoleEnum,
    Specialisation,
    User,
    UserProfile,
)


def seed_taxonomy(db: Session) -> None:
    audience_by_slug = {}
    for entry in AUDIENCE_TYPES:
        existing = db.query(AudienceType).filter_by(slug=entry["slug"]).first()
        if not existing:
            existing = AudienceType(**entry)
            db.add(existing)
            db.flush()
            print(f"[seed] created audience type: {existing.name}")
        audience_by_slug[entry["slug"]] = existing

    category_by_slug = {}
    for entry in CATEGORIES:
        audience = audience_by_slug[entry["audience_slug"]]
        existing = db.query(Category).filter_by(audience_type_id=audience.id, slug=entry["slug"]).first()
        if not existing:
            existing = Category(
                audience_type_id=audience.id,
                name=entry["name"],
                slug=entry["slug"],
                display_order=entry["display_order"],
            )
            db.add(existing)
            db.flush()
            print(f"[seed] created category: {existing.name}")
        category_by_slug[entry["slug"]] = existing

    for entry in PROFESSIONS:
        category = category_by_slug[entry["category_slug"]]
        profession = db.query(Profession).filter_by(category_id=category.id, slug=entry["slug"]).first()
        if not profession:
            profession = Profession(
                category_id=category.id,
                name=entry["name"],
                slug=entry["slug"],
                display_order=entry["display_order"],
            )
            db.add(profession)
            db.flush()
            print(f"[seed] created profession: {profession.name}")

        for order, spec_name in enumerate(entry.get("specialisations", []), start=1):
            spec_slug = slugify(spec_name)
            existing_spec = (
                db.query(Specialisation).filter_by(profession_id=profession.id, slug=spec_slug).first()
            )
            if not existing_spec:
                db.add(
                    Specialisation(
                        profession_id=profession.id,
                        name=spec_name,
                        slug=spec_slug,
                        display_order=order,
                    )
                )
                print(f"[seed] created specialisation: {spec_name}")

    db.commit()
    print("[seed] taxonomy up to date")


def seed_questionnaire_schemas(db: Session) -> None:
    for audience_slug, sections in AUDIENCE_QUESTIONNAIRE_SECTIONS.items():
        audience = db.query(AudienceType).filter_by(slug=audience_slug).first()
        if not audience:
            continue
        for section in sections:
            existing = (
                db.query(QuestionnaireSchema)
                .filter_by(audience_type_id=audience.id, section_key=section["section_key"])
                .first()
            )
            if not existing:
                db.add(
                    QuestionnaireSchema(
                        audience_type_id=audience.id,
                        section_key=section["section_key"],
                        section_title=section["section_title"],
                        section_order=section["section_order"],
                        questions=section["questions"],
                    )
                )
                print(f"[seed] created questionnaire section '{section['section_key']}' for audience {audience.name}")

    db.commit()
    print("[seed] questionnaire schemas up to date")


def seed_templates(db: Session) -> None:
    for entry in PORTFOLIO_TEMPLATES:
        existing = db.query(PortfolioTemplate).filter_by(slug=entry["slug"]).first()
        if not existing:
            fields = {k: v for k, v in entry.items() if k != "audience_slug"}
            audience_slug = entry.get("audience_slug")
            if audience_slug:
                audience = db.query(AudienceType).filter_by(slug=audience_slug).first()
                fields["audience_type_id"] = audience.id if audience else None
            db.add(PortfolioTemplate(**fields))
            print(f"[seed] created template: {entry['name']}")
    db.commit()
    print("[seed] templates up to date")


def seed_default_admin(db: Session) -> None:
    mobile_hash = hmac_lookup_hash(settings.DEFAULT_ADMIN_MOBILE)
    existing = db.query(User).filter_by(mobile_number_hash=mobile_hash).first()
    if not existing:
        admin = User(
            mobile_number_encrypted=settings.DEFAULT_ADMIN_MOBILE,
            mobile_number_hash=mobile_hash,
            full_name="Platform Administrator",
            password_hash=hash_value(settings.DEFAULT_ADMIN_PASSWORD),
            role=RoleEnum.super_admin,
            is_active=True,
        )
        db.add(admin)
        db.flush()
        db.add(
            UserProfile(
                user_id=admin.id,
                display_name="Platform Administrator",
                onboarding_status="onboarding_complete",
            )
        )
        db.commit()
        print(f"[seed] created default super_admin: {settings.DEFAULT_ADMIN_MOBILE}")
    else:
        print("[seed] default super_admin already exists")


def run() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_taxonomy(db)
        seed_questionnaire_schemas(db)
        seed_templates(db)
        seed_default_admin(db)
    finally:
        db.close()


if __name__ == "__main__":
    run()
