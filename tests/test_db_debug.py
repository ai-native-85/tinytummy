"""Debug test to check database configuration"""

import os
import pytest
from app.config import settings
from app.database import engine

def test_database_url():
    """Test to see what database URL is being used"""
    print(f"Environment DATABASE_URL: {os.environ.get('DATABASE_URL')}")
    print(f"Settings database_url: {settings.database_url}")
    print(f"Engine URL: {engine.url}")
    print(f"Engine dialect: {engine.dialect.name}")
    
    # Check if we're using PostgreSQL
    assert engine.dialect.name == "postgresql", f"Expected PostgreSQL, got {engine.dialect.name}"
    assert "tinytummy_test" in str(engine.url), f"Expected test database, got {engine.url}"


def test_dependency_override():
    """Test that the dependency override is working"""
    from app.database import get_db
    from main import app
    
    # Check if the override is applied
    assert get_db in app.dependency_overrides, "Dependency override not applied"
    
    # Get a database session
    db_gen = app.dependency_overrides[get_db]()
    db = next(db_gen)
    
    try:
        # Check the engine being used
        print(f"Session engine URL: {db.bind.url}")
        print(f"Session engine dialect: {db.bind.dialect.name}")
        
        assert db.bind.dialect.name == "postgresql", f"Expected PostgreSQL, got {db.bind.dialect.name}"
        assert "tinytummy_test" in str(db.bind.url), f"Expected test database, got {db.bind.url}"
    finally:
        db.close()
        try:
            next(db_gen)
        except StopIteration:
            pass 