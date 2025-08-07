from sqlalchemy import Column, String, DateTime, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import Enum
from sqlalchemy.sql import func
from app.database import Base
import enum


class GuidelineType(str, enum.Enum):
    GROWTH = "growth"
    NUTRITION = "nutrition"
    DEVELOPMENT = "development"
    FEEDING = "feeding"
    ALLERGIES = "allergies"


class NutritionGuideline(Base):
    __tablename__ = "nutrition_guidelines"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    title = Column(String(255), nullable=False)
    guideline_text = Column(String, nullable=False)  # Main content for embedding
    source = Column(String(255), nullable=False)  # WHO, AAP, local guidelines, etc.
    region = Column(String(100), nullable=True)  # Geographic region (US, EU, Asia, etc.)
    language = Column(String(10), default="en")  # Language code
    age_min_months = Column(Integer, nullable=True)  # Minimum age in months
    age_max_months = Column(Integer, nullable=True)  # Maximum age in months
    guideline_type = Column(Enum(GuidelineType), nullable=False)
    embedding_id = Column(String(255), nullable=True)  # Pinecone vector ID
    guideline_metadata = Column(JSONB, default={})  # Additional metadata (tags, keywords, etc.)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now()) 