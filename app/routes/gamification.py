from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from datetime import datetime, date as date_cls
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.auth.jwt import get_current_user
from sqlalchemy.exc import SQLAlchemyError
import importlib
from sqlalchemy import func as sfunc, case, text

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
    db: Session = Depends(get_db),
    response: Response = None,
):
    import time
    t0 = time.perf_counter()
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

    # points combined query
    points_today = 0
    points_total = 0
    if GamPointsLedger is not None:
        try:
            row = db.query(
                sfunc.coalesce(sfunc.sum(case((GamPointsLedger.date == day, GamPointsLedger.points), else_=0)), 0).label("today"),
                sfunc.coalesce(sfunc.sum(GamPointsLedger.points), 0).label("total"),
            ).filter(
                GamPointsLedger.user_id == current_user_id,
                GamPointsLedger.child_id == child_id,
            ).one()
            points_today = int(row.today or 0)
            points_total = int(row.total or 0)
        except SQLAlchemyError:
            points_today = 0
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

    # badges omitted for performance
    badges = []

    out = {
      "date": str(day),
      "daily_score": score_payload,
      "streak": {"current": current_len, "best": best_len},
      "points_today": points_today,
      "points_total": points_total,
      "badges": badges,
      "active_challenge": None
    }
    if response is not None:
        response.headers["X-Handler-Time-ms"] = str(int((time.perf_counter() - t0) * 1000))
    return out


@router.get("/__diag", tags=["Gamification"])
def gam_diag(
    child_id: str,
    day: date_cls = Query(...),
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    import logging, uuid
    logger = logging.getLogger("tinytummy")
    # Normalize to UUID if model uses UUID
    try:
        child_uuid = str(uuid.UUID(str(child_id)))
    except Exception:
        child_uuid = str(child_id)
    try:
        user_uuid = str(uuid.UUID(str(current_user_id)))
    except Exception:
        user_uuid = str(current_user_id)
    from app.models.child import Child
    child = db.query(Child).filter(Child.id == child_uuid, Child.user_id == user_uuid).first()
    if not child:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Child not found")
    logger.info("[diag] user=%s child=%s allowed", user_uuid, child_uuid)

    out = {}
    ds = db.execute(
        text("""
        SELECT score, components_json
        FROM gam_daily_score
        WHERE user_id=:u AND child_id=:c AND date=:d
        """),
        {"u": user_uuid, "c": child_uuid, "d": day},
    ).mappings().first()
    out["daily_score_row"] = dict(ds) if ds else None

    sums = db.execute(
        text("""
        SELECT
          COALESCE(SUM(CASE WHEN date = :d THEN points ELSE 0 END), 0) AS points_today,
          COALESCE(SUM(points), 0) AS points_total
        FROM gam_points_ledger
        WHERE user_id = :u AND child_id = :c
        """),
        {"u": user_uuid, "c": child_uuid, "d": day},
    ).mappings().first()
    out["points_sums"] = dict(sums) if sums else None

    rows = db.execute(
        text("""
        SELECT date, reason, points
        FROM gam_points_ledger
        WHERE user_id=:u AND child_id=:c
        ORDER BY date ASC, reason ASC
        """),
        {"u": user_uuid, "c": child_uuid},
    ).mappings().all()
    out["points_rows"] = [dict(r) for r in rows]

    st = db.execute(
        text("""
        SELECT current_length, best_length, last_active_date
        FROM gam_streak
        WHERE user_id=:u AND child_id=:c
        """),
        {"u": user_uuid, "c": child_uuid},
    ).mappings().first()
    out["streak_row"] = dict(st) if st else None

    return out