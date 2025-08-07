"""Gamification service for streaks, badges, and rewards"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status
from app.models.gamification import Gamification, Badge, UserBadge
from app.models.meal import Meal
from app.schemas.gamification import GamificationResponse, BadgeResponse


class GamificationService:
    def __init__(self, db: Session):
        self.db = db

    def update_user_progress(self, user_id: str, child_id: str) -> Gamification:
        """Update user's gamification progress based on recent meals"""
        
        # Get or create gamification record
        gamification = self.db.query(Gamification).filter(
            Gamification.user_id == user_id,
            Gamification.child_id == child_id
        ).first()
        
        if not gamification:
            gamification = Gamification(
                user_id=user_id,
                child_id=child_id,
                current_streak=0,
                longest_streak=0,
                total_meals=0,
                total_points=0,
                level=1
            )
            self.db.add(gamification)
        
        # Calculate new streak
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        
        # Check if user logged meals today and yesterday
        today_meals = self.db.query(Meal).filter(
            Meal.user_id == user_id,
            Meal.child_id == child_id,
            func.date(Meal.meal_time) == today
        ).count()
        
        yesterday_meals = self.db.query(Meal).filter(
            Meal.user_id == user_id,
            Meal.child_id == child_id,
            func.date(Meal.meal_time) == yesterday
        ).count()
        
        # Update streak
        if today_meals > 0:
            if yesterday_meals > 0:
                gamification.current_streak += 1
            else:
                gamification.current_streak = 1
        else:
            gamification.current_streak = 0
        
        # Update longest streak
        if gamification.current_streak > gamification.longest_streak:
            gamification.longest_streak = gamification.current_streak
        
        # Update total meals
        total_meals = self.db.query(Meal).filter(
            Meal.user_id == user_id,
            Meal.child_id == child_id
        ).count()
        gamification.total_meals = total_meals
        
        # Calculate points (10 points per meal + streak bonus)
        base_points = total_meals * 10
        streak_bonus = gamification.current_streak * 5
        gamification.total_points = base_points + streak_bonus
        
        # Calculate level (every 100 points = 1 level)
        gamification.level = (gamification.total_points // 100) + 1
        
        gamification.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(gamification)
        
        # Check for new badges
        self._check_and_award_badges(user_id, gamification)
        
        return gamification

    def get_user_progress(self, user_id: str, child_id: str) -> Gamification:
        """Get user's gamification progress"""
        gamification = self.db.query(Gamification).filter(
            Gamification.user_id == user_id,
            Gamification.child_id == child_id
        ).first()
        
        if not gamification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Gamification progress not found"
            )
        
        return gamification

    def get_user_badges(self, user_id: str) -> List[UserBadge]:
        """Get all badges earned by a user"""
        return self.db.query(UserBadge).filter(
            UserBadge.user_id == user_id
        ).order_by(UserBadge.earned_at.desc()).all()

    def _check_and_award_badges(self, user_id: str, gamification: Gamification):
        """Check and award badges based on user progress"""
        
        # Get all badges
        all_badges = self.db.query(Badge).all()
        
        # Get user's earned badges
        earned_badges = self.db.query(UserBadge).filter(
            UserBadge.user_id == user_id
        ).all()
        earned_badge_ids = [eb.badge_id for eb in earned_badges]
        
        # Check for new badges
        for badge in all_badges:
            if badge.id not in earned_badge_ids:
                should_award = False
                
                # Check badge criteria
                if badge.criteria_type == "meals_logged":
                    should_award = gamification.total_meals >= badge.criteria_value
                elif badge.criteria_type == "streak_days":
                    should_award = gamification.longest_streak >= badge.criteria_value
                elif badge.criteria_type == "total_points":
                    should_award = gamification.total_points >= badge.criteria_value
                elif badge.criteria_type == "level":
                    should_award = gamification.level >= badge.criteria_value
                
                if should_award:
                    # Award badge
                    user_badge = UserBadge(
                        user_id=user_id,
                        badge_id=badge.id,
                        earned_at=datetime.now()
                    )
                    self.db.add(user_badge)
        
        self.db.commit()

    def get_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get leaderboard of top users"""
        top_users = self.db.query(Gamification).order_by(
            Gamification.total_points.desc()
        ).limit(limit).all()
        
        leaderboard = []
        for i, gamification in enumerate(top_users, 1):
            leaderboard.append({
                "rank": i,
                "user_id": str(gamification.user_id),
                "child_id": str(gamification.child_id),
                "total_points": gamification.total_points,
                "level": gamification.level,
                "longest_streak": gamification.longest_streak
            })
        
        return leaderboard 