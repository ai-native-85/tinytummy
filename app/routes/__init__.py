from .auth import router as auth_router
from .children import router as children_router
from .meals import router as meals_router
from .plans import router as plans_router
from .reports import router as reports_router
from .chat import router as chat_router
from .gamification import router as gamification_router
from .caregiver import router as caregiver_router
from .sync import router as sync_router
from .audio import router as audio_router

__all__ = [
    "auth_router",
    "children_router",
    "meals_router", 
    "plans_router",
    "reports_router",
    "chat_router",
    "gamification_router",
    "caregiver_router",
    "sync_router",
    "audio_router",
] 