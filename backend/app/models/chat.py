from sqlalchemy import Column, String, UUID, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from .base import Base, TimestampMixin
import uuid

class ChatMessage(Base, TimestampMixin):
    __tablename__ = "chat_messages"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    couple_id = Column(PGUUID(as_uuid=True), ForeignKey("couples.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    # E2EE: Server only stores the encrypted blob
    encrypted_content = Column(String, nullable=False)
    # Disappearing message engine: null means permanent
    expires_at = Column(DateTime(timezone=True), nullable=True)
    # Optional link to media if this is a media message
    media_id = Column(PGUUID(as_uuid=True), ForeignKey("media.id"), nullable=True)
