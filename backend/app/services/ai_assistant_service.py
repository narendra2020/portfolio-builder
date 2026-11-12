"""
AI Assistant knowledge assembly: builds the plain-text context handed to
the LLM on every chat request. Pulls from the user's existing profile
data (UserProfile, QuestionnaireResponse) plus their authored
AiAssistantQaPair rows — no web scraping, no separate "website" source.
"""
from sqlalchemy.orm import Session

from app.models.models import AiAssistantConfig, AiAssistantQaPair, QuestionnaireResponse, User


def get_or_create_config(user: User, db: Session) -> AiAssistantConfig:
    config = db.query(AiAssistantConfig).filter_by(user_id=user.id).first()
    if not config:
        config = AiAssistantConfig(user_id=user.id)
        db.add(config)
        db.commit()
        db.refresh(config)
    return config


def build_knowledge_context(user: User, db: Session) -> str:
    config = get_or_create_config(user, db)
    sections: list[str] = []

    if config.use_profile_data and user.profile:
        profile = user.profile
        profile_lines = [f"Name: {profile.display_name}"] if profile.display_name else []
        if profile.city or profile.country:
            profile_lines.append(f"Location: {', '.join(p for p in (profile.city, profile.country) if p)}")
        if profile.resume_text:
            profile_lines.append(f"Resume:\n{profile.resume_text}")
        if profile_lines:
            sections.append("## Profile\n" + "\n".join(profile_lines))

        responses = db.query(QuestionnaireResponse).filter_by(user_id=user.id).all()
        for response in responses:
            sections.append(f"## {response.section_key}\n{response.answers}")

    qa_pairs = (
        db.query(AiAssistantQaPair)
        .filter_by(user_id=user.id)
        .order_by(AiAssistantQaPair.display_order)
        .all()
    )
    if qa_pairs:
        qa_lines = [f"Q: {pair.question}\nA: {pair.answer}" for pair in qa_pairs]
        sections.append("## Frequently asked questions\n" + "\n\n".join(qa_lines))

    return "\n\n".join(sections)
