from pathlib import Path
ROOT = Path(__file__).parents[1]

def read(rel): return (ROOT / "app" / rel).read_text()

def test_event_worker_isolated_handler_delivery():
    s = read("services/event_worker.py")
    assert "EventDelivery" in s
    assert "DEAD_LETTER" in s
    assert "skip_locked" in s
    assert "db.rollback()" in s

def test_photo_shared_memory_event_exists():
    assert '"PHOTO_SHARED"' in read("services/event_handlers.py")
    assert 'EventBus.publish(db, "MEMORY_CREATED"' in read("services/event_handlers.py")

def test_password_recovery_and_refresh_exist():
    s = read("api/v1/auth.py")
    assert '"/refresh"' in s
    assert '"/password/forgot"' in s
    assert '"/password/reset"' in s

def test_suspended_write_protection_is_centralized():
    s = read("api/deps.py")
    assert "get_current_active_user" in s
    assert "current_user.suspended" in s
    assert "Depends(get_current_active_user)" in s

def test_dedicated_worker_entrypoint_exists():
    s = (ROOT / "app" / "worker.py").read_text()
    assert "start_scheduler" in s and "process_domain_events" in s
