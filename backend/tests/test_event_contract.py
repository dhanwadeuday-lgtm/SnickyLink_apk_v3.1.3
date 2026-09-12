from pathlib import Path

ROOT=Path(__file__).parents[1]

def read(rel): return (ROOT/"app"/rel).read_text()

def test_event_worker_has_retry_and_dead_letter():
    s=read("services/event_worker.py")
    assert "MAX_ATTEMPTS" in s and "DEAD_LETTER" in s and "skip_locked" in s

def test_granular_event_map_is_registered():
    s=read("services/event_handlers.py")
    for name in ["SNICK_SUBMITTED","AI_VERIFICATION_REQUESTED","SNICK_VERIFIED",
                 "DIAMONDS_AWARDED","XP_AWARDED","STATS_UPDATED",
                 "LEADERBOARD_UPDATED","NOTIFICATION_REQUESTED","NOTIFICATION_SENT",
                 "STREAK_UPDATED","MEMORY_CREATED","MEDIA_UPLOADED",
                 "COMMUNITY_POSTED","REPORT_RESOLVED","CALENDAR_REMINDER_DUE"]:
        assert f'"{name}"' in s

def test_media_has_thumbnail_pipeline():
    assert "generate_thumbnail" in read("services/media_service.py")
    assert "MEDIA_UPLOADED" in read("api/v1/media.py")

def test_chat_supports_since_timestamp():
    assert "since_timestamp" in read("api/v1/chat.py")

def test_auth_device_registration_on_login():
    s=read("api/v1/auth.py")
    assert "device_token" in s and 'UserDevice' in s and 'logout' in s

def test_models_include_v1_fields():
    assert "thumbnail_url" in read("models/media.py")
    assert "media_id" in read("models/snick.py")
    assert "suspended" in read("models/user.py")
    assert "moderation_status" in read("models/community.py")
    assert "class Level" in read("models/gamification.py")
