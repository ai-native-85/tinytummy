from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from app.models.gamification import BadgeType


class GamificationResponse(BaseModel):
    id: str
    user_id: str
    child_id: Optional[str] = None
    points: int
    current_streak: int
    longest_streak: int
    badges: List[Dict[str, Any]]
    level: int
    experience_points: int
    last_activity_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BadgeResponse(BaseModel):
    id: str
    name: str
    description: str
    badge_type: BadgeType
    icon_url: Optional[str] = None
    points_reward: int
    criteria: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True 