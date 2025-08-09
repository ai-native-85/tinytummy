from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.meal import MealCreate, MealPatch, MealResponse, MealTrendResponse
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


@router.get("/recent/{child_id}")
def get_recent_meals(
    child_id: str,
    limit: int = DEFAULT_MEAL_LIMIT,
    before: str | None = None,
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return recent meals for a child, sorted by meal_time desc, with optional pagination via before (exclusive)."""
    from app.models.child import Child
    from app.models.meal import Meal
    # Ownership
    child = db.query(Child).filter(Child.id == child_id, Child.user_id == current_user_id).first()
    if not child:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Child not found")

    q = db.query(Meal).filter(Meal.child_id == child_id, Meal.user_id == current_user_id)
    if before:
        try:
            from datetime import datetime as _dt
            from dateutil import parser as _p
            ts = _p.isoparse(before) if not isinstance(before, str) else _p.isoparse(before)
        except Exception:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid before timestamp")
        q = q.filter(Meal.meal_time < ts)
    rows = q.order_by(Meal.meal_time.desc()).limit(max(1, min(100, int(limit)))).all()
    out = []
    for m in rows:
        out.append({
            "id": str(m.id),
            "meal_time": m.meal_time,
            "meal_date": getattr(m, "meal_date", None),
            "meal_type": m.meal_type,
            "description": getattr(m, "notes", None),
            "calories": float(m.calories) if m.calories is not None else None,
            "protein_g": float(m.protein_g) if m.protein_g is not None else None,
            "fiber_g": float(m.fiber_g) if m.fiber_g is not None else None,
            "iron_mg": float(m.iron_mg) if m.iron_mg is not None else None,
            "calcium_mg": float(m.calcium_mg) if m.calcium_mg is not None else None,
            "vitamin_c_mg": float(m.vitamin_c_mg) if m.vitamin_c_mg is not None else None,
            "vitamin_d_iu": float(m.vitamin_d_iu) if m.vitamin_d_iu is not None else None,
            "zinc_mg": float(m.zinc_mg) if m.zinc_mg is not None else None,
        })
    return out

@router.get("/trends/{child_id}")
def get_meal_trends(
    child_id: str,
    days: int = DEFAULT_TREND_DAYS,
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get nutrition trends for a child (last N days)."""
    from datetime import timedelta
    days = max(1, min(30, int(days)))
    end_date = datetime.now(tz=timezone.utc).date()
    start_date = end_date - timedelta(days=days - 1)

    # Ownership check via child
    from app.models.child import Child
    child = db.query(Child).filter(Child.id == child_id, Child.user_id == current_user_id).first()
    if not child:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Child not found")

    # Aggregate nutrients per day
    from app.models.meal import Meal
    from sqlalchemy import func as sfunc
    rows = db.query(
        Meal.meal_date.label("d"),
        sfunc.sum(Meal.calories).label("calories"),
        sfunc.sum(Meal.protein_g).label("protein_g"),
        sfunc.sum(Meal.fiber_g).label("fiber_g"),
        sfunc.sum(Meal.iron_mg).label("iron_mg"),
        sfunc.sum(Meal.calcium_mg).label("calcium_mg"),
        sfunc.sum(Meal.vitamin_c_mg).label("vitamin_c_mg"),
        sfunc.sum(Meal.vitamin_d_iu).label("vitamin_d_iu"),
        sfunc.sum(Meal.zinc_mg).label("zinc_mg"),
        sfunc.count(Meal.id).label("cnt")
    ).filter(
        Meal.child_id == child_id,
        Meal.user_id == current_user_id,
        Meal.meal_date >= start_date,
        Meal.meal_date <= end_date,
    ).group_by(Meal.meal_date).all()
    by_day = {r.d: r for r in rows if r.d}

    # Prefer saved scores
    try:
        from app.models.gamification import GamDailyScore
        scores = db.query(GamDailyScore.date, GamDailyScore.score).filter(
            GamDailyScore.user_id == current_user_id,
            GamDailyScore.child_id == child_id,
            GamDailyScore.date >= start_date,
            GamDailyScore.date <= end_date,
        ).all()
        score_map = {d: s for d, s in scores}
    except Exception:
        score_map = {}

    out = []
    cur = start_date
    while cur <= end_date:
        r = by_day.get(cur)
        totals = {}
        if r:
            for k in ["calories","protein_g","fiber_g","iron_mg","calcium_mg","vitamin_c_mg","vitamin_d_iu","zinc_mg"]:
                v = getattr(r, k)
                if v is not None:
                    totals[k] = float(v)
        score = int(score_map.get(cur, 0) or 0)
        out.append({"date": cur.isoformat(), "totals": totals, "score": score})
        cur += timedelta(days=1)
    logger.info("[trends] child=%s start=%s end=%s days=%s", child_id, start_date.isoformat(), end_date.isoformat(), days)
    return {"child_id": child_id, "start_date": start_date.isoformat(), "end_date": end_date.isoformat(), "days": out}

@router.patch("/{meal_id}", response_model=MealResponse)
def edit_meal(
    meal_id: str,
    payload: MealPatch,
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from app.models.meal import Meal
    meal = db.query(Meal).filter(Meal.id == meal_id, Meal.user_id == current_user_id).first()
    if not meal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meal not found")
    old_day = getattr(meal, "meal_date", None) or meal.meal_time.date()
    # Apply partial updates
    import dateutil.parser
    data = payload.model_dump(exclude_unset=True)
    if "meal_time" in data:
        try:
            meal.meal_time = dateutil.parser.isoparse(data["meal_time"]) if isinstance(data["meal_time"], str) else data["meal_time"]
        except Exception:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid meal_time")
    if "meal_type" in data:
        meal.meal_type = str(data["meal_type"]).lower()
    if "raw_input" in data:
        meal.raw_input = data["raw_input"]
    if "description" in data:
        meal.notes = data["description"]
    db.commit(); db.refresh(meal)
    new_day = getattr(meal, "meal_date", None) or meal.meal_time.date()
    try:
        logger.info("[meals] patch meal_id=%s old_day=%s new_day=%s recompute=%s", meal_id, old_day, new_day, [old_day] + ([new_day] if new_day != old_day else []))
        recompute_for_day(db, current_user_id, str(meal.child_id), old_day)
        if new_day != old_day:
            recompute_for_day(db, current_user_id, str(meal.child_id), new_day)
    except Exception:
        logger.warning("[meals] recompute after edit failed", exc_info=True)
    # Attach affected_dates for FE cache invalidation
    try:
        ad = sorted({str(old_day), str(new_day)})
    except Exception:
        ad = list({str(old_day), str(new_day)})
    obj = meal
    try:
        # If meal is a SQLAlchemy model, enrich via __dict__ copy for response_model
        data = MealResponse.model_validate(meal).model_dump()
        data["affected_dates"] = ad
        return data
    except Exception:
        # Fallback: add attribute dynamically
        setattr(obj, "affected_dates", ad)
        return obj

@router.delete("/{meal_id}")
def delete_meal(
    meal_id: str,
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from app.models.meal import Meal
    meal = db.query(Meal).filter(Meal.id == meal_id, Meal.user_id == current_user_id).first()
    if not meal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meal not found")
    day = getattr(meal, "meal_date", None) or meal.meal_time.date()
    child_id = str(meal.child_id)
    db.delete(meal); db.commit()
    try:
        logger.info("[meals] delete meal_id=%s day=%s recompute=true", meal_id, day)
        recompute_for_day(db, current_user_id, child_id, day)
    except Exception:
        logger.warning("[meals] recompute after delete failed", exc_info=True)
    return {"deleted": True, "id": meal_id}


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
            # After each commit, recompute for that meal's date (UTC date part)
            meal_time = getattr(meal, "meal_time", None) or datetime.now(tz=timezone.utc)
            try:
                meal_time_utc = meal_time.astimezone(timezone.utc)
            except Exception:
                meal_time_utc = meal_time
            meal_day = getattr(meal, "meal_date", None) or meal_time_utc.date()
            try:
                logger.info(
                    "[meals] recompute gamification",
                    extra={
                        "child_id": str(meal.child_id),
                        "meal_time": meal_time_utc.isoformat() if hasattr(meal_time_utc, "isoformat") else str(meal_time_utc),
                        "meal_date_used": meal_day.isoformat(),
                    },
                )
                recompute_for_day(db, current_user_id, str(meal.child_id), meal_day)
            except Exception:
                logger.warning("[meals] recompute failed for batch item", exc_info=True)
        except Exception as e:
            # Log error but continue with other meals
            continue
    
    return sync_response(synced_count=len(synced_meals), total_count=len(meals_data)) 