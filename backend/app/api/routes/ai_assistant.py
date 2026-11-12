"""
AI Assistant chat widget: owner-facing config + Q&A CRUD (authenticated,
prefix /api/ai-assistant), and the public, unauthenticated widget
endpoints served on a visitor's published portfolio page (prefix
/api/public/ai-assistant).
"""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.models import (
    AiAssistantChatLog,
    AiAssistantConfig,
    AiAssistantQaPair,
    PublishedPortfolio,
    PublishedPortfolioStatusEnum,
    User,
)
from app.schemas.schemas import (
    AiAssistantConfigOut,
    AiAssistantConfigUpdateIn,
    AiAssistantLimitsOut,
    AiAssistantPublicInfoOut,
    AiAssistantStatusOut,
    ChatRequestIn,
    ChatResponseOut,
    QaPairCreateIn,
    QaPairOut,
)
from app.services.ai_assistant_llm import AiAssistantLLMError, answer_question
from app.services.ai_assistant_service import build_knowledge_context, get_or_create_config
from app.services.subscription_service import is_ai_assistant_entitled, require_ai_assistant_entitled

router = APIRouter(prefix="/api/ai-assistant", tags=["ai-assistant"])
public_router = APIRouter(prefix="/api/public/ai-assistant", tags=["ai-assistant-public"])


# ---- Owner-facing (authenticated) ----

@router.get("/limits", response_model=AiAssistantLimitsOut)
def get_limits():
    return AiAssistantLimitsOut(
        max_qa_pairs=settings.AI_ASSISTANT_MAX_QA_PAIRS,
        question_max_length=settings.AI_ASSISTANT_QUESTION_MAX_LENGTH,
        answer_max_length=settings.AI_ASSISTANT_ANSWER_MAX_LENGTH,
        add_on_price_rupees=settings.AI_ASSISTANT_ADD_ON_PRICE_RUPEES,
    )


@router.get("/status", response_model=AiAssistantStatusOut)
def get_status(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    config = get_or_create_config(current_user, db)
    qa_pair_count = db.query(AiAssistantQaPair).filter_by(user_id=current_user.id).count()
    return AiAssistantStatusOut(
        entitled=is_ai_assistant_entitled(current_user, db),
        config=config,
        qa_pair_count=qa_pair_count,
    )


@router.put("/config", response_model=AiAssistantConfigOut)
def update_config(
    payload: AiAssistantConfigUpdateIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_ai_assistant_entitled(current_user, db)
    config = get_or_create_config(current_user, db)
    config.enabled = payload.enabled
    config.use_profile_data = payload.use_profile_data
    db.commit()
    db.refresh(config)
    return config


@router.get("/qa-pairs", response_model=list[QaPairOut])
def list_qa_pairs(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(AiAssistantQaPair)
        .filter_by(user_id=current_user.id)
        .order_by(AiAssistantQaPair.display_order)
        .all()
    )


@router.post("/qa-pairs", response_model=QaPairOut)
def create_qa_pair(
    payload: QaPairCreateIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_ai_assistant_entitled(current_user, db)

    existing_count = db.query(AiAssistantQaPair).filter_by(user_id=current_user.id).count()
    if existing_count >= settings.AI_ASSISTANT_MAX_QA_PAIRS:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"You can add at most {settings.AI_ASSISTANT_MAX_QA_PAIRS} question/answer pairs.",
        )
    question = payload.question.strip()
    answer = payload.answer.strip()
    if not question or len(question) > settings.AI_ASSISTANT_QUESTION_MAX_LENGTH:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"Question must be 1-{settings.AI_ASSISTANT_QUESTION_MAX_LENGTH} characters.",
        )
    if not answer or len(answer) > settings.AI_ASSISTANT_ANSWER_MAX_LENGTH:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"Answer must be 1-{settings.AI_ASSISTANT_ANSWER_MAX_LENGTH} characters.",
        )

    pair = AiAssistantQaPair(
        user_id=current_user.id, question=question, answer=answer, display_order=existing_count
    )
    db.add(pair)
    db.commit()
    db.refresh(pair)
    return pair


@router.delete("/qa-pairs/{pair_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_qa_pair(
    pair_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    pair = db.get(AiAssistantQaPair, pair_id)
    if not pair or pair.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
    db.delete(pair)
    db.commit()


# ---- Public (unauthenticated widget) ----

def _resolve_active_owner(slug: str, db: Session) -> User:
    """
    Looks up the published, enabled, entitled owner for a slug. Returns a
    generic 404 on any failure mode (not published, not configured, not
    entitled) rather than leaking which — this endpoint is unauthenticated.
    """
    portfolio = (
        db.query(PublishedPortfolio)
        .filter_by(slug=slug, status=PublishedPortfolioStatusEnum.published)
        .first()
    )
    not_found = HTTPException(status.HTTP_404_NOT_FOUND, "AI Assistant is not available for this site.")
    if not portfolio:
        raise not_found
    user = db.get(User, portfolio.user_id)
    if not user:
        raise not_found
    config = db.query(AiAssistantConfig).filter_by(user_id=user.id).first()
    if not config or not config.enabled:
        raise not_found
    if not is_ai_assistant_entitled(user, db):
        raise not_found
    return user


def _owner_display_name(user: User) -> str:
    if user.profile and user.profile.display_name:
        return user.profile.display_name
    return user.full_name


@public_router.get("/{slug}/info", response_model=AiAssistantPublicInfoOut)
def get_public_info(slug: str, db: Session = Depends(get_db)):
    user = _resolve_active_owner(slug, db)
    return AiAssistantPublicInfoOut(owner_name=_owner_display_name(user))


@public_router.post("/{slug}/chat", response_model=ChatResponseOut)
def chat(slug: str, payload: ChatRequestIn, db: Session = Depends(get_db)):
    user = _resolve_active_owner(slug, db)

    message = payload.message.strip()
    if not message:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Message cannot be empty.")

    since = datetime.now(timezone.utc) - timedelta(days=1)
    recent_count = (
        db.query(AiAssistantChatLog)
        .filter(AiAssistantChatLog.user_id == user.id, AiAssistantChatLog.created_at > since)
        .count()
    )
    if recent_count >= settings.AI_ASSISTANT_DAILY_MESSAGE_LIMIT:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "This assistant has reached its daily message limit.")

    knowledge_context = build_knowledge_context(user, db)
    try:
        answer = answer_question(knowledge_context, message, _owner_display_name(user))
    except AiAssistantLLMError:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "The assistant is temporarily unavailable.")

    db.add(AiAssistantChatLog(user_id=user.id))
    db.commit()
    return ChatResponseOut(answer=answer)
