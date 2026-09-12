from sqlalchemy import Column, ForeignKey, String, JSON, DateTime, Boolean, Index, Integer, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.sql import func
from .base import Base
import uuid

class DomainEvent(Base):
    __tablename__ = "domain_events"
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String, nullable=False, index=True)
    aggregate_type = Column(String, nullable=False)
    aggregate_id = Column(String, nullable=False, index=True)
    actor_user_id = Column(PGUUID(as_uuid=True), nullable=True, index=True)
    payload = Column(JSON, nullable=False, default=dict)
    processed = Column(Boolean, nullable=False, default=False, index=True)
    status = Column(String, nullable=False, default="PENDING", index=True)
    attempts = Column(Integer, nullable=False, default=0)
    last_error = Column(Text, nullable=True)
    next_attempt_at = Column(DateTime(timezone=True), nullable=True, index=True)
    processing_started_at = Column(DateTime(timezone=True), nullable=True)
    dead_lettered_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    __table_args__ = (Index("ix_domain_events_dispatch", "status", "processed", "next_attempt_at"),)

class EventDelivery(Base):
    __tablename__ = "event_deliveries"
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(PGUUID(as_uuid=True), ForeignKey("domain_events.id", ondelete="CASCADE"), nullable=False)
    handler_name = Column(String, nullable=False)
    status = Column(String, nullable=False, default="DELIVERED")
    attempts = Column(Integer, nullable=False, default=0)
    last_error = Column(Text, nullable=True)
    next_attempt_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)
    __table_args__ = (UniqueConstraint("event_id", "handler_name", name="uq_event_handler"),)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_user_id = Column(PGUUID(as_uuid=True), nullable=True, index=True)
    action = Column(String, nullable=False, index=True)
    entity_type = Column(String, nullable=True)
    entity_id = Column(String, nullable=True, index=True)
    metadata_json = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
