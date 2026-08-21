from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from backend.app.db.session import get_db
from backend.app.routes.auth import get_current_user
from backend.app.models.models import User, Alert
from backend.app.schemas.schemas import AlertResponse

router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])

@router.get("/", response_model=List[AlertResponse])
def get_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves all scraper health, restoration, and market alerts.
    """
    alerts = db.query(Alert).order_by(Alert.created_at.desc()).all()
    return alerts

@router.post("/{alert_id}/read")
def mark_alert_read(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Marks a system alert as read.
    """
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
        
    alert.read = True
    db.commit()
    return {"message": f"Alert {alert_id} marked as read."}
