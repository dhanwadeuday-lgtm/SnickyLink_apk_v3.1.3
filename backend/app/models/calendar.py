from sqlalchemy import Column, String, UUID, ForeignKey, DateTime, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from .base import Base, TimestampMixin
import uuid

class CalendarEvent(Base, TimestampMixin):
    __tablename__ = "calendar_events"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    couple_id = Column(PGUUID(as_uuid=True), ForeignKey("couples.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    event_date = Column(DateTime(timezone=True), nullable=False, index=True)
    is_all_day = Column(Boolean, default=False)
    is_anniversary = Column(Boolean, default=False)
    memory_id = Column(PGUUID(as_uuid=True), ForeignKey("memories.id"), nullable=True)
    created_by_user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    reminder_sent = Column(Boolean, nullable=False, default=False)
