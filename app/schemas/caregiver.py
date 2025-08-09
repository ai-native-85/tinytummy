from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class CaregiverInviteRequest(BaseModel):
    child_id: str
    invitee_email: str
    role: Optional[str] = "viewer"


class CaregiverInviteResponse(BaseModel):
    id: str
    child_id: str
    inviter_user_id: str
    invitee_email: str
    role: str
    status: str
    token: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CaregiverAccessResponse(BaseModel):
    id: str
    child_id: str
    user_id: str
    role: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True