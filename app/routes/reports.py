from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.report import ReportResponse
from app.models.report import Report
from app.models.user import User
from app.auth.jwt import get_current_user
from app.utils.constants import FEATURE_REPORTS, PREMIUM_FEATURE_ERROR

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post("/generate", response_model=ReportResponse)
def generate_report(
    child_id: str,
    report_type: str,
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate a pediatrician report (Premium feature)"""
    # Check premium subscription
    user = db.query(User).filter(User.id == current_user_id).first()
    if user.subscription_tier != "premium":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=PREMIUM_FEATURE_ERROR.format(feature=FEATURE_REPORTS)
        )
    
    # TODO: Implement report generation
    raise NotImplementedError("Report generation not yet implemented")


@router.get("/{child_id}", response_model=List[ReportResponse])
def get_reports(
    child_id: str,
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get reports for a child"""
    reports = db.query(Report).filter(
        Report.child_id == child_id,
        Report.user_id == current_user_id
    ).all()
    return reports 