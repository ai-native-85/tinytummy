from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime, date
from typing import Dict

from app.database import get_db
from app.auth.jwt import get_current_user
from app.schemas.nutrition import NutritionTargetsResponse, DailyTotalsResponse
from app.models.child import Child
from app.models.targets import ChildTargets
from app.models.meal import Meal
from sqlalchemy import func


router = APIRouter(prefix="/nutrition", tags=["nutrition"])


def _calc_age_months(dob: date) -> int:
    today = datetime.utcnow().date()
    months = (today.year - dob.year) * 12 + (today.month - dob.month)
    if today.day < dob.day:
        months -= 1
    return max(0, months)


@router.get("/targets/{child_id}", response_model=NutritionTargetsResponse)
def get_nutrition_targets(child_id: str, current_user_id: str = Depends(get_current_user), db: Session = Depends(get_db)):
    child = db.query(Child).filter(Child.id == child_id, Child.user_id == current_user_id).first()
    if not child:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Child not found")

    age_months = _calc_age_months(child.date_of_birth)
    region = child.region or "US"

    # Prefer per-child overrides if present
    ct = db.query(ChildTargets).filter(ChildTargets.child_id == child_id, ChildTargets.user_id == current_user_id).first()
    if ct and ct.overrides:
        return NutritionTargetsResponse(age_months=age_months, region=region, targets={k: float(v) for k, v in ct.overrides.items()})

    # Simple placeholder mapping. In a fuller version, query nutrition_guidelines table
    # for the closest matching age band by region and emit only defined keys.
    targets: Dict[str, float] = {}
    if age_months <= 12:
        targets = {
            "calories": 700,
            "protein_g": 11,
            "iron_mg": 11,
            "vitamin_d_iu": 400,
        }
    elif age_months <= 36:
        targets = {
            "calories": 1000,
            "protein_g": 13,
            "fiber_g": 14,
            "iron_mg": 7,
            "calcium_mg": 700,
            "vitamin_a_iu": 1000,
            "vitamin_c_mg": 15,
            "vitamin_d_iu": 600,
            "zinc_mg": 3,
        }
    else:
        targets = {
            "calories": 1200,
            "protein_g": 19,
            "fiber_g": 17,
            "iron_mg": 10,
            "calcium_mg": 1000,
            "vitamin_c_mg": 25,
            "zinc_mg": 5,
        }

    return NutritionTargetsResponse(age_months=age_months, region=region, targets=targets)


@router.get("/daily_totals/{child_id}", response_model=DailyTotalsResponse)
def get_daily_totals(child_id: str, date: str = Query(..., description="YYYY-MM-DD"), current_user_id: str = Depends(get_current_user), db: Session = Depends(get_db)):
    child = db.query(Child).filter(Child.id == child_id, Child.user_id == current_user_id).first()
    if not child:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Child not found")

    try:
        day = datetime.fromisoformat(date).date()
    except Exception:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid date format")

    q = db.query(
        func.sum(Meal.calories).label("calories"),
        func.sum(Meal.protein_g).label("protein_g"),
        func.sum(Meal.fiber_g).label("fiber_g"),
        func.sum(Meal.iron_mg).label("iron_mg"),
        func.sum(Meal.calcium_mg).label("calcium_mg"),
        func.sum(Meal.vitamin_a_iu).label("vitamin_a_iu"),
        func.sum(Meal.vitamin_c_mg).label("vitamin_c_mg"),
        func.sum(Meal.vitamin_d_iu).label("vitamin_d_iu"),
        func.sum(Meal.zinc_mg).label("zinc_mg"),
    ).filter(
        Meal.child_id == child_id,
        Meal.user_id == current_user_id,
        func.coalesce(Meal.meal_date, func.date(Meal.meal_time)) == day,
    )

    row = q.one()
    totals: Dict[str, float] = {}
    for k in [
        "calories",
        "protein_g",
        "fiber_g",
        "iron_mg",
        "calcium_mg",
        "vitamin_a_iu",
        "vitamin_c_mg",
        "vitamin_d_iu",
        "zinc_mg",
    ]:
        v = getattr(row, k)
        if v is not None:
            totals[k] = float(v)

    return DailyTotalsResponse(date=str(day), totals=totals)


# --- Alias router for backward-compatibility under /meals ---
meals_router = APIRouter(prefix="/meals", tags=["meals"])


@meals_router.get("/daily_totals/{child_id}", response_model=DailyTotalsResponse)
def daily_totals_alias(child_id: str, date: str = Query(..., description="YYYY-MM-DD"), current_user_id: str = Depends(get_current_user), db: Session = Depends(get_db)):
    # Delegate to original to ensure identical payloads
    return get_daily_totals(child_id=child_id, date=date, current_user_id=current_user_id, db=db)


