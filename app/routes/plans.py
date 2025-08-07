from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.plan import PlanResponse
from app.models.plan import Plan
from app.models.user import User
from app.auth.jwt import get_current_user
from app.utils.constants import FEATURE_MEAL_PLANS, PREMIUM_FEATURE_ERROR

router = APIRouter(prefix="/plans", tags=["Meal Plans"])


@router.post("/generate", response_model=PlanResponse)
def generate_meal_plan(
    child_id: str,
    plan_name: str,
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate a 21-day meal plan (Premium feature)"""
    # Check premium subscription
    user = db.query(User).filter(User.id == current_user_id).first()
    if user.subscription_tier != "premium":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=PREMIUM_FEATURE_ERROR.format(feature=FEATURE_MEAL_PLANS)
        )
    
    # TODO: Implement GPT-4 meal plan generation
    # This would call a service to generate the plan
    raise NotImplementedError("Meal plan generation not yet implemented")


@router.get("/{child_id}", response_model=List[PlanResponse])
def get_meal_plans(
    child_id: str,
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get meal plans for a child"""
    plans = db.query(Plan).filter(
        Plan.child_id == child_id,
        Plan.user_id == current_user_id
    ).all()
    return plans 