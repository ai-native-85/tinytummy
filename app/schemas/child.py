from pydantic import BaseModel, field_validator, model_validator
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
import uuid


class ChildCreate(BaseModel):
    name: str
    # Accept both `date_of_birth` and `dob` from clients via pre-processing
    date_of_birth: date
    dob: Optional[date] = None
    gender: Optional[str] = None
    weight_kg: Optional[Decimal] = None
    height_cm: Optional[Decimal] = None
    allergies: Optional[List[str]] = None
    dietary_restrictions: Optional[List[str]] = None
    region: Optional[str] = None
    pediatrician_name: Optional[str] = None
    pediatrician_contact: Optional[str] = None


class ChildUpdate(BaseModel):
    name: Optional[str] = None
    gender: Optional[str] = None
    weight_kg: Optional[Decimal] = None
    height_cm: Optional[Decimal] = None
    allergies: Optional[List[str]] = None
    dietary_restrictions: Optional[List[str]] = None
    region: Optional[str] = None
    pediatrician_name: Optional[str] = None
    pediatrician_contact: Optional[str] = None


class ChildResponse(BaseModel):
    id: str
    user_id: str
    name: str
    date_of_birth: date
    gender: Optional[str] = None
    weight_kg: Optional[Decimal] = None
    height_cm: Optional[Decimal] = None
    allergies: Optional[List[str]] = None
    dietary_restrictions: Optional[List[str]] = None
    region: Optional[str] = None
    pediatrician_name: Optional[str] = None
    pediatrician_contact: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    @field_validator('id', 'user_id', mode='before')
    @classmethod
    def validate_uuids(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

    class Config:
        from_attributes = True

    @field_validator('gender')
    @classmethod
    def normalize_gender(cls, v):
        if v is None:
            return v
        return str(v).lower()

    @model_validator(mode='before')
    @classmethod
    def accept_dob_alias(cls, values: dict):
        # If client sent `dob`, copy it into `date_of_birth` before validation
        if isinstance(values, dict):
            if values.get('date_of_birth') is None and values.get('dob') is not None:
                values['date_of_birth'] = values['dob']
        return values