from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime, date


class PlanCreate(BaseModel):
    child_id: str
    plan_name: str
    start_date: date
    end_date: date


class PlanGenerateRequest(BaseModel):
    child_id: str
    plan_name: str


class PlanResponse(BaseModel):
    id: str
    child_id: str
    user_id: str
    plan_name: str
    start_date: date
    end_date: date
    plan_data: Dict[str, Any]
    gpt_generation_prompt: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 