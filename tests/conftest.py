"""Pytest configuration and fixtures"""

import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Set environment variables BEFORE importing any app modules
os.environ["DATABASE_URL"] = "postgresql://localhost/tinytummy_test"
os.environ["ENVIRONMENT"] = "test"
os.environ["DISABLE_PREMIUM_CHECKS"] = "true"

# Now import app modules after environment is set
from app.database import get_db, Base, create_database_engine
from main import app

# Test database - use local PostgreSQL
SQLALCHEMY_DATABASE_URL = "postgresql://localhost/tinytummy_test"
test_engine = create_database_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    """Override the database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Override the database dependency
app.dependency_overrides[get_db] = override_get_db


# Create database tables and triggers once at the start
def setup_database():
    """Create test database tables and triggers"""
    # Create tables
    Base.metadata.create_all(bind=test_engine)
    
    # Create meal_date trigger
    with test_engine.connect() as conn:
        conn.execute(text("""
            CREATE OR REPLACE FUNCTION update_meal_date()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.meal_date = NEW.meal_time::DATE;
                RETURN NEW;
            END;
            $$ language 'plpgsql';
        """))
        conn.execute(text("""
            DROP TRIGGER IF EXISTS update_meals_meal_date ON meals;
            CREATE TRIGGER update_meals_meal_date 
            BEFORE INSERT OR UPDATE ON meals 
            FOR EACH ROW EXECUTE FUNCTION update_meal_date();
        """))
        conn.commit()


# Setup database once at module level
setup_database()


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Ensure database is set up for testing"""
    yield
    
    # Cleanup at the end
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    """Database session fixture"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    """Create authenticated headers for testing"""
    import uuid
    
    # Use unique email for each test to avoid conflicts
    unique_id = str(uuid.uuid4())[:8]
    user_data = {
        "email": f"test-{unique_id}@example.com",
        "password": "testpassword123",
        "first_name": "Test",
        "last_name": "User"
    }
    
    # Try to register, ignore if user already exists
    response = client.post("/auth/register", json=user_data)
    if response.status_code != 201:
        # User might already exist, try login instead
        pass
    
    # Login to get token
    login_data = {
        "email": user_data["email"],
        "password": user_data["password"]
    }
    
    response = client.post("/auth/login", json=login_data)
    assert response.status_code == 200
    
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def premium_user_headers(client):
    """Create authenticated headers for premium user testing"""
    import uuid
    
    # Use unique email for each test to avoid conflicts
    unique_id = str(uuid.uuid4())[:8]
    user_data = {
        "email": f"premium-{unique_id}@example.com",
        "password": "testpassword123",
        "first_name": "Premium",
        "last_name": "User"
    }
    
    # Try to register, ignore if user already exists
    response = client.post("/auth/register", json=user_data)
    if response.status_code != 201:
        # User might already exist, try login instead
        pass
    
    # Login to get token
    login_data = {
        "email": user_data["email"],
        "password": user_data["password"]
    }
    
    response = client.post("/auth/login", json=login_data)
    assert response.status_code == 200
    
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"} 