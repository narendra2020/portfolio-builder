"""
Super-admin user management: cascading user deletion, since
QuestionnaireResponse/LayoutBlockSet/PublishedPortfolio/UserProfile/
UserSession/Subscription/PaymentRequest/AiAssistantConfig/
AiAssistantQaPair/AiAssistantChatLog have plain (non-cascading) FKs to
users.id at the DB level.
"""
from sqlalchemy.orm import Session

from app.models.models import (
    AiAssistantChatLog,
    AiAssistantConfig,
    AiAssistantQaPair,
    AuditLog,
    LayoutBlockSet,
    PaymentRequest,
    PublishedPortfolio,
    QuestionnaireResponse,
    Subscription,
    User,
    UserProfile,
    UserSession,
)


def delete_user_cascade(db: Session, user: User) -> None:
    db.query(QuestionnaireResponse).filter_by(user_id=user.id).delete()
    db.query(LayoutBlockSet).filter_by(user_id=user.id).delete()
    db.query(PublishedPortfolio).filter_by(user_id=user.id).delete()
    db.query(UserProfile).filter_by(user_id=user.id).delete()
    db.query(UserSession).filter_by(user_id=user.id).delete()
    db.query(PaymentRequest).filter_by(user_id=user.id).delete()
    db.query(PaymentRequest).filter_by(reviewed_by_id=user.id).update({"reviewed_by_id": None})
    db.query(Subscription).filter_by(user_id=user.id).delete()
    db.query(AiAssistantChatLog).filter_by(user_id=user.id).delete()
    db.query(AiAssistantQaPair).filter_by(user_id=user.id).delete()
    db.query(AiAssistantConfig).filter_by(user_id=user.id).delete()
    db.query(AuditLog).filter_by(actor_id=user.id).update({"actor_id": None})
    db.delete(user)
    db.commit()
