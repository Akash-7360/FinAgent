from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.entities import Alert, User
from backend.app.schemas.schemas import AlertResponse
from backend.app.api.deps import get_current_user

router = APIRouter(prefix="/alerts", tags=["alerts"])

@router.get("", response_model=List[AlertResponse])
def list_alerts(
    resolved: Optional[bool] = None,
    limit: int = 50,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    q = db.query(Alert).filter(Alert.user_id == user.id)
    if resolved is not None:
        q = q.filter(Alert.is_resolved == resolved)
    alerts = q.order_by(Alert.created_at.desc()).limit(limit).all()
    return alerts

@router.post("/{id}/resolve", response_model=AlertResponse)
def resolve_alert(
    id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    alert = db.query(Alert).filter(Alert.id == id, Alert.user_id == user.id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.is_resolved = True
    db.commit()
    db.refresh(alert)
    return alert
