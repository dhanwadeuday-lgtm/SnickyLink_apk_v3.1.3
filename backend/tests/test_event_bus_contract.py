from app.services.event_bus import EventBus


class FakeDB:
    def __init__(self):
        self.added = []
        self.flushed = False

    def add(self, value):
        self.added.append(value)

    def flush(self):
        self.flushed = True


def test_publish_only_enqueues_and_does_not_execute_handlers():
    calls = []

    def handler(event, db):
        calls.append(event.event_type)

    original = EventBus._handlers.get("TEST_EVENT", [])[:]
    EventBus._handlers["TEST_EVENT"] = [handler]
    try:
        db = FakeDB()
        event = EventBus.publish(db, "TEST_EVENT", "test", "1", {"ok": True})
        assert event.status == "PENDING"
        assert event.processed is False
        assert db.flushed is True
        assert calls == []
    finally:
        EventBus._handlers["TEST_EVENT"] = original
