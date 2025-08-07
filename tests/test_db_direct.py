"""Direct database tests (bypassing FastAPI)"""

import pytest
from sqlalchemy.orm import Session
from app.models.user import User
from app.services.auth_service import AuthService
from app.schemas.auth import UserCreate
from datetime import datetime


def test_direct_database_connection():
    """Test direct database connection and user creation"""
    from tests.conftest import test_engine, TestingSessionLocal, Base
    
    # Create tables
    Base.metadata.create_all(bind=test_engine)
    
    # Create session
    session = TestingSessionLocal()
    
    try:
        # Test user creation
        user_data = UserCreate(
            email="test@example.com",
            password="testpassword123",
            first_name="Test",
            last_name="User"
        )
        
        auth_service = AuthService(session)
        user = auth_service.register_user(user_data)
        
        assert user.email == "test@example.com"
        assert user.first_name == "Test"
        assert user.last_name == "User"
        assert user.id is not None
        
        # Test user retrieval
        retrieved_user = session.query(User).filter(User.email == "test@example.com").first()
        assert retrieved_user is not None
        assert retrieved_user.email == "test@example.com"
        
        print(f"✅ Direct database test passed - User ID: {user.id}")
        
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


def test_auth_service_direct():
    """Test auth service with direct database session"""
    from tests.conftest import test_engine, TestingSessionLocal, Base
    
    # Create tables
    Base.metadata.create_all(bind=test_engine)
    
    # Create session
    session = TestingSessionLocal()
    
    try:
        # Test user registration
        user_data = UserCreate(
            email="auth@example.com",
            password="testpassword123",
            first_name="Auth",
            last_name="Test"
        )
        
        auth_service = AuthService(session)
        user = auth_service.register_user(user_data)
        
        # Test authentication
        authenticated_user = auth_service.authenticate_user("auth@example.com", "testpassword123")
        assert authenticated_user is not None
        assert authenticated_user.email == "auth@example.com"
        
        # Test failed authentication
        failed_auth = auth_service.authenticate_user("auth@example.com", "wrongpassword")
        assert failed_auth is None
        
        # Test login
        from app.schemas.auth import UserLogin
        login_data = UserLogin(email="auth@example.com", password="testpassword123")
        token = auth_service.login_user(login_data)
        
        assert token.access_token is not None
        assert token.token_type == "bearer"
        
        print(f"✅ Auth service direct test passed - User ID: {user.id}")
        
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine) 