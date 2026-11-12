"""
AI Resume Builder endpoints. Every handler is scoped strictly to
current_user.id (house rule — never trust a client-supplied user id, see
app/api/routes/questionnaire.py); cross-user access to any resume returns
404, never 403, so existence is never leaked.
"""
import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.models import Resume, ResumeExport, ResumeVersion, User
from app.schemas.schemas import (
    AtsAnalysisOut,
    ImproveFieldIn,
    ImproveFieldOut,
    JobDescriptionIn,
    ResumeCreateIn,
    ResumeGenerateIn,
    ResumeGenerateOut,
    ResumeListItemOut,
    ResumeOut,
    ResumeUpdateIn,
    ResumeVersionOut,
    TailoringOut,
)
from app.services import resume_parser, resume_pdf, resume_pipeline
from app.services import resume_profile_mapper as mapper
from app.services.resume_pipeline import ResumePipelineError
from app.services.subscription_service import require_resume_builder_entitled

router = APIRouter(prefix="/api/resumes", tags=["resumes"])

_EMPTY_CONTENT = {
    "personal": {}, "summary": {"text": "", "source": "scratch"},
    "experience": [], "projects": [], "skills": {"groups": [], "source": "scratch"},
    "education": [], "certifications": [], "achievements": [], "additional_sections": [],
}

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_VERSIONS_PER_RESUME = 20


def _get_owned_resume(resume_id: str, current_user: User, db: Session) -> Resume:
    resume = (
        db.query(Resume)
        .filter(Resume.id == resume_id, Resume.user_id == current_user.id, Resume.is_archived.is_(False))
        .first()
    )
    if not resume:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Resume not found.")
    return resume


def _snapshot_version(resume: Resume, reason: str, db: Session) -> None:
    db.add(ResumeVersion(resume_id=resume.id, content=resume.content, reason=reason))
    db.flush()
    extra = (
        db.query(ResumeVersion)
        .filter(ResumeVersion.resume_id == resume.id)
        .order_by(ResumeVersion.created_at.desc())
        .offset(MAX_VERSIONS_PER_RESUME)
        .all()
    )
    for row in extra:
        db.delete(row)


@router.get("", response_model=list[ResumeListItemOut])
def list_resumes(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(Resume)
        .filter(Resume.user_id == current_user.id, Resume.is_archived.is_(False))
        .order_by(Resume.updated_at.desc())
        .all()
    )


@router.post("", response_model=ResumeOut, status_code=status.HTTP_201_CREATED)
def create_resume(
    payload: ResumeCreateIn, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    content = dict(_EMPTY_CONTENT)
    last_profile_import_at = None
    if payload.source == "mepage_import":
        content = mapper.build_resume_content_from_profile(current_user, db)
        last_profile_import_at = datetime.now(timezone.utc)

    resume = Resume(
        user_id=current_user.id,
        title=payload.title,
        template_key=payload.template_key,
        content=content,
        source=payload.source,
        last_profile_import_at=last_profile_import_at,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume


@router.post("/import", response_model=ResumeOut, status_code=status.HTTP_201_CREATED)
async def import_resume_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ext = file.filename.rsplit(".", 1)[-1].lower() if file.filename and "." in file.filename else ""
    if ext not in ("pdf", "docx"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Only PDF or DOCX files are supported.")

    file_bytes = await file.read()
    if len(file_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "File is too large (max 10MB).")

    try:
        resume_text = resume_parser.extract_text(file_bytes, file.filename)
    except resume_parser.ResumeParseError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    content = dict(_EMPTY_CONTENT)
    content["additional_sections"] = [{
        "id": "raw-import", "heading": "Imported Resume Text (unprocessed)",
        "items": [resume_text], "source": "upload_import",
    }]

    resume = Resume(
        user_id=current_user.id,
        title=file.filename.rsplit(".", 1)[0] or "Imported Resume",
        template_key="ats_professional",
        content=content,
        source="upload_import",
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume


@router.get("/{resume_id}", response_model=ResumeOut)
def get_resume(resume_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _get_owned_resume(resume_id, current_user, db)


@router.put("/{resume_id}", response_model=ResumeOut)
def update_resume(
    resume_id: str, payload: ResumeUpdateIn,
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    resume = _get_owned_resume(resume_id, current_user, db)
    if payload.title is not None:
        resume.title = payload.title
    if payload.template_key is not None:
        resume.template_key = payload.template_key
    if payload.target_role is not None:
        resume.target_role = payload.target_role
    if payload.content is not None:
        resume.content = payload.content
    db.commit()
    db.refresh(resume)
    return resume


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_resume(resume_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    resume = _get_owned_resume(resume_id, current_user, db)
    resume.is_archived = True
    db.commit()
    return None


@router.post("/{resume_id}/import-profile", response_model=ResumeOut)
def import_profile(resume_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    resume = _get_owned_resume(resume_id, current_user, db)
    _snapshot_version(resume, "pre_import", db)
    fresh = mapper.build_resume_content_from_profile(current_user, db)
    resume.content = mapper.merge_profile_import(resume.content, fresh)
    resume.last_profile_import_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(resume)
    return resume


@router.post("/{resume_id}/generate", response_model=ResumeGenerateOut)
def generate_resume(
    resume_id: str, payload: ResumeGenerateIn,
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    resume = _get_owned_resume(resume_id, current_user, db)
    require_resume_builder_entitled(current_user, db)  # no-op today; real gate hooks in here later

    _snapshot_version(resume, "pre_generate", db)

    try:
        result = resume_pipeline.run_generation_pipeline(
            resume.content, target_role=payload.target_role, job_description=payload.job_description
        )
    except ResumePipelineError as exc:
        db.rollback()
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "Resume generation is temporarily unavailable. Please try again."
        ) from exc

    resume.content = result["content"]
    if payload.target_role:
        resume.target_role = payload.target_role
    db.commit()
    db.refresh(resume)
    return ResumeGenerateOut(
        resume=resume, analysis=result["analysis"], critique=result["critique"], retried=result["retried"],
    )


@router.post("/{resume_id}/improve-field", response_model=ImproveFieldOut)
def improve_field(
    resume_id: str, payload: ImproveFieldIn,
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    _get_owned_resume(resume_id, current_user, db)
    try:
        revised = resume_pipeline.improve_bullet_text(payload.current_text, payload.action, payload.context)
    except ResumePipelineError as exc:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "Could not improve this text right now. Please try again."
        ) from exc
    return ImproveFieldOut(revised_text=revised)


@router.post("/{resume_id}/analyze-ats", response_model=AtsAnalysisOut)
def analyze_ats(resume_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    resume = _get_owned_resume(resume_id, current_user, db)
    try:
        result = resume_pipeline.analyze_ats(resume.content)
    except ResumePipelineError as exc:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "ATS analysis is temporarily unavailable. Please try again."
        ) from exc

    resume.ats_score = result.get("overall_score")
    resume.ats_analysis = result.get("categories")
    db.commit()
    db.refresh(resume)
    return AtsAnalysisOut(categories=result["categories"], overall_score=result["overall_score"])


@router.post("/{resume_id}/analyze-job-description", response_model=TailoringOut)
def analyze_job_description(
    resume_id: str, payload: JobDescriptionIn,
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    resume = _get_owned_resume(resume_id, current_user, db)
    try:
        result = resume_pipeline.tailor_resume_to_job(resume.content, payload.job_description)
    except ResumePipelineError as exc:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "Job description analysis is temporarily unavailable. Please try again."
        ) from exc

    resume.tailoring_job_description = payload.job_description
    resume.tailoring_match_scores = result.get("match_scores")
    resume.tailoring_gap_analysis = result.get("gap_analysis")
    db.commit()
    db.refresh(resume)
    return TailoringOut(
        match_scores=result["match_scores"],
        gap_analysis=result["gap_analysis"],
        suggested_bullet_rewrites=result["suggested_bullet_rewrites"],
    )


@router.get("/{resume_id}/export")
def export_resume_pdf(
    resume_id: str, template_key: str | None = None, page_size: str = "A4",
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    resume = _get_owned_resume(resume_id, current_user, db)
    require_resume_builder_entitled(current_user, db)  # no-op today; real gate hooks in here later

    effective_template = template_key or resume.template_key
    pdf_bytes = resume_pdf.render_resume_pdf(resume.content, effective_template, page_size)
    filename = resume_pdf.build_export_filename(resume.content)

    os.makedirs(settings.RESUME_EXPORT_DIR, exist_ok=True)
    file_path = os.path.join(settings.RESUME_EXPORT_DIR, f"{resume.id}-{int(datetime.now(timezone.utc).timestamp())}.pdf")
    with open(file_path, "wb") as f:
        f.write(pdf_bytes)
    db.add(ResumeExport(resume_id=resume.id, template_key=effective_template, file_path=file_path, page_size=page_size))
    db.commit()

    from io import BytesIO
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{resume_id}/versions", response_model=list[ResumeVersionOut])
def list_versions(resume_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    resume = _get_owned_resume(resume_id, current_user, db)
    return (
        db.query(ResumeVersion)
        .filter(ResumeVersion.resume_id == resume.id)
        .order_by(ResumeVersion.created_at.desc())
        .all()
    )


@router.post("/{resume_id}/versions/{version_id}/restore", response_model=ResumeOut)
def restore_version(
    resume_id: str, version_id: str,
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    resume = _get_owned_resume(resume_id, current_user, db)
    version = db.query(ResumeVersion).filter(
        ResumeVersion.id == version_id, ResumeVersion.resume_id == resume.id
    ).first()
    if not version:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Version not found.")

    _snapshot_version(resume, "manual_save", db)
    resume.content = version.content
    db.commit()
    db.refresh(resume)
    return resume
