from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Date, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class BadgeType(str, enum.Enum):
    STREAK = "streak"
    MILESTONE = "milestone"
    ACHIEVEMENT = "achievement"
    SOCIAL = "social"


class Gamification(Base):
    __tablename__ = "gamification"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    child_id = Column(UUID(as_uuid=True), ForeignKey("children.id", ondelete="CASCADE"), nullable=True)
    points = Column(Integer, default=0)
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    badges = Column(JSONB, default=[])  # Array of earned badges
    level = Column(Integer, default=1)
    experience_points = Column(Integer, default=0)
    last_activity_date = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="gamification")
    child = relationship("Child")


class Badge(Base):
    __tablename__ = "badges"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    name = Column(String(100), nullable=False)
    description = Column(String, nullable=False)
    badge_type = Column(Enum(BadgeType), nullable=False)
    icon_url = Column(String(500), nullable=True)
    points_reward = Column(Integer, default=0)
    criteria = Column(JSONB, nullable=False)  # Conditions to earn badge
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user_badges = relationship("UserBadge", back_populates="badge")


class UserBadge(Base):
    __tablename__ = "user_badges"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    badge_id = Column(UUID(as_uuid=True), ForeignKey("badges.id", ondelete="CASCADE"), nullable=False)
    earned_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="user_badges")
    badge = relationship("Badge", back_populates="user_badges") 


# --- Child-focused tables ---

class GamDailyScore(Base):
    __tablename__ = "gam_daily_score"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    child_id = Column(UUID(as_uuid=True), ForeignKey("children.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    score = Column(Integer, nullable=False, default=0)
    components_json = Column(JSONB, default={})
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "child_id", "date", name="uq_gam_daily_score_ucd"),
    )


class GamPointsLedger(Base):
    __tablename__ = "gam_points_ledger"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    child_id = Column(UUID(as_uuid=True), ForeignKey("children.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    points = Column(Integer, nullable=False, default=0)
    reason = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "child_id", "date", "reason", name="uq_gam_points_ledger_ucdr"),
    )


class GamStreak(Base):
    __tablename__ = "gam_streak"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    child_id = Column(UUID(as_uuid=True), ForeignKey("children.id", ondelete="CASCADE"), nullable=False)
    current_length = Column(Integer, nullable=False, default=0)
    best_length = Column(Integer, nullable=False, default=0)
    last_active_date = Column(Date, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "child_id", name="uq_gam_streak_uc"),
    )