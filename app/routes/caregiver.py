from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.caregiver import (
    CaregiverInviteRequest,
    CaregiverInviteResponse,
    CaregiverAccessResponse,
)
from app.models.caregiver_access import CaregiverInvite, ChildCaregiver
from app.models.child import Child
from app.models.user import User
from app.auth.jwt import get_current_user

router = APIRouter(prefix="/caregivers", tags=["Caregivers"])


@router.get("/{child_id}", response_model=List[CaregiverAccessResponse])
def list_caregivers(child_id: str, current_user_id: str = Depends(get_current_user), db: Session = Depends(get_db)):
    # owner check
    child = db.query(Child).filter(Child.id == child_id, Child.user_id == current_user_id).first()
    if not child:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Child not found")
    rows = db.query(ChildCaregiver).filter(ChildCaregiver.child_id == child_id).all()
    return rows


@router.get("/invites/{child_id}")
def list_invites(child_id: str, current_user_id: str = Depends(get_current_user), db: Session = Depends(get_db)):
    child = db.query(Child).filter(Child.id == child_id, Child.user_id == current_user_id).first()
    if not child:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Child not found")
    rows = db.query(CaregiverInvite).filter(CaregiverInvite.child_id == child_id).all()
    return [{"id": str(r.id), "invitee_email": r.invitee_email, "role": r.role, "status": r.status, "token": str(r.token)} for r in rows]


@router.post("/invite", response_model=CaregiverInviteResponse)
def invite_caregiver(req: CaregiverInviteRequest, current_user_id: str = Depends(get_current_user), db: Session = Depends(get_db)):
    # owner check
    child = db.query(Child).filter(Child.id == req.child_id, Child.user_id == current_user_id).first()
    if not child:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Child not found")
    # upsert pending
    existing = db.query(CaregiverInvite).filter(CaregiverInvite.child_id == req.child_id, CaregiverInvite.invitee_email == req.invitee_email, CaregiverInvite.status == "pending").first()
    if existing:
        inv = existing
    else:
        inv = CaregiverInvite(child_id=req.child_id, inviter_user_id=current_user_id, invitee_email=req.invitee_email, role=req.role or "viewer")
        db.add(inv); db.commit(); db.refresh(inv)
    return inv


@router.post("/accept")
def accept_invite(payload: dict, current_user_id: str = Depends(get_current_user), db: Session = Depends(get_db)):
    token = payload.get("token")
    if not token:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="token required")
    inv = db.query(CaregiverInvite).filter(CaregiverInvite.token == token, CaregiverInvite.status == "pending").first()
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found")
    # create link
    exists = db.query(ChildCaregiver).filter(ChildCaregiver.child_id == inv.child_id, ChildCaregiver.user_id == current_user_id).first()
    if not exists:
        db.add(ChildCaregiver(child_id=inv.child_id, user_id=current_user_id, role=inv.role))
    inv.status = "accepted"
    db.commit()
    return {"accepted": True}


@router.post("/decline")
def decline_invite(payload: dict, current_user_id: str = Depends(get_current_user), db: Session = Depends(get_db)):
    token = payload.get("token")
    if not token:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="token required")
    inv = db.query(CaregiverInvite).filter(CaregiverInvite.token == token, CaregiverInvite.status == "pending").first()
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found")
    inv.status = "declined"
    db.commit()
    return {"declined": True}


@router.post("/revoke")
def revoke_invite(payload: dict, current_user_id: str = Depends(get_current_user), db: Session = Depends(get_db)):
    invite_id = payload.get("invite_id")
    if not invite_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="invite_id required")
    inv = db.query(CaregiverInvite).filter(CaregiverInvite.id == invite_id).first()
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found")
    # owner check
    child = db.query(Child).filter(Child.id == inv.child_id, Child.user_id == current_user_id).first()
    if not child:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not owner")
    inv.status = "revoked"
    db.commit()
    return {"revoked": True}