import asyncio
import inspect
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session
from ..db.session import SessionLocal
from ..models.events import DomainEvent, EventDelivery
from .event_bus import EventBus

logger = logging.getLogger(__name__)
MAX_EVENT_ATTEMPTS = 8
MAX_ATTEMPTS = MAX_EVENT_ATTEMPTS  # backward-compatible test/config name
MAX_HANDLER_ATTEMPTS = 8
CLAIM_STALE_AFTER_MINUTES = 10


def _handler_name(handler):
    return f"{handler.__module__}.{handler.__qualname__}"


def _invoke(handler, event, db):
    result = handler(event, db)
    if inspect.isawaitable(result):
        return asyncio.run(result)
    return result


def _claim_events(db: Session, limit: int = 25):
    now = datetime.now(timezone.utc)
    stale = now - timedelta(minutes=CLAIM_STALE_AFTER_MINUTES)
    eligible = or_(
        and_(DomainEvent.processed.is_(False), DomainEvent.status == "PENDING",
             or_(DomainEvent.next_attempt_at.is_(None), DomainEvent.next_attempt_at <= now)),
        and_(DomainEvent.processed.is_(False), DomainEvent.status == "PROCESSING",
             DomainEvent.processing_started_at <= stale),
    )
    events = (db.query(DomainEvent).filter(eligible)
              .order_by(DomainEvent.created_at)
              .with_for_update(skip_locked=True).limit(limit).all())
    for event in events:
        event.status = "PROCESSING"
        event.processing_started_at = now
        event.attempts = (event.attempts or 0) + 1
    db.commit()
    return events


def process_domain_events(limit: int = 25):
    db = SessionLocal()
    processed_count = 0
    try:
        for claimed in _claim_events(db, limit):
            event_id = claimed.id
            event = db.query(DomainEvent).filter(DomainEvent.id == event_id).one()
            handlers = list(EventBus._handlers.get(event.event_type, []))
            if not handlers:
                event.status = "DEAD_LETTER"
                event.dead_lettered_at = datetime.now(timezone.utc)
                event.last_error = f"No handler registered for {event.event_type}"
                db.commit()
                continue

            any_failed = False
            now = datetime.now(timezone.utc)
            for handler in handlers:
                name = _handler_name(handler)
                delivery = (db.query(EventDelivery)
                             .filter(EventDelivery.event_id == event.id,
                                     EventDelivery.handler_name == name).first())
                if delivery and delivery.status == "DELIVERED":
                    continue
                if delivery and delivery.next_attempt_at and delivery.next_attempt_at > now:
                    any_failed = True
                    continue
                if not delivery:
                    delivery = EventDelivery(event_id=event.id, handler_name=name,
                                             status="PROCESSING", attempts=0)
                    db.add(delivery)
                    db.flush()
                delivery.status = "PROCESSING"
                delivery.attempts = (delivery.attempts or 0) + 1
                db.commit()  # claim this handler independently from its business transaction
                try:
                    _invoke(handler, event, db)
                    delivery.status = "DELIVERED"
                    delivery.delivered_at = datetime.now(timezone.utc)
                    delivery.last_error = None
                    delivery.next_attempt_at = None
                    db.commit()
                except Exception as exc:
                    db.rollback()
                    # Re-load both rows after rollback so a bad handler cannot poison
                    # sibling handlers or the whole event transaction.
                    event = db.query(DomainEvent).filter(DomainEvent.id == event_id).one()
                    delivery = (db.query(EventDelivery).filter(
                        EventDelivery.event_id == event_id,
                        EventDelivery.handler_name == name).one())
                    delivery.status = "FAILED"
                    delivery.last_error = str(exc)
                    delay = min(900, 2 ** max(delivery.attempts - 1, 0))
                    delivery.next_attempt_at = datetime.now(timezone.utc) + timedelta(seconds=delay)
                    event.last_error = f"{name}: {exc}"
                    any_failed = True
                    logger.exception("Event handler failed: %s", event.last_error)
                    if delivery.attempts >= MAX_HANDLER_ATTEMPTS:
                        delivery.status = "DEAD_LETTER"
                    db.commit()

            event = db.query(DomainEvent).filter(DomainEvent.id == event_id).one()
            deliveries = db.query(EventDelivery).filter(EventDelivery.event_id == event_id).all()
            failed = [d for d in deliveries if d.status in {"FAILED", "PROCESSING"}]
            dead = [d for d in deliveries if d.status == "DEAD_LETTER"]
            if dead or event.attempts >= MAX_EVENT_ATTEMPTS and failed:
                event.status = "DEAD_LETTER"
                event.dead_lettered_at = datetime.now(timezone.utc)
                event.last_error = event.last_error or "One or more handlers exhausted retries"
            elif failed:
                event.status = "PENDING"
                event.next_attempt_at = min((d.next_attempt_at for d in failed if d.next_attempt_at),
                                            default=datetime.now(timezone.utc) + timedelta(seconds=2))
            else:
                event.status = "PROCESSED"
                event.processed = True
                event.processed_at = datetime.now(timezone.utc)
                event.processing_started_at = None
                event.last_error = None
                processed_count += 1
            db.commit()
    finally:
        db.close()
    return processed_count
