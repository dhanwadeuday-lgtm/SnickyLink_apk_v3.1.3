from sqlalchemy import Column, String, UUID, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from .base import Base, TimestampMixin
import uuid

class Invite(Base, TimestampMixin):
    __tablename__ = "invites"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    inviter_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    token = Column(String, unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
