from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from app.models.report import ReportType


class ReportCreate(BaseModel):
    child_id: str
    report_type: ReportType
    start_date: date
    end_date: date


class ReportGenerateRequest(BaseModel):
    child_id: str
    report_type: ReportType
    start_date: date
    end_date: date


class ReportResponse(BaseModel):
    id: str
    child_id: str
    user_id: str
    report_type: ReportType
    start_date: date
    end_date: date
    report_data: Dict[str, Any]
    pdf_url: Optional[str] = None
    insights: Optional[List[str]] = None
    recommendations: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 