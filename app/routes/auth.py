from fastapi import APIRouter, Depends, HTTPException, status
import logging
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.auth import UserCreate, UserLogin, UserResponse, Token
from app.services.auth_service import AuthService
from app.auth.jwt import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    logger = logging.getLogger(__name__)
    try:
        logger.info("Register endpoint called", extra={"email": user_data.email})
        auth_service = AuthService(db)
        user = auth_service.register_user(user_data)
        logger.info("User registered successfully", extra={"user_id": str(user.id), "email": user.email})
        return user
    except HTTPException:
        # Bubble up well-formed HTTP errors
        raise
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during registration"
        )


@router.post("/login", response_model=Token)
def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """Login user and return access token"""
    auth_service = AuthService(db)
    return auth_service.login_user(user_credentials)


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user_id: str = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get current user information"""
    auth_service = AuthService(db)
    user = auth_service.get_user_by_id(current_user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user 