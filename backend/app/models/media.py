from sqlalchemy import Column, String, UUID, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from .base import Base, TimestampMixin
import uuid

class Media(Base, TimestampMixin):
    __tablename__ = "media"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    couple_id = Column(PGUUID(as_uuid=True), ForeignKey("couples.id", ondelete="CASCADE"), nullable=False, index=True)
    owner_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    file_path = Column(String, nullable=False) # Path in S3/R2
    mime_type = Column(String, nullable=False)
    size_bytes = Column(Integer, nullable=False)
    thumbnail_url = Column(String, nullable=True)
    processed = Column(Boolean, nullable=False, default=False)
