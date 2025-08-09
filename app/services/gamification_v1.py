from __future__ import annotations

from datetime import datetime, date, timedelta
from typing import Dict, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, case, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError
import logging
import uuid

from app.models.child import Child
from app.models.meal import Meal
from app.models.gamification import GamPointsLedger, GamDailyScore, GamStreak


def _gm_module():
    """Lazily import gamification models; return module or None if unavailable."""
    try:
        from app.models import gamification as gm
        return gm
    except Exception:
        return None


def _calc_age_months(dob: date) -> int:
    today = datetime.utcnow().date()
    months = (today.year - dob.year) * 12 + (today.month - dob.month)
    if today.day < dob.day:
        months -= 1
    return max(0, months)


def _targets_for_age_region(age_months: int, region: str) -> Dict[str, float]:
    # Placeholder bands; align with nutrition.routes mapping
    if age_months <= 12:
        return {"calories": 700, "protein_g": 11, "iron_mg": 11, "vitamin_d_iu": 400}
    if age_months <= 36:
        return {
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
    return {
        "calories": 1200,
        "protein_g": 19,
        "fiber_g": 17,
        "iron_mg": 10,
        "calcium_mg": 1000,
        "vitamin_c_mg": 25,
        "zinc_mg": 5,
    }


def _totals_for_day(db: Session, user_id: str, child_id: str, day: date) -> Dict[str, float]:
    row = db.query(
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
        Meal.user_id == user_id,
        func.coalesce(Meal.meal_date, func.date(Meal.meal_time)) == day,
    ).one()
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
    return totals


def compute_daily_score(db: Session, user_id: str, child_id: str, day: date) -> Dict:
    child = db.query(Child).filter(Child.id == child_id, Child.user_id == user_id).first()
    if not child:
        raise ValueError("child not found or unauthorized")
    age_months = _calc_age_months(child.date_of_birth)
    targets = _targets_for_age_region(age_months, child.region or "US")
    totals = _totals_for_day(db, user_id, child_id, day)

    weights = {
        "calories": 25,
        "protein_g": 25,
        "iron_mg": 15,
        "calcium_mg": 15,
        "vitamin_c_mg": 10,
        "fiber_g": 10,
    }
    component_scores: Dict[str, int] = {}
    total_score = 0
    for key, weight in weights.items():
        tgt = targets.get(key)
        act = totals.get(key)
        if tgt and act is not None and tgt > 0:
            frac = min(act / tgt, 1.0)
            pts = int(round(frac * weight))
        else:
            pts = 0
        component_scores[key] = pts
        total_score += pts

    # upsert into gam_daily_score
    gm = _gm_module()
    try:
        if gm and hasattr(gm, "GamDailyScore"):
            GDS = gm.GamDailyScore
            existing = db.query(GDS).filter(
                GDS.user_id == user_id,
                GDS.child_id == child_id,
                GDS.date == day,
            ).first()
            if not existing:
                existing = GDS(user_id=user_id, child_id=child_id, date=day)
                db.add(existing)
            existing.score = total_score
            existing.components_json = component_scores
            db.commit()
            logging.getLogger("tinytummy").info("[gam] upsert_daily_score user=%s child=%s day=%s score=%s", user_id, child_id, day, total_score)
    except SQLAlchemyError:
        db.rollback()
        logging.getLogger("tinytummy").exception("[gam] WRITE_FAIL daily_score user=%s child=%s day=%s", user_id, child_id, day)
    return {"score": total_score, "components": component_scores}


def update_streak(db: Session, user_id: str, child_id: str, day: date) -> Dict:
    gm = _gm_module()
    try:
        GS = gm.GamStreak if gm and hasattr(gm, "GamStreak") else None
        streak = db.query(GS).filter(GS.user_id == user_id, GS.child_id == child_id).first() if GS else None
        if not streak:
            if GS:
                streak = GS(user_id=user_id, child_id=child_id, current_length=0, best_length=0)
            db.add(streak)

        # Active day if any meal exists
        has_any = (
            db.query(Meal.id)
            .filter(
                Meal.user_id == user_id,
                Meal.child_id == child_id,
                func.coalesce(Meal.meal_date, func.date(Meal.meal_time)) == day,
            )
            .limit(1)
            .first()
            is not None
        )

        if has_any:
            if streak.last_active_date == day - timedelta(days=1):
                streak.current_length += 1
            elif streak.last_active_date == day:
                streak.current_length = streak.current_length or 1
            else:
                streak.current_length = 1
            streak.last_active_date = day
            if streak.current_length > streak.best_length:
                streak.best_length = streak.current_length
        db.commit()
        logging.getLogger("tinytummy").info("[gam] streak", extra={"child_id": child_id, "day": day.isoformat(), "current": streak.current_length if streak else 0, "best": streak.best_length if streak else 0, "last_active_date": streak.last_active_date.isoformat() if streak and streak.last_active_date else None})
        return {"current": streak.current_length if streak else 0, "best": streak.best_length if streak else 0}
    except SQLAlchemyError:
        db.rollback()
        # Fallback ephemeral streak: 1 if any meal exists today, else 0
        has_any = (
            db.query(Meal.id)
            .filter(
                Meal.user_id == user_id,
                Meal.child_id == child_id,
                func.coalesce(Meal.meal_date, func.date(Meal.meal_time)) == day,
            )
            .limit(1)
            .first()
            is not None
        )
        return {"current": 1 if has_any else 0, "best": 1 if has_any else 0}


def _insert_points_once(db: Session, user_id: str, child_id: str, day: date, points: int, reason: str) -> int:
    gm = _gm_module()
    try:
        GPL = gm.GamPointsLedger if gm and hasattr(gm, "GamPointsLedger") else None
        exists = db.query(GPL).filter(
            GPL.user_id == user_id,
            GPL.child_id == child_id,
            GPL.date == day,
            GPL.reason == reason,
        ).first() if GPL else None
        if exists:
            return 0
        if GPL:
            db.add(GPL(user_id=user_id, child_id=child_id, date=day, points=points, reason=reason))
        db.commit()
        logging.getLogger("tinytummy").info("[gam] points_insert user=%s child=%s day=%s reason=%s points=%s", user_id, child_id, day, reason, points)
        return points
    except SQLAlchemyError:
        db.rollback()
        logging.getLogger("tinytummy").exception("[gam] WRITE_FAIL points_insert user=%s child=%s day=%s reason=%s", user_id, child_id, day, reason)
        return points


def award_points(db: Session, user_id: str, child_id: str, day: date, daily_score: int) -> tuple[int, list[str]]:
    awarded = 0
    reasons: list[str] = []
    got = _insert_points_once(db, user_id, child_id, day, 10, "base")
    if got:
        awarded += got
        reasons.append("base")
    if daily_score >= 70:
        got = _insert_points_once(db, user_id, child_id, day, 10, "score70")
        if got:
            awarded += got
            reasons.append("score70")
    if daily_score >= 90:
        got = _insert_points_once(db, user_id, child_id, day, 20, "score90")
        if got:
            awarded += got
            reasons.append("score90")
    logging.getLogger("tinytummy").info("[gam] points_awarded user=%s child=%s day=%s reasons=%s points_awarded_today=%s", user_id, child_id, day, reasons, awarded)
    return awarded, reasons


def _get_or_create_badge(db: Session, name: str, badge_type: BadgeType) -> Badge:
    gm = _gm_module()
    try:
        Badge = gm.Badge if gm and hasattr(gm, "Badge") else None
        if not Badge:
            raise SQLAlchemyError("Badge model missing")
        b = db.query(Badge).filter(Badge.name == name).first()
        if b:
            return b
        b = Badge(name=name, description=name.replace("_", " ").title(), badge_type=badge_type, criteria={})
        db.add(b)
        db.commit()
        logging.getLogger("tinytummy").debug("[gam] maybe_award_badges done", extra={"child_id": child_id})
        return b
    except SQLAlchemyError:
        db.rollback()
        # If badges table missing, return a stub not persisted
        class _Stub:
            id = None
        return _Stub()


def maybe_award_badges(db: Session, user_id: str, child_id: str, day: date, daily_score: int, streak: Dict):
    gm = _gm_module()
    try:
        UserBadge = gm.UserBadge if gm and hasattr(gm, "UserBadge") else None
        BadgeType = gm.BadgeType if gm and hasattr(gm, "BadgeType") else None
        # starter_chef: first meal ever for this child
        first_meal = (
            db.query(Meal.id)
            .filter(Meal.user_id == user_id, Meal.child_id == child_id)
            .order_by(Meal.created_at.asc())
            .limit(1)
            .first()
        )
        if first_meal and streak.get("current", 0) == 1:
            if BadgeType:
                b = _get_or_create_badge(db, "starter_chef", BadgeType.MILESTONE)
                if UserBadge and getattr(b, "id", None) is not None and not db.query(UserBadge).filter(UserBadge.user_id == user_id, UserBadge.badge_id == b.id).first():
                    db.add(UserBadge(user_id=user_id, badge_id=b.id))

        if BadgeType and streak.get("best", 0) >= 7:
            b = _get_or_create_badge(db, "seven_day_strong", BadgeType.STREAK)
            if UserBadge and getattr(b, "id", None) is not None and not db.query(UserBadge).filter(UserBadge.user_id == user_id, UserBadge.badge_id == b.id).first():
                db.add(UserBadge(user_id=user_id, badge_id=b.id))

        if BadgeType and daily_score >= 90:
            b = _get_or_create_badge(db, "perfect_day", BadgeType.ACHIEVEMENT)
            if UserBadge and getattr(b, "id", None) is not None and not db.query(UserBadge).filter(UserBadge.user_id == user_id, UserBadge.badge_id == b.id).first():
                db.add(UserBadge(user_id=user_id, badge_id=b.id))
        db.commit()
    except SQLAlchemyError:
        db.rollback()


def recompute_for_day(db: Session, user_id: str, child_id: str, day: date) -> Dict:
    logger = logging.getLogger("tinytummy")
    # Normalize IDs to UUID
    try:
        user_uuid = user_id if isinstance(user_id, uuid.UUID) else uuid.UUID(str(user_id))
    except Exception:
        user_uuid = user_id
    try:
        child_uuid = child_id if isinstance(child_id, uuid.UUID) else uuid.UUID(str(child_id))
    except Exception:
        child_uuid = child_id

    logger.info("[meals] recompute gamification user=%s child=%s day=%s", user_uuid, child_uuid, day)

    # Active-day detection (any meal exists for the date)
    has_any = (
        db.query(Meal.id)
        .filter(
            Meal.user_id == user_uuid,
            Meal.child_id == child_uuid,
            func.coalesce(Meal.meal_date, func.date(Meal.meal_time)) == day,
        )
        .limit(1)
        .first()
        is not None
    )
    logger.info("[gam] active_today user=%s child=%s day=%s active=%s", user_id, child_id, day, has_any)

    # Calculate daily score (read-only compute)
    try:
        daily = compute_daily_score(db, user_uuid, child_uuid, day)
    except Exception:
        logger.exception("[gam] WRITE_FAIL daily_score user=%s child=%s day=%s", user_uuid, child_uuid, day)
        daily = {"score": 0, "components": {}}

    # Upsert daily score (Core UPSERT)
    try:
        score_val = int(daily.get("score", 0))
        stmt = insert(GamDailyScore.__table__).values(
            user_id=user_uuid, child_id=child_uuid, date=day, score=score_val
        ).on_conflict_do_update(
            index_elements=["user_id", "child_id", "date"],
            set_={"score": score_val}
        )
        res = db.execute(stmt)
        db.flush(); db.commit()
        logger.info("[gam] upsert_daily_score rowcount=%s", getattr(res, "rowcount", None))
        rb = db.query(GamDailyScore.score).filter(
            GamDailyScore.user_id == user_uuid,
            GamDailyScore.child_id == child_uuid,
            GamDailyScore.date == day,
        ).scalar()
        logger.info("[gam] daily_score_readback score=%s", rb)
    except Exception:
        db.rollback()
        logger.exception("[gam] WRITE_FAIL daily_score user=%s child=%s day=%s", user_uuid, child_uuid, day)
        rb = 0

    # Points inserts (idempotent UPSERT do-nothing)
    points_awarded = 0
    reasons = []
    try:
        for reason, pts, cond in [("base", 10, True), ("score70", 10, rb >= 70), ("score90", 20, rb >= 90)]:
            if not cond:
                continue
            stmt = insert(GamPointsLedger.__table__).values(
                user_id=user_uuid, child_id=child_uuid, date=day, reason=reason, points=pts
            ).on_conflict_do_nothing(index_elements=["user_id", "child_id", "date", "reason"])
            res = db.execute(stmt)
            db.flush(); db.commit()
            logger.info("[gam] points_insert rowcount=%s reason=%s points=%s", getattr(res, "rowcount", None), reason, pts)
            if getattr(res, "rowcount", 0):
                points_awarded += pts
                reasons.append(reason)
    except Exception:
        db.rollback()
        logger.exception("[gam] WRITE_FAIL points user=%s child=%s day=%s", user_uuid, child_uuid, day)

    # Points readback (same session)
    try:
        today_sum = db.query(func.coalesce(func.sum(GamPointsLedger.points), 0)).filter(
            GamPointsLedger.user_id == user_uuid,
            GamPointsLedger.child_id == child_uuid,
            GamPointsLedger.date == day,
        ).scalar()
        total_sum = db.query(func.coalesce(func.sum(GamPointsLedger.points), 0)).filter(
            GamPointsLedger.user_id == user_uuid,
            GamPointsLedger.child_id == child_uuid,
        ).scalar()
        logger.info("[gam] points_readback user=%s child=%s day=%s today=%s total=%s", user_uuid, child_uuid, day, today_sum, total_sum)
    except Exception:
        logger.exception("[gam] READBACK_FAIL points")

    # Streak upsert
    try:
        # Determine new values
        existing = db.query(GamStreak).filter(GamStreak.user_id == user_uuid, GamStreak.child_id == child_uuid).first()
        last_active = existing.last_active_date if existing else None
        if has_any:
            if last_active == (day - timedelta(days=1)):
                new_current = (existing.current_length if existing else 0) + 1
            elif last_active == day:
                new_current = existing.current_length if existing else 1
            else:
                new_current = 1
            new_best = max(existing.best_length if existing else 0, new_current)
        else:
            new_current = existing.current_length if existing else 0
            new_best = existing.best_length if existing else 0

        stmt = insert(GamStreak.__table__).values(
            user_id=user_uuid, child_id=child_uuid,
            current_length=new_current, best_length=new_best, last_active_date=day if has_any else last_active
        ).on_conflict_do_update(
            index_elements=["user_id", "child_id"],
            set_={"current_length": new_current, "best_length": new_best, "last_active_date": (day if has_any else last_active)}
        )
        res = db.execute(stmt)
        db.flush(); db.commit()
        logger.info("[gam] upsert_streak rowcount=%s", getattr(res, "rowcount", None))
        rb_st = db.query(GamStreak.current_length, GamStreak.best_length, GamStreak.last_active_date).filter(
            GamStreak.user_id == user_uuid, GamStreak.child_id == child_uuid
        ).first()
        if rb_st:
            logger.info("[gam] streak_readback current=%s best=%s last_active=%s", rb_st[0], rb_st[1], rb_st[2])
    except Exception:
        db.rollback()
        logger.exception("[gam] WRITE_FAIL streak user=%s child=%s day=%s", user_uuid, child_uuid, day)

    return {"score": daily["score"], "components": daily["components"], "streak": {"current": new_current if has_any else 0, "best": new_best if has_any else 0}, "points_awarded_today": points_awarded}


