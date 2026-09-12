from datetime import datetime, timezone
from typing import Any, Dict, Callable, List, Optional
from sqlalchemy.orm import Session
from ..models.events import DomainEvent, AuditLog

Handler = Callable[[DomainEvent, Session], None]


class EventBus:
    """Durable transactional outbox.

    Publishing only persists the event + audit record. Handlers are executed by the
    background event worker, so a slow/failing handler cannot fail the request that
    created the domain event.
    """
    _handlers: Dict[str, List[Handler]] = {}

    @classmethod
    def subscribe(cls, event_type: str, handler: Handler):
        handlers = cls._handlers.setdefault(event_type, [])
        if handler not in handlers:
            handlers.append(handler)

    @classmethod
    def publish(
        cls,
        db: Session,
        event_type: str,
        aggregate_type: str,
        aggregate_id: str,
        payload: Optional[Dict[str, Any]] = None,
        actor_user_id: Optional[str] = None,
    ) -> DomainEvent:
        event = DomainEvent(
            event_type=event_type,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            payload=payload or {},
            actor_user_id=actor_user_id,
            status="PENDING",
            processed=False,
            attempts=0,
        )
        db.add(event)
        db.flush()
        db.add(
            AuditLog(
                actor_user_id=actor_user_id,
                action=event_type,
                entity_type=aggregate_type,
                entity_id=aggregate_id,
                metadata_json=payload or {},
            )
        )
        # No in-process handler execution here. The outbox worker owns delivery.
        return event
