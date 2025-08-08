from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError
import logging
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.child import ChildCreate, ChildUpdate, ChildResponse
from app.models.child import Child
from app.auth.jwt import get_current_user
from app.models.user import User
from app.utils.constants import (
    CHILD_NOT_FOUND_ERROR, 
    FEATURE_MULTIPLE_CHILDREN,
    PREMIUM_FEATURE_ERROR,
    FREE_TIER_CHILD_LIMIT
)

router = APIRouter(prefix="/children", tags=["Children"])


# Accept both /children and /children/ to avoid 307 redirects from trailing slash normalization
@router.post("", response_model=ChildResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=ChildResponse, status_code=status.HTTP_201_CREATED)
def create_child(
    child_data: ChildCreate,
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new child profile"""
    logger = logging.getLogger(__name__)
    try:
        # Log safe payload snapshot
        logger.info("Create child called", extra={
            "user_id": current_user_id,
            "payload_keys": list(child_data.model_dump(exclude_none=True).keys())
        })

        # Check subscription tier for multiple children
        user = db.query(User).filter(User.id == current_user_id).first()
        if user.subscription_tier == "free":
            existing_children = db.query(Child).filter(Child.user_id == current_user_id).count()
            if existing_children >= FREE_TIER_CHILD_LIMIT:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=PREMIUM_FEATURE_ERROR.format(feature=FEATURE_MULTIPLE_CHILDREN)
                )

        payload = child_data.model_dump(exclude_none=True)
        # Ensure gender stored consistently in lowercase (validated already)
        if payload.get("gender"):
            payload["gender"] = payload["gender"].lower()

        db_child = Child(**payload, user_id=current_user_id)
        db.add(db_child)
        db.commit()
        db.refresh(db_child)
        return db_child
    except ValidationError:
        logger.exception("Validation error in /children")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid child payload")
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unhandled error in /children")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal error creating child")


@router.get("/", response_model=List[ChildResponse])
def get_children(
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all children for current user"""
    children = db.query(Child).filter(Child.user_id == current_user_id).all()
    return children


@router.get("/{child_id}", response_model=ChildResponse)
def get_child(
    child_id: str,
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific child by ID"""
    child = db.query(Child).filter(
        Child.id == child_id,
        Child.user_id == current_user_id
    ).first()
    
    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=CHILD_NOT_FOUND_ERROR
        )
    
    return child


@router.put("/{child_id}", response_model=ChildResponse)
def update_child(
    child_id: str,
    child_data: ChildUpdate,
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a child profile"""
    child = db.query(Child).filter(
        Child.id == child_id,
        Child.user_id == current_user_id
    ).first()
    
    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=CHILD_NOT_FOUND_ERROR
        )
    
    # Update only provided fields
    update_data = child_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(child, field, value)
    
    db.commit()
    db.refresh(child)
    return child


@router.delete("/{child_id}")
def delete_child(
    child_id: str,
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a child profile"""
    child = db.query(Child).filter(
        Child.id == child_id,
        Child.user_id == current_user_id
    ).first()
    
    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=CHILD_NOT_FOUND_ERROR
        )
    
    db.delete(child)
    db.commit()
    return {"message": "Child deleted successfully"} 