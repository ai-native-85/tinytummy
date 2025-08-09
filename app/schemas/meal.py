from pydantic import BaseModel, UUID4, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from app.models.meal import MealType, InputMethod
import uuid


class MealCreate(BaseModel):
    child_id: UUID4
    meal_type: MealType
    meal_time: datetime
    input_method: InputMethod
    raw_input: str

    @field_validator('meal_type', 'input_method', mode='before')
    @classmethod
    def normalize_enums(cls, v):
        # Accept values like "BREAKFAST" / "Text" by coercing to lowercase first
        if isinstance(v, str):
            return v.lower()
        return v


class MealPatch(BaseModel):
    meal_time: Optional[datetime] = None
    meal_type: Optional[MealType] = None
    description: Optional[str] = None
    raw_input: Optional[str] = None

    @field_validator('meal_type', mode='before')
    @classmethod
    def normalize_meal_type(cls, v):
        if isinstance(v, str):
            return v.lower()
        return v


class MealAnalysisRequest(BaseModel):
    child_id: UUID4
    meal_type: MealType
    meal_time: datetime
    input_method: InputMethod
    raw_input: str


class MealResponse(BaseModel):
    id: str
    child_id: str
    user_id: str
    meal_type: MealType
    meal_time: datetime
    meal_date: Optional[date] = None
    input_method: InputMethod
    raw_input: str
    gpt_analysis: Dict[str, Any]
    food_items: List[str]
    estimated_quantity: Optional[str] = None
    calories: Optional[Decimal] = None
    protein_g: Optional[Decimal] = None
    fat_g: Optional[Decimal] = None
    carbs_g: Optional[Decimal] = None
    fiber_g: Optional[Decimal] = None
    iron_mg: Optional[Decimal] = None
    calcium_mg: Optional[Decimal] = None
    vitamin_a_iu: Optional[Decimal] = None
    vitamin_c_mg: Optional[Decimal] = None
    vitamin_d_iu: Optional[Decimal] = None
    zinc_mg: Optional[Decimal] = None
    folate_mcg: Optional[Decimal] = None
    confidence_score: Optional[Decimal] = None
    notes: Optional[str] = None
    logged_at: datetime
    created_at: datetime
    updated_at: datetime
    affected_dates: Optional[List[str]] = None

    @field_validator('id', 'child_id', 'user_id', mode='before')
    @classmethod
    def validate_uuids(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

    class Config:
        from_attributes = True


class MealTrendResponse(BaseModel):
    date: date
    daily_calories: Optional[Decimal] = None
    daily_protein: Optional[Decimal] = None
    daily_iron: Optional[Decimal] = None
    meal_count: int