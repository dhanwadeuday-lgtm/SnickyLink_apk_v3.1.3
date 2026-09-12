from sqlalchemy import Column, String, UUID, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from .base import Base, TimestampMixin
import uuid

class Memory(Base, TimestampMixin):
    __tablename__ = "memories"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    couple_id = Column(PGUUID(as_uuid=True), ForeignKey("couples.id", ondelete="CASCADE"), nullable=False, index=True)
    creator_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    media_id = Column(PGUUID(as_uuid=True), ForeignKey("media.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
