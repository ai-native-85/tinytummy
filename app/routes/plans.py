from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import date, timedelta
from app.database import get_db
from app.schemas.plan import PlanResponse
from app.models.plan import Plan
from app.auth.jwt import get_current_user
from app.models.child import Child

router = APIRouter(prefix="/plans", tags=["Meal Plans"])


@router.post("/21day/{child_id}", response_model=PlanResponse)
def generate_21day_plan(
    child_id: str,
    start: date = Query(..., description="YYYY-MM-DD start date"),
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate a stub 21-day plan and persist it."""
    child = db.query(Child).filter(Child.id == child_id, Child.user_id == current_user_id).first()
    if not child:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Child not found")

    end = start + timedelta(days=20)
    days = []
    for i in range(21):
        d = start + timedelta(days=i)
        days.append({
            "date": d.isoformat(),
            "meals": {
                "breakfast": {"title": "Balanced breakfast", "notes": "Protein + whole grains + fruit"},
                "lunch": {"title": "Nutritious lunch", "notes": "Veggies + protein + carbs"},
                "dinner": {"title": "Light dinner", "notes": "Veg-forward with protein"},
                "snack": {"title": "Healthy snack", "notes": "Fruit/yogurt/nuts"},
            },
            "summary": {"calories": 1000, "protein_g": 13}
        })
    plan = Plan(
        child_id=child_id,
        user_id=current_user_id,
        plan_name="21-day plan",
        start_date=start,
        end_date=end,
        plan_data={"days": days},
        is_active=True,
    )
    db.add(plan)
    db.commit(); db.refresh(plan)
    # deactivate previous plans for this child
    db.query(Plan).filter(Plan.child_id == child_id, Plan.user_id == current_user_id, Plan.id != plan.id).update({Plan.is_active: False})
    db.commit()
    return plan


@router.get("/{plan_id}", response_model=PlanResponse)
def get_plan(plan_id: str, current_user_id: str = Depends(get_current_user), db: Session = Depends(get_db)):
    plan = db.query(Plan).filter(Plan.id == plan_id, Plan.user_id == current_user_id).first()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    return plan


@router.get("/active/{child_id}", response_model=PlanResponse)
def get_active_plan(child_id: str, current_user_id: str = Depends(get_current_user), db: Session = Depends(get_db)):
    plan = db.query(Plan).filter(Plan.child_id == child_id, Plan.user_id == current_user_id, Plan.is_active == True).order_by(Plan.created_at.desc()).first()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active plan")
    return plan