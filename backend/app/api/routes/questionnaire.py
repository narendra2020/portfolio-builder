"""
User-facing questionnaire endpoints: fetch the Universal template's fixed
section schema and save/read the current user's answers.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.models import AudienceType, QuestionnaireResponse, QuestionnaireSchema, User
from app.schemas.schemas import (
    QuestionnaireAnswerIn,
    QuestionnaireResponseOut,
    QuestionnaireSectionOut,
)

router = APIRouter(prefix="/api/questionnaire", tags=["questionnaire"])


@router.get("/schema", response_model=list[QuestionnaireSectionOut])
def get_schema(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    audience_type_id = current_user.profile.audience_type_id if current_user.profile else None
    if not audience_type_id:
        professional = db.query(AudienceType).filter_by(slug="professional").first()
        if not professional:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Questionnaire schema is not seeded.")
        audience_type_id = professional.id

    return (
        db.query(QuestionnaireSchema)
        .filter(QuestionnaireSchema.audience_type_id == audience_type_id, QuestionnaireSchema.is_active.is_(True))
        .order_by(QuestionnaireSchema.section_order)
        .all()
    )


@router.get("/responses", response_model=list[QuestionnaireResponseOut])
def get_responses(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(QuestionnaireResponse)
        .filter(QuestionnaireResponse.user_id == current_user.id)
        .all()
    )


@router.put("/responses", response_model=QuestionnaireResponseOut)
def save_response(
    payload: QuestionnaireAnswerIn, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    row = (
        db.query(QuestionnaireResponse)
        .filter(
            QuestionnaireResponse.user_id == current_user.id,
            QuestionnaireResponse.section_key == payload.section_key,
        )
        .first()
    )
    if row:
        row.answers = payload.answers
    else:
        row = QuestionnaireResponse(
            user_id=current_user.id, section_key=payload.section_key, answers=payload.answers
        )
        db.add(row)
    db.commit()
    db.refresh(row)
    return row
