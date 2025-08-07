from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class CaregiverInviteRequest(BaseModel):
    child_id: str
    caregiver_email: str
    permissions: Optional[Dict[str, bool]] = None


class CaregiverResponse(BaseModel):
    id: str
    child_id: str
    primary_user_id: str
    caregiver_user_id: str
    permissions: Dict[str, bool]
    status: str
    invited_at: datetime
    responded_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 