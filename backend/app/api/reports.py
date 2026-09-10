from typing import Optional, List
from datetime import date
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.entities import MonthlyReport, User
from backend.app.schemas.schemas import MonthlyReportResponse
from backend.app.api.deps import get_current_user
from backend.app.agent.tools import AgentTools

router = APIRouter(prefix="/reports", tags=["reports"])

@router.post("/monthly", response_model=MonthlyReportResponse)
def generate_monthly_report(
    month: Optional[int] = Query(None, ge=1, le=12),
    year: Optional[int] = Query(None, ge=2000, le=2100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tools = AgentTools(db, user.id)
    report_dict = tools.generate_monthly_report(month=month, year=year)

    rep = db.query(MonthlyReport).filter(
        MonthlyReport.user_id == user.id,
        MonthlyReport.month == report_dict["month"],
        MonthlyReport.year == report_dict["year"]
    ).first()

    if not rep:
        raise HTTPException(status_code=500, detail="Failed to persist report")
    return rep

@router.get("/monthly", response_model=List[MonthlyReportResponse])
def list_reports(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    reports = db.query(MonthlyReport).filter(
        MonthlyReport.user_id == user.id
    ).order_by(MonthlyReport.year.desc(), MonthlyReport.month.desc()).all()
    return reports
