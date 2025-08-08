from pydantic import BaseModel
from typing import Dict, Optional


class NutritionTargetsResponse(BaseModel):
    age_months: int
    region: str
    targets: Dict[str, float]


class DailyTotalsResponse(BaseModel):
    date: str
    totals: Dict[str, float]


