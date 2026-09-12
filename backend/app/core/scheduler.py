from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timezone, timedelta
from ..db.session import SessionLocal
from ..services.snick_service import SnickService
from ..services.event_bus import EventBus
from ..models.couple import Couple
from ..models.snick import DailySnick, DailySnickState
from ..models.chat import ChatMessage
from ..services.event_worker import process_domain_events
from ..models.calendar import CalendarEvent

def daily_snick_assignment_job():
    """
    Job to assign daily snicks to all couples.
    """
    db = SessionLocal()
    try:
        couples = db.query(Couple).all()
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        for couple in couples:
            # Idempotent daily assignment: never create a second set for the same couple/date.
            exists = db.query(DailySnick.id).filter(DailySnick.couple_id == couple.id, DailySnick.assigned_date == today).first()
            if not exists:
                SnickService.assign_daily_snicks(db, str(couple.id), today)
    finally:
        db.close()

def window_expiry_job():
    """
    Job to expire active/submitted snicks past their window_end.
    """
    db = SessionLocal()
    try:
        # This is a bit inefficient to do for all, but works for MVP
        # In production, we'd use a more targeted query
        now = datetime.now(timezone.utc)
        expired_snicks = db.query(DailySnick).filter(
            DailySnick.state.in_([DailySnickState.ACTIVE, DailySnickState.SUBMITTED]),
            DailySnick.window_end <= now
        ).all()

        for s in expired_snicks:
            s.state = DailySnickState.EXPIRED

        db.commit()
    finally:
        db.close()

def cleanup_expired_messages_job():
    """
    Deletes messages that have passed their expires_at timestamp.
    """
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        expired_msgs = db.query(ChatMessage).filter(
            ChatMessage.expires_at != None,
            ChatMessage.expires_at <= now
        ).all()

        for m in expired_msgs:
            db.delete(m)

        db.commit()
    finally:
        db.close()

def calendar_reminder_job():
    db=SessionLocal()
    try:
        now=datetime.now(timezone.utc)
        events=db.query(CalendarEvent).filter(CalendarEvent.event_date >= now,
            CalendarEvent.event_date <= now + timedelta(minutes=30),
            CalendarEvent.reminder_sent.is_(False)).all()
        for ev in events:
            EventBus.publish(db,"CALENDAR_REMINDER_DUE","calendar_event",str(ev.id),
                             {"couple_id":str(ev.couple_id),"title":ev.title},str(ev.created_by_user_id))
            ev.reminder_sent=True
        db.commit()
    finally: db.close()

def start_scheduler():
    scheduler = BackgroundScheduler()
    # Run assignment daily at midnight UTC
    scheduler.add_job(daily_snick_assignment_job, 'cron', hour=0, minute=0)
    # Run expiry check every 15 minutes
    scheduler.add_job(window_expiry_job, 'interval', minutes=15)
    # Clean up disappearing messages every hour
    scheduler.add_job(cleanup_expired_messages_job, 'interval', minutes=60)
    # Durable transactional-outbox worker. Multiple worker processes are safe because
    # event claiming uses PostgreSQL row locks with SKIP LOCKED.
    if __import__("os").getenv("RUN_EVENT_WORKER", "true").lower() == "true":
        scheduler.add_job(process_domain_events, 'interval', seconds=10, max_instances=1, coalesce=True)
    scheduler.add_job(calendar_reminder_job, 'interval', minutes=5, max_instances=1, coalesce=True)
    scheduler.start()
    return scheduler
