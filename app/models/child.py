from sqlalchemy import Column, String, Date, DateTime, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Child(Base):
    __tablename__ = "children"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    gender = Column(String(10), nullable=True)  # male, female, other
    weight_kg = Column(Numeric(5, 2), nullable=True)
    height_cm = Column(Numeric(5, 2), nullable=True)
    allergies = Column(ARRAY(String), nullable=True)
    dietary_restrictions = Column(ARRAY(String), nullable=True)
    region = Column(String(100), nullable=True)
    pediatrician_name = Column(String(255), nullable=True)
    pediatrician_contact = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="children")
    meals = relationship("Meal", back_populates="child", cascade="all, delete-orphan")
    plans = relationship("Plan", back_populates="child", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="child", cascade="all, delete-orphan")
    caregiver_links = relationship("CaregiverLink", back_populates="child", cascade="all, delete-orphan") 