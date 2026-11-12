"""
Public read-only taxonomy browsing (audience -> category -> profession
-> specialisation), used by onboarding.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import AudienceType, Category, Profession, Specialisation
from app.schemas.schemas import AudienceTypeOut, CategoryOut, ProfessionOut, SpecialisationOut

router = APIRouter(prefix="/api/taxonomy", tags=["taxonomy"])


@router.get("/audience-types", response_model=list[AudienceTypeOut])
def list_audience_types(db: Session = Depends(get_db)):
    return (
        db.query(AudienceType)
        .filter_by(is_active=True)
        .order_by(AudienceType.display_order)
        .all()
    )


@router.get("/categories", response_model=list[CategoryOut])
def list_categories(audience_type_id: int = Query(...), db: Session = Depends(get_db)):
    return (
        db.query(Category)
        .filter_by(audience_type_id=audience_type_id, is_active=True)
        .order_by(Category.display_order)
        .all()
    )


@router.get("/professions", response_model=list[ProfessionOut])
def list_professions(category_id: int = Query(...), db: Session = Depends(get_db)):
    return (
        db.query(Profession)
        .filter_by(category_id=category_id, is_active=True)
        .order_by(Profession.display_order)
        .all()
    )


@router.get("/specialisations", response_model=list[SpecialisationOut])
def list_specialisations(profession_id: int = Query(...), db: Session = Depends(get_db)):
    return (
        db.query(Specialisation)
        .filter_by(profession_id=profession_id, is_active=True)
        .order_by(Specialisation.display_order)
        .all()
    )
