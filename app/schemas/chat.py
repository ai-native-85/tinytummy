from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import UUID4


class ChatSessionCreate(BaseModel):
    child_id: Optional[UUID4] = None
    session_name: Optional[str] = None


class ChatMessageCreate(BaseModel):
    role: str
    content: str


class ChatQueryRequest(BaseModel):
    user_input: str
    child_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    metadata: Optional[Dict[str, Any]] = None


class ChatSessionResponse(BaseModel):
    id: str
    user_id: str
    child_id: Optional[str] = None
    session_name: Optional[str] = None
    context_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 