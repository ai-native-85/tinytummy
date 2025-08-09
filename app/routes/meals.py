from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.meal import MealCreate, MealResponse, MealTrendResponse
from app.services.meal_service import MealService
from app.auth.jwt import get_current_user
from app.utils.responses import sync_response
from app.utils.constants import DEFAULT_MEAL_LIMIT, DEFAULT_TREND_DAYS
from datetime import datetime, timezone
from app.services.gamification_v1 import recompute_for_day
import logging

router = APIRouter(prefix="/meals", tags=["Meals"])
logger = logging.getLogger("tinytummy")


@router.post("/log", response_model=MealResponse, status_code=status.HTTP_201_CREATED)
def log_meal(
    meal_data: MealCreate,
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Log a new meal with GPT-4 analysis"""
    meal_service = MealService(db)
    meal = meal_service.create_meal(meal_data, current_user_id)
    # Recompute gamification for the meal date
    meal_time = getattr(meal, "meal_time", None)
    if meal_time is None:
        meal_time = datetime.now(tz=timezone.utc)
    # Normalize to UTC date
    try:
        meal_time_utc = meal_time.astimezone(timezone.utc)
    except Exception:
        meal_time_utc = meal_time
    meal_day = getattr(meal, "meal_date", None) or meal_time_utc.date()
    try:
        logger.debug(
            "[meals] recompute gamification",
            extra={
                "child_id": str(meal.child_id),
                "meal_time": meal_time_utc.isoformat() if hasattr(meal_time_utc, "isoformat") else str(meal_time_utc),
                "meal_date_used": meal_day.isoformat(),
            },
        )
        recompute_for_day(db, current_user_id, str(meal.child_id), meal_day)
    except Exception:
        pass
    return meal


@router.get("/{child_id}", response_model=List[MealResponse])
def get_meals_by_child(
    child_id: str,
    limit: int = DEFAULT_MEAL_LIMIT,
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get meals for a specific child"""
    meal_service = MealService(db)
    meals = meal_service.get_meals_by_child(child_id, current_user_id, limit)
    return meals


@router.get("/trends/{child_id}", response_model=List[MealTrendResponse])
def get_meal_trends(
    child_id: str,
    days: int = DEFAULT_TREND_DAYS,
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get nutrition trends for a child"""
    meal_service = MealService(db)
    trends = meal_service.get_meal_trends(child_id, current_user_id, days)
    return trends


@router.post("/batch-sync")
def batch_sync_meals(
    meals_data: List[MealCreate],
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Sync multiple meals from offline storage"""
    meal_service = MealService(db)
    synced_meals = []
    
    for meal_data in meals_data:
        try:
            meal = meal_service.create_meal(meal_data, current_user_id)
            synced_meals.append(meal)
        except Exception as e:
            # Log error but continue with other meals
            continue
    
    return sync_response(synced_count=len(synced_meals), total_count=len(meals_data)) 