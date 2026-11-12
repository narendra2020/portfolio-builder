"""
Admin-only taxonomy management (super_admin/admin roles only).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.models.models import AudienceType, Category, Profession, Specialisation
from app.schemas.schemas import (
    AudienceTypeCreateIn,
    AudienceTypeOut,
    CategoryCreateIn,
    CategoryOut,
    ProfessionCreateIn,
    ProfessionOut,
    SpecialisationCreateIn,
    SpecialisationOut,
)

router = APIRouter(prefix="/api/admin", tags=["admin-taxonomy"], dependencies=[Depends(require_admin)])


def _create(db: Session, model, payload):
    row = model(**payload.model_dump())
    db.add(row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Duplicate slug for this parent")
    return row


def _delete(db: Session, model, row_id):
    row = db.get(model, row_id)
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
    db.delete(row)
    db.commit()


@router.post("/audience-types", response_model=AudienceTypeOut)
def create_audience_type(payload: AudienceTypeCreateIn, db: Session = Depends(get_db)):
    return _create(db, AudienceType, payload)


@router.delete("/audience-types/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_audience_type(item_id: int, db: Session = Depends(get_db)):
    _delete(db, AudienceType, item_id)


@router.post("/categories", response_model=CategoryOut)
def create_category(payload: CategoryCreateIn, db: Session = Depends(get_db)):
    return _create(db, Category, payload)


@router.delete("/categories/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(item_id: int, db: Session = Depends(get_db)):
    _delete(db, Category, item_id)


@router.post("/professions", response_model=ProfessionOut)
def create_profession(payload: ProfessionCreateIn, db: Session = Depends(get_db)):
    return _create(db, Profession, payload)


@router.delete("/professions/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_profession(item_id: int, db: Session = Depends(get_db)):
    _delete(db, Profession, item_id)


@router.post("/specialisations", response_model=SpecialisationOut)
def create_specialisation(payload: SpecialisationCreateIn, db: Session = Depends(get_db)):
    return _create(db, Specialisation, payload)


@router.delete("/specialisations/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_specialisation(item_id: int, db: Session = Depends(get_db)):
    _delete(db, Specialisation, item_id)
