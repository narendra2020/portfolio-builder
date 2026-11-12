"""
User-owned drag-and-drop layout: a single ordered block list per user.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.models import LayoutBlockSet, User
from app.schemas.schemas import LayoutBlocksIn, LayoutBlocksOut

router = APIRouter(prefix="/api/layout", tags=["layout"])


@router.get("", response_model=LayoutBlocksOut)
def get_layout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    row = db.query(LayoutBlockSet).filter_by(user_id=current_user.id).first()
    if not row:
        return LayoutBlocksOut(blocks=[], updated_at=datetime.now(timezone.utc))
    return row


@router.put("", response_model=LayoutBlocksOut)
def set_layout(
    payload: LayoutBlocksIn, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    row = db.query(LayoutBlockSet).filter_by(user_id=current_user.id).first()
    if row:
        row.blocks = payload.blocks
    else:
        row = LayoutBlockSet(user_id=current_user.id, blocks=payload.blocks)
        db.add(row)
    db.commit()
    db.refresh(row)
    return row
