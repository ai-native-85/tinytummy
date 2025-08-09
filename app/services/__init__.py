from .auth_service import AuthService
from .meal_service import MealService
from .rag_service import RAGService
# Avoid importing CaregiverService here to prevent eager import failures
from .chat_service import ChatService
from .plan_service import PlanService
from .report_service import ReportService
# Deprecated legacy service not exported to avoid drift
from .sync_service import SyncService

__all__ = [
    "AuthService",
    "MealService", 
    "RAGService",
    # "CaregiverService",  # intentionally not exported to avoid eager import
    "ChatService",
    "PlanService",
    "ReportService",
    "GamificationService",
    "SyncService"
]