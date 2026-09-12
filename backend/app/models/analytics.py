from sqlalchemy import Column, String, UUID, ForeignKey, DateTime, JSON, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from .base import Base, TimestampMixin
import uuid

class AnalyticsEvent(Base, TimestampMixin):
    __tablename__ = "analytics_events"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    couple_id = Column(PGUUID(as_uuid=True), ForeignKey("couples.id"), nullable=True, index=True)
    event_name = Column(String, nullable=False, index=True) # e.g., "user_signup", "couple_paired", "snick_completed"
    properties = Column(JSON, nullable=True) # Additional metadata (e.g., {"pillar": "growth", "difficulty": 2})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
