from sqlalchemy import Column, String, UUID, ForeignKey, Boolean, DateTime, Enum, Integer, Float
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy import func
from .base import Base, TimestampMixin
import uuid
import enum

class SnickPillar(enum.Enum):
    GROWTH = "growth"
    CONNECTION = "connection"
    IMPACT = "impact"
    WELLNESS = "wellness"

class DailySnickState(enum.Enum):
    LOCKED = "LOCKED"
    ACTIVE = "ACTIVE"
    SUBMITTED = "SUBMITTED"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"

class SubmissionType(enum.Enum):
    TEXT = "text"
    PHOTO = "photo"
    PARTNER_CONFIRMATION = "partner_confirmation"

class RewardReason(enum.Enum):
    SNICK_VERIFIED = "snick_verified"
    STREAK_BONUS = "streak_bonus"

class Snick(Base, TimestampMixin):
    __tablename__ = "snicks"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    category = Column(String)
    difficulty = Column(Integer, default=1)
    pillar = Column(Enum(SnickPillar), nullable=False)
    requires_photo = Column(Boolean, default=False)

class DailySnick(Base, TimestampMixin):
    __tablename__ = "daily_snicks"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    couple_id = Column(PGUUID(as_uuid=True), ForeignKey("couples.id", ondelete="CASCADE"), nullable=False, index=True)
    snick_id = Column(PGUUID(as_uuid=True), ForeignKey("snicks.id"), nullable=False)
    assigned_date = Column(DateTime(timezone=True), nullable=False, index=True)
    order_index = Column(Integer, nullable=False) # 1-5
    window_start = Column(DateTime(timezone=True), nullable=False)
    window_end = Column(DateTime(timezone=True), nullable=False)
    state = Column(Enum(DailySnickState), default=DailySnickState.LOCKED, nullable=False)

class SnickSubmission(Base, TimestampMixin):
    __tablename__ = "snick_submissions"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    daily_snick_id = Column(PGUUID(as_uuid=True), ForeignKey("daily_snicks.id", ondelete="CASCADE"), nullable=False, index=True)
    submitted_by_user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    submission_type = Column(Enum(SubmissionType), nullable=False)
    content = Column(String) # text or legacy media URL/reference
    media_id = Column(PGUUID(as_uuid=True), ForeignKey("media.id"), nullable=True, index=True)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    confirmed_by_user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String) # PENDING, APPROVED, REJECTED
    ai_confidence_score = Column(Float, nullable=True) # 0.0 to 1.0
    ai_verification_result = Column(String, nullable=True) # JSON or text result from AI

class DiamondTransaction(Base, TimestampMixin):
    __tablename__ = "diamond_transactions"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    couple_id = Column(PGUUID(as_uuid=True), ForeignKey("couples.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    amount = Column(Integer, nullable=False)
    reason = Column(Enum(RewardReason), nullable=False)
    source_event_id = Column(String, unique=True, nullable=False) # Idempotency key
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class CoupleStats(Base):
    __tablename__ = "couple_stats"

    couple_id = Column(PGUUID(as_uuid=True), ForeignKey("couples.id", ondelete="CASCADE"), primary_key=True)
    total_diamonds = Column(Integer, default=0)
    snicks_completed = Column(Integer, default=0)
    completion_rate = Column(Float, default=0.0)
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    last_updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
