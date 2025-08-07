from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.gamification import GamificationResponse, BadgeResponse
from app.models.gamification import Gamification, Badge
from app.auth.jwt import get_current_user

router = APIRouter(prefix="/gamification", tags=["Gamification"])


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