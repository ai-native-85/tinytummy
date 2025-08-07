from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.sync import SyncRequest, SyncResponse
from app.models.sync import OfflineSync
from app.auth.jwt import get_current_user
from app.utils.responses import sync_response

router = APIRouter(prefix="/sync", tags=["Offline Sync"])


@router.post("/", response_model=SyncResponse)
def sync_data(
    sync_data: SyncRequest,
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Sync offline data with server"""
    # TODO: Implement offline sync logic
    return sync_response(synced_count=0, total_count=0)


@router.get("/pending")
def get_pending_sync(
    device_id: str,
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get pending sync data for a device"""
    pending_sync = db.query(OfflineSync).filter(
        OfflineSync.user_id == current_user_id,
        OfflineSync.device_id == device_id
    ).first()
    
    return pending_sync.sync_data if pending_sync else {} 