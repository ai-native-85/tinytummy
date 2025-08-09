from fastapi import APIRouter, Depends, HTTPException, status, Query
from datetime import datetime, date as date_cls
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.auth.jwt import get_current_user
from sqlalchemy.exc import SQLAlchemyError
import importlib
from sqlalchemy import func as sfunc

router = APIRouter(prefix="/gamification", tags=["Gamification"])


@router.get("/ping")
def gam_ping():
    return {"ok": True, "module": "gamification"}


@router.get("/{user_id}")
def get_gamification(
    user_id: str,
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get gamification data for a user"""
    from app.models.gamification import Gamification
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


@router.get("/badges")
def get_badges(
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all available badges"""
    from app.models.gamification import Badge
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
    from app.services.gamification_v1 import recompute_for_day
    from app.models.child import Child
    child = db.query(Child).filter(Child.id == child_id, Child.user_id == current_user_id).first()
    if not child:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Child not found")
    try:
        day = datetime.fromisoformat(date).date()
    except Exception:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid date format")

    out = recompute_for_day(db, current_user_id, child_id, day)

    # Points today/total and streak/badges; prefer persisted reads (fast path)
    try:
        gm = importlib.import_module("app.models.gamification")
    except Exception:
        gm = None

    GamPointsLedger = getattr(gm, "GamPointsLedger", None) if gm else None
    GamStreak = getattr(gm, "GamStreak", None) if gm else None
    UserBadge = getattr(gm, "UserBadge", None) if gm else None
    Badge = getattr(gm, "Badge", None) if gm else None
    GamDailyScore = getattr(gm, "GamDailyScore", None) if gm else None

    # Try to load daily_score from table; if absent, compute once and then read
    score_payload = None
    if GamDailyScore is not None:
        try:
            ds = db.query(GamDailyScore).filter(
                GamDailyScore.user_id == current_user_id,
                GamDailyScore.child_id == child_id,
                GamDailyScore.date == day,
            ).first()
            if ds:
                score_payload = {"score": ds.score or 0, "components": ds.components_json or {}}
        except SQLAlchemyError:
            score_payload = None
    if score_payload is None:
        # compute-and-persist once
        try:
            from app.services.gamification_v1 import recompute_for_day as _recompute
            out = _recompute(db, current_user_id, child_id, day)
            score_payload = {"score": out["score"], "components": out["components"]}
        except Exception:
            score_payload = {"score": 0, "components": {}}

    # points_today
    if GamPointsLedger is not None:
        try:
            points_today = db.query(sfunc.coalesce(sfunc.sum(GamPointsLedger.points), 0)).filter(
                GamPointsLedger.user_id == current_user_id,
                GamPointsLedger.child_id == child_id,
                GamPointsLedger.date == day,
            ).scalar() or 0
        except SQLAlchemyError:
            points_today = 0
    else:
        points_today = 0

    # points_total
    if GamPointsLedger is not None:
        try:
            points_total = db.query(sfunc.coalesce(sfunc.sum(GamPointsLedger.points), 0)).filter(
                GamPointsLedger.user_id == current_user_id,
                GamPointsLedger.child_id == child_id,
            ).scalar() or 0
        except SQLAlchemyError:
            points_total = 0
    else:
        points_total = 0

    # streak
    if GamStreak is not None:
        try:
            streak = db.query(GamStreak).filter(GamStreak.user_id == current_user_id, GamStreak.child_id == child_id).first()
            current_len = streak.current_length if streak else 0
            best_len = streak.best_length if streak else 0
        except SQLAlchemyError:
            current_len = 0
            best_len = 0
    else:
        current_len = 0
        best_len = 0

    # badges
    if UserBadge is not None and Badge is not None:
        try:
            earned = db.query(UserBadge, Badge).join(Badge, UserBadge.badge_id == Badge.id).filter(UserBadge.user_id == current_user_id).all()
            badges = [{"key": b.name, "earned_on": ub.earned_at.isoformat()} for ub, b in earned]
        except SQLAlchemyError:
            badges = []
    else:
        badges = []

    return {
      "date": str(day),
      "daily_score": score_payload,
      "streak": {"current": current_len, "best": best_len},
      "points_today": points_today,
      "points_total": points_total,
      "badges": badges,
      "active_challenge": None
    }