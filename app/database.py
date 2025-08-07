from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Create Base class
Base = declarative_base()

# Function to create engine dynamically
def create_database_engine(database_url=None):
    """Create database engine with optional custom URL (uses DATABASE_URL)."""
    url = database_url or settings.database_url
    return create_engine(url)

# Create default engine directly from DATABASE_URL
engine = create_engine(settings.database_url)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 