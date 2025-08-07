from pydantic import BaseModel
from typing import Dict, Any


class SyncRequest(BaseModel):
    device_id: str
    sync_data: Dict[str, Any]


class SyncResponse(BaseModel):
    message: str
    synced: bool 