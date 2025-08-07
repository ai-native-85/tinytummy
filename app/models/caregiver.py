from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class CaregiverLink(Base):
    __tablename__ = "caregiver_links"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    child_id = Column(UUID(as_uuid=True), ForeignKey("children.id", ondelete="CASCADE"), nullable=False)
    primary_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    caregiver_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    permissions = Column(JSONB, default={"read": True, "write": False})  # Read/write permissions
    status = Column(String(20), default="pending")  # pending, accepted, declined
    invited_at = Column(DateTime(timezone=True), server_default=func.now())
    responded_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    child = relationship("Child", back_populates="caregiver_links")
    primary_user = relationship("User", foreign_keys=[primary_user_id], back_populates="primary_caregiver_links")
    caregiver_user = relationship("User", foreign_keys=[caregiver_user_id], back_populates="caregiver_links") 