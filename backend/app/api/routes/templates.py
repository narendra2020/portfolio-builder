"""
Public read-only template catalog browsing, used for template selection.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.models import PortfolioTemplate, User
from app.schemas.schemas import PortfolioTemplateOut

router = APIRouter(prefix="/api/templates", tags=["templates"])


@router.get("", response_model=list[PortfolioTemplateOut])
def list_templates(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    audience_type_id = current_user.profile.audience_type_id if current_user.profile else None

    base_query = db.query(PortfolioTemplate).filter(PortfolioTemplate.is_active.is_(True))

    audience_specific = []
    if audience_type_id is not None:
        audience_specific = (
            base_query.filter(PortfolioTemplate.audience_type_id == audience_type_id)
            .order_by(PortfolioTemplate.display_order)
            .all()
        )

    global_templates = (
        base_query.filter(PortfolioTemplate.audience_type_id.is_(None))
        .order_by(PortfolioTemplate.display_order)
        .all()
    )

    def _sorted(templates: list[PortfolioTemplate]) -> list[PortfolioTemplate]:
        return sorted(
            templates,
            key=lambda tpl: (
                0 if tpl.slug == "universal-modern" else 1,
                tpl.display_order,
                tpl.id,
            ),
        )

    if audience_specific:
        existing_ids = {template.id for template in audience_specific}
        combined = audience_specific + [tpl for tpl in global_templates if tpl.id not in existing_ids]
        return _sorted(combined)

    return _sorted(global_templates)
