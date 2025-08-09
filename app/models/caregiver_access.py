from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class CaregiverInvite(Base):
    __tablename__ = "caregiver_invites"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    child_id = Column(UUID(as_uuid=True), ForeignKey("children.id", ondelete="CASCADE"), nullable=False)
    inviter_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    invitee_email = Column(String, nullable=False)
    role = Column(String(32), nullable=False, default="viewer")
    status = Column(String(16), nullable=False, default="pending")  # pending, accepted, declined, revoked
    token = Column(UUID(as_uuid=True), unique=True, nullable=False, server_default=func.uuid_generate_v4())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)

    child = relationship("Child")

    __table_args__ = (
        UniqueConstraint("child_id", "invitee_email", "status", name="uq_invite_child_email_status"),
    )


class ChildCaregiver(Base):
    __tablename__ = "child_caregivers"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    child_id = Column(UUID(as_uuid=True), ForeignKey("children.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(32), nullable=False, default="viewer")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    child = relationship("Child")

    __table_args__ = (
        UniqueConstraint("child_id", "user_id", name="uq_child_caregiver"),
    )


