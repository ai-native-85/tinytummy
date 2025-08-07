from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.caregiver import CaregiverInviteRequest, CaregiverResponse
from app.models.caregiver import CaregiverLink
from app.models.user import User
from app.auth.jwt import get_current_user
from app.utils.constants import FEATURE_CAREGIVER, PREMIUM_FEATURE_ERROR

router = APIRouter(prefix="/caregiver", tags=["Caregiver Sharing"])


@router.post("/invite", response_model=CaregiverResponse)
def invite_caregiver(
    invite_data: CaregiverInviteRequest,
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Invite a caregiver to access a child (Premium feature)"""
    # Check premium subscription
    user = db.query(User).filter(User.id == current_user_id).first()
    if user.subscription_tier != "premium":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=PREMIUM_FEATURE_ERROR.format(feature=FEATURE_CAREGIVER)
        )
    
    # Use caregiver service
    from app.services.caregiver_service import CaregiverService
    caregiver_service = CaregiverService(db)
    
    caregiver_link = caregiver_service.invite_caregiver(invite_data, current_user_id)
    return caregiver_link


@router.get("/{child_id}/access", response_model=List[CaregiverResponse])
def get_caregiver_access(
    child_id: str,
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get caregiver access for a child"""
    from app.services.caregiver_service import CaregiverService
    caregiver_service = CaregiverService(db)
    
    return caregiver_service.get_caregiver_access(child_id, current_user_id)


@router.post("/accept/{invitation_id}")
def accept_invitation(
    invitation_id: str,
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Accept a caregiver invitation"""
    from app.services.caregiver_service import CaregiverService
    caregiver_service = CaregiverService(db)
    
    return caregiver_service.accept_invitation(invitation_id, current_user_id)


@router.post("/decline/{invitation_id}")
def decline_invitation(
    invitation_id: str,
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Decline a caregiver invitation"""
    from app.services.caregiver_service import CaregiverService
    caregiver_service = CaregiverService(db)
    
    return caregiver_service.decline_invitation(invitation_id, current_user_id)


@router.delete("/{child_id}/remove/{caregiver_user_id}")
def remove_caregiver_access(
    child_id: str,
    caregiver_user_id: str,
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove caregiver access to a child"""
    from app.services.caregiver_service import CaregiverService
    caregiver_service = CaregiverService(db)
    
    caregiver_service.remove_caregiver_access(child_id, caregiver_user_id, current_user_id)
    return {"message": "Caregiver access removed successfully"} 