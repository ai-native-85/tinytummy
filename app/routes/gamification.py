from fastapi import APIRouter, Depends, HTTPException, status, Query
from datetime import datetime, date as date_cls
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.gamification import GamificationResponse, BadgeResponse
from app.models.gamification import Gamification, Badge
from app.auth.jwt import get_current_user
from app.services.gamification_v1 import recompute_for_day

router = APIRouter(prefix="/gamification", tags=["Gamification"])


@router.get("/ping")
def gam_ping():
    return {"ok": True, "module": "gamification"}


@router.get("/{user_id}", response_model=GamificationResponse)
def get_gamification(
    user_id: str,
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get gamification data for a user"""
    if user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only access own gamification data"
        )
    
    gamification = db.query(Gamification).filter(
        Gamification.user_id == current_user_id
    ).first()
    
    if not gamification:
        # Create new gamification record
        gamification = Gamification(user_id=current_user_id)
        db.add(gamification)
        db.commit()
        db.refresh(gamification)
    
    return gamification


@router.get("/badges", response_model=List[BadgeResponse])
def get_badges(
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all available badges"""
    badges = db.query(Badge).all()
    return badges 


@router.get("/summary/{child_id}")
def gamification_summary(
    child_id: str,
    date: str = Query(default=datetime.utcnow().date().isoformat()),
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Validate child ownership
    from app.models.child import Child
    child = db.query(Child).filter(Child.id == child_id, Child.user_id == current_user_id).first()
    if not child:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Child not found")
    try:
        day = datetime.fromisoformat(date).date()
    except Exception:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid date format")

    out = recompute_for_day(db, current_user_id, child_id, day)

    # Points today/total
    from app.models.gamification import GamPointsLedger, GamStreak, UserBadge, Badge
    from sqlalchemy import func as sfunc
    points_today = db.query(sfunc.coalesce(sfunc.sum(GamPointsLedger.points), 0)).filter(
        GamPointsLedger.user_id == current_user_id,
        GamPointsLedger.child_id == child_id,
        GamPointsLedger.date == day,
    ).scalar() or 0

    points_total = db.query(sfunc.coalesce(sfunc.sum(GamPointsLedger.points), 0)).filter(
        GamPointsLedger.user_id == current_user_id,
        GamPointsLedger.child_id == child_id,
    ).scalar() or 0

    streak = db.query(GamStreak).filter(GamStreak.user_id == current_user_id, GamStreak.child_id == child_id).first()
    current_len = streak.current_length if streak else 0
    best_len = streak.best_length if streak else 0

    # Earned badges (names)
    earned = db.query(UserBadge, Badge).join(Badge, UserBadge.badge_id == Badge.id).filter(UserBadge.user_id == current_user_id).all()
    badges = [{"key": b.name, "earned_on": ub.earned_at.isoformat()} for ub, b in earned]

    return {
      "date": str(day),
      "daily_score": {"score": out["score"], "components": out["components"]},
      "streak": {"current": current_len, "best": best_len},
      "points_today": points_today,
      "points_total": points_total,
      "badges": badges,
      "active_challenge": None
    }