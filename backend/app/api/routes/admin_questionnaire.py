"""
Admin/content-manager questionnaire schema authoring.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.models.models import QuestionnaireSchema, RoleEnum
from app.schemas.schemas import (
    QuestionnaireSchemaCreateIn,
    QuestionnaireSchemaOut,
    QuestionnaireSchemaUpdateIn,
)

router = APIRouter(
    prefix="/api/admin/questionnaire",
    tags=["admin-questionnaire"],
    dependencies=[Depends(require_role(RoleEnum.super_admin, RoleEnum.admin, RoleEnum.content_manager))],
)


@router.get("/schemas", response_model=list[QuestionnaireSchemaOut])
def list_schemas(
    profession_id: int | None = Query(None),
    audience_type_id: int | None = Query(None),
    db: Session = Depends(get_db),
):
    if not profession_id and not audience_type_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Provide profession_id or audience_type_id")
    query = db.query(QuestionnaireSchema)
    if profession_id:
        query = query.filter(QuestionnaireSchema.profession_id == profession_id)
    else:
        query = query.filter(QuestionnaireSchema.audience_type_id == audience_type_id)
    return query.order_by(QuestionnaireSchema.section_order).all()


@router.post("/schemas", response_model=QuestionnaireSchemaOut)
def create_schema(payload: QuestionnaireSchemaCreateIn, db: Session = Depends(get_db)):
    if bool(payload.profession_id) == bool(payload.audience_type_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Provide exactly one of profession_id or audience_type_id")
    row = QuestionnaireSchema(**payload.model_dump())
    db.add(row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Duplicate section_key for this scope")
    return row


@router.put("/schemas/{schema_id}", response_model=QuestionnaireSchemaOut)
def update_schema(schema_id: int, payload: QuestionnaireSchemaUpdateIn, db: Session = Depends(get_db)):
    row = db.get(QuestionnaireSchema, schema_id)
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    db.commit()
    return row


@router.delete("/schemas/{schema_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_schema(schema_id: int, db: Session = Depends(get_db)):
    row = db.get(QuestionnaireSchema, schema_id)
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
    db.delete(row)
    db.commit()
