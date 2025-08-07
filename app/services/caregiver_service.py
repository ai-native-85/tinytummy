"""Caregiver invitation and access management service"""

import secrets
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.caregiver import CaregiverLink
from app.models.user import User
from app.models.child import Child
from app.schemas.caregiver import CaregiverInviteRequest, CaregiverResponse


class CaregiverService:
    def __init__(self, db: Session):
        self.db = db

    def invite_caregiver(self, invite_data: CaregiverInviteRequest, primary_user_id: str) -> CaregiverLink:
        """Invite a caregiver to access a child profile"""
        
        # Verify child ownership
        child = self.db.query(Child).filter(
            Child.id == invite_data.child_id,
            Child.user_id == primary_user_id
        ).first()
        
        if not child:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Child not found"
            )
        
        # Find caregiver user by email
        caregiver_user = self.db.query(User).filter(
            User.email == invite_data.caregiver_email
        ).first()
        
        if not caregiver_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Caregiver user not found"
            )
        
        if caregiver_user.id == primary_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot invite yourself as caregiver"
            )
        
        # Check if invitation already exists
        existing_invite = self.db.query(CaregiverLink).filter(
            CaregiverLink.child_id == invite_data.child_id,
            CaregiverLink.caregiver_user_id == caregiver_user.id
        ).first()
        
        if existing_invite:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Caregiver already invited or has access"
            )
        
        # Create invitation
        caregiver_link = CaregiverLink(
            child_id=invite_data.child_id,
            primary_user_id=primary_user_id,
            caregiver_user_id=caregiver_user.id,
            permissions=invite_data.permissions or {"read": True, "write": False},
            status="pending"
        )
        
        self.db.add(caregiver_link)
        self.db.commit()
        self.db.refresh(caregiver_link)
        
        # TODO: Send email notification to caregiver
        # For now, just log the invitation
        
        return caregiver_link

    def accept_invitation(self, invitation_id: str, caregiver_user_id: str) -> CaregiverLink:
        """Accept a caregiver invitation"""
        
        invitation = self.db.query(CaregiverLink).filter(
            CaregiverLink.id == invitation_id,
            CaregiverLink.caregiver_user_id == caregiver_user_id,
            CaregiverLink.status == "pending"
        ).first()
        
        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invitation not found or already processed"
            )
        
        invitation.status = "accepted"
        invitation.responded_at = datetime.now()
        
        self.db.commit()
        self.db.refresh(invitation)
        
        return invitation

    def decline_invitation(self, invitation_id: str, caregiver_user_id: str) -> CaregiverLink:
        """Decline a caregiver invitation"""
        
        invitation = self.db.query(CaregiverLink).filter(
            CaregiverLink.id == invitation_id,
            CaregiverLink.caregiver_user_id == caregiver_user_id,
            CaregiverLink.status == "pending"
        ).first()
        
        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invitation not found or already processed"
            )
        
        invitation.status = "declined"
        invitation.responded_at = datetime.now()
        
        self.db.commit()
        self.db.refresh(invitation)
        
        return invitation

    def get_caregiver_access(self, child_id: str, user_id: str) -> List[CaregiverLink]:
        """Get caregiver access for a child"""
        
        # Verify user has access to child (either as primary or caregiver)
        access = self.db.query(CaregiverLink).filter(
            CaregiverLink.child_id == child_id,
            (CaregiverLink.primary_user_id == user_id) | (CaregiverLink.caregiver_user_id == user_id)
        ).all()
        
        if not access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No access to this child"
            )
        
        return access

    def remove_caregiver_access(self, child_id: str, caregiver_user_id: str, primary_user_id: str) -> bool:
        """Remove caregiver access to a child"""
        
        # Verify primary user owns the child
        child = self.db.query(Child).filter(
            Child.id == child_id,
            Child.user_id == primary_user_id
        ).first()
        
        if not child:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Child not found"
            )
        
        # Remove caregiver link
        caregiver_link = self.db.query(CaregiverLink).filter(
            CaregiverLink.child_id == child_id,
            CaregiverLink.caregiver_user_id == caregiver_user_id
        ).first()
        
        if not caregiver_link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Caregiver access not found"
            )
        
        self.db.delete(caregiver_link)
        self.db.commit()
        
        return True 