from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.sql import func
from .base import Base
import uuid

class Level(Base):
    __tablename__ = "levels"
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True)
    threshold = Column(Integer, nullable=False, unique=True, index=True)
    sort_order = Column(Integer, nullable=False, default=0)

class UserLevel(Base):
    __tablename__ = "user_levels"
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    level_id = Column(PGUUID(as_uuid=True), ForeignKey("levels.id"), nullable=False)
    awarded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class Badge(Base):
    __tablename__ = "badges"
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True)
    criteria = Column(Text, nullable=False)
    threshold = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)

class UserBadge(Base):
    __tablename__ = "user_badges"
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    badge_id = Column(PGUUID(as_uuid=True), ForeignKey("badges.id"), primary_key=True)
    awarded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
