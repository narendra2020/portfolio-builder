"""
Optional resume upload right after OTP verification: extracts text from
a PDF/DOCX resume, asks Claude to suggest taxonomy + pre-fill answers,
and stores the suggestions on the profile for the frontend to read (and
let the user confirm/edit) on the existing onboarding/questionnaire
screens. Never writes taxonomy FKs or QuestionnaireResponse rows itself
— those are only committed when the user actually submits each screen.
"""
import os
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.models import (
    AudienceType,
    OnboardingStatusEnum,
    QuestionnaireSchema,
    User,
)
from app.schemas.schemas import ResumeUploadOut, UserProfileOut
from app.services import onboarding, resume_llm, resume_parser

router = APIRouter(prefix="/api/profile", tags=["resume"])

_ALLOWED_EXTENSIONS = {"pdf", "docx"}


def _require_resume_pending(profile) -> None:
    if profile.onboarding_status != OnboardingStatusEnum.resume_pending:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Resume upload step is not currently active.")


@router.post("/resume", response_model=ResumeUploadOut)
def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = current_user.profile
    _require_resume_pending(profile)

    ext = file.filename.rsplit(".", 1)[-1].lower() if file.filename and "." in file.filename else ""
    if ext not in _ALLOWED_EXTENSIONS:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Unsupported file type. Please upload a PDF or DOCX resume "
            "(if you have an old .doc file, re-save/export it as PDF or DOCX first).",
        )

    raw_bytes = file.file.read()

    upload_dir = os.path.join(settings.RESUME_UPLOAD_DIR, current_user.id)
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"resume-{uuid.uuid4().hex}.{ext}"
    dest_path = os.path.join(upload_dir, filename)
    with open(dest_path, "wb") as f:
        f.write(raw_bytes)

    try:
        resume_text = resume_parser.extract_text(raw_bytes, file.filename)
    except resume_parser.ResumeParseError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc

    profile.resume_file_path = dest_path
    profile.resume_text = resume_text

    llm_available = bool(settings.ANTHROPIC_API_KEY)
    suggestions = None
    if llm_available:
        professional_audience = db.query(AudienceType).filter_by(slug="professional").first()
        schema_rows = (
            db.query(QuestionnaireSchema)
            .filter_by(audience_type_id=professional_audience.id if professional_audience else None, is_active=True)
            .order_by(QuestionnaireSchema.section_order)
            .all()
        )
        section_questions = {row.section_key: row.questions for row in schema_rows}
        audience_slugs = [a.slug for a in db.query(AudienceType).filter_by(is_active=True).all()]

        try:
            suggestions = resume_llm.suggest_from_resume(resume_text, section_questions, audience_slugs)
        except resume_llm.ResumeLLMError:
            llm_available = False
            suggestions = None

    profile.resume_suggestions = suggestions
    profile.onboarding_status = OnboardingStatusEnum.audience_pending
    db.commit()

    return ResumeUploadOut(
        suggestions=suggestions,
        llm_available=llm_available,
        onboarding_status=profile.onboarding_status,
        next_step=onboarding.next_step_for(profile.onboarding_status),
    )


@router.post("/resume/skip", response_model=UserProfileOut)
def skip_resume(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = current_user.profile
    _require_resume_pending(profile)
    profile.onboarding_status = OnboardingStatusEnum.audience_pending
    db.commit()
    return profile
