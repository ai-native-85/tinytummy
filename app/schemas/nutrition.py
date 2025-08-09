from pydantic import BaseModel
from typing import Dict, Optional, List


class NutritionTargetsResponse(BaseModel):
    age_months: int
    region: str
    source: Dict[str, Optional[List[str]]] = {"primary": None, "fallbacks": []}
    targets: Dict[str, float]
    overrides_applied: bool = False


class DailyTotalsResponse(BaseModel):
    date: str
    totals: Dict[str, float]


