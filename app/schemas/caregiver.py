from pydantic import BaseModel, EmailStr
from typing import Optional, List, Literal
from uuid import UUID
from datetime import datetime


class CaregiverInviteRequest(BaseModel):
    child_id: UUID
    invitee_email: EmailStr
    role: Literal["viewer","editor"] = "viewer"


class CaregiverAcceptRequest(BaseModel):
    token: UUID


class CaregiverDeclineRequest(BaseModel):
    token: UUID


class CaregiverRevokeRequest(BaseModel):
    invite_id: UUID


class CaregiverResponse(BaseModel):
    id: UUID
    child_id: UUID
    user_id: UUID
    email: Optional[EmailStr] = None
    role: str
    added_at: datetime


class CaregiverInviteResponse(BaseModel):
    id: UUID
    child_id: UUID
    invitee_email: EmailStr
    role: str
    status: Literal["pending","accepted","declined","revoked"]
    token: Optional[UUID] = None
    created_at: datetime
    expires_at: Optional[datetime] = None


class CaregiverListResponse(BaseModel):
    caregivers: List[CaregiverResponse]


class CaregiverInviteListResponse(BaseModel):
    invites: List[CaregiverInviteResponse]