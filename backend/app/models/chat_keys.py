from sqlalchemy import Column, String, UUID, ForeignKey, DateTime, Integer, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from .base import Base, TimestampMixin
import uuid

class ChatKey(Base, TimestampMixin):
    __tablename__ = "chat_keys"

    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    public_key = Column(String, nullable=False)
    key_version = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
