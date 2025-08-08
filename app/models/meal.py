from sqlalchemy import Column, String, DateTime, Date, Numeric, ForeignKey, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class MealType(str, enum.Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"


class InputMethod(str, enum.Enum):
    TEXT = "text"
    VOICE = "voice"
    IMAGE = "image"


class Meal(Base):
    __tablename__ = "meals"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    child_id = Column(UUID(as_uuid=True), ForeignKey("children.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    # Store as plain text to avoid DB enum constraint issues; validated in app layer
    meal_type = Column(String(32), nullable=False)
    meal_time = Column(DateTime(timezone=True), nullable=False)
    meal_date = Column(Date, nullable=True)  # Populated by trigger
    input_method = Column(String(32), nullable=False)
    raw_input = Column(Text, nullable=False)
    gpt_analysis = Column(JSONB, nullable=False)
    food_items = Column(ARRAY(String), nullable=False)
    estimated_quantity = Column(String, nullable=True)
    calories = Column(Numeric(8, 2), nullable=True)
    protein_g = Column(Numeric(6, 2), nullable=True)
    fat_g = Column(Numeric(6, 2), nullable=True)
    carbs_g = Column(Numeric(6, 2), nullable=True)
    fiber_g = Column(Numeric(6, 2), nullable=True)
    iron_mg = Column(Numeric(6, 2), nullable=True)
    calcium_mg = Column(Numeric(6, 2), nullable=True)
    vitamin_a_iu = Column(Numeric(8, 2), nullable=True)
    vitamin_c_mg = Column(Numeric(6, 2), nullable=True)
    vitamin_d_iu = Column(Numeric(8, 2), nullable=True)
    zinc_mg = Column(Numeric(6, 2), nullable=True)
    folate_mcg = Column(Numeric(6, 2), nullable=True)
    confidence_score = Column(Numeric(3, 2), nullable=True)
    notes = Column(Text, nullable=True)
    logged_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    child = relationship("Child", back_populates="meals")
    user = relationship("User", back_populates="meals") 