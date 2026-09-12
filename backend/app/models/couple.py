from sqlalchemy import Column, UUID, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from .base import Base, TimestampMixin
import uuid

class Couple(Base, TimestampMixin):
    __tablename__ = "couples"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

class CoupleMember(Base):
    __tablename__ = "couple_members"

    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    couple_id = Column(PGUUID(as_uuid=True), ForeignKey("couples.id", ondelete="CASCADE"), nullable=False)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
 # Wait, joined_at should be DateTime
