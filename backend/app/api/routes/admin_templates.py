"""
Admin/template-manager template registry authoring.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.models.models import PortfolioTemplate, RoleEnum
from app.schemas.schemas import (
    PortfolioTemplateAdminOut,
    PortfolioTemplateCreateIn,
    PortfolioTemplateUpdateIn,
)

router = APIRouter(
    prefix="/api/admin/templates",
    tags=["admin-templates"],
    dependencies=[Depends(require_role(RoleEnum.super_admin, RoleEnum.admin, RoleEnum.template_manager))],
)


@router.get("", response_model=list[PortfolioTemplateAdminOut])
def list_templates(db: Session = Depends(get_db)):
    return db.query(PortfolioTemplate).order_by(PortfolioTemplate.display_order).all()


@router.post("", response_model=PortfolioTemplateAdminOut)
def create_template(payload: PortfolioTemplateCreateIn, db: Session = Depends(get_db)):
    row = PortfolioTemplate(**payload.model_dump())
    db.add(row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Duplicate name or slug")
    return row


@router.put("/{template_id}", response_model=PortfolioTemplateAdminOut)
def update_template(template_id: int, payload: PortfolioTemplateUpdateIn, db: Session = Depends(get_db)):
    row = db.get(PortfolioTemplate, template_id)
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Duplicate name or slug")
    return row


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(template_id: int, db: Session = Depends(get_db)):
    row = db.get(PortfolioTemplate, template_id)
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
    db.delete(row)
    db.commit()
