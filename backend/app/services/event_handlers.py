"""Durable domain-event consumers. Each handler is intentionally idempotent."""
import asyncio, os
from datetime import datetime, timezone
from .event_bus import EventBus
from .reward_service import RewardService
from .notification_service import NotificationService
from .media_service import MediaService
from .leaderboard_service import leaderboard_service
from .ai_service import ai_provider
from ..models.snick import DailySnick, SnickSubmission, RewardReason, DailySnickState, DiamondTransaction, CoupleStats
from ..models.memory import Memory
from ..models.media import Media
from ..models.user import User
from ..models.community import CommunityPost, PostReport
from ..models.gamification import Level, UserLevel, Badge, UserBadge
from ..models.couple import CoupleMember


def handle_snick_submitted(event, db):
    p = event.payload or {}
    sub = db.query(SnickSubmission).filter(SnickSubmission.id == p["submission_id"]).one()
    if sub.submission_type.value == "photo":
        EventBus.publish(db, "AI_VERIFICATION_REQUESTED", "snick_submission", str(sub.id), p, event.actor_user_id)
    else:
        sub.status = "NEEDS_PARTNER_CONFIRMATION"


async def handle_ai_verification_requested(event, db):
    sub = db.query(SnickSubmission).filter(SnickSubmission.id == event.aggregate_id).one()
    ds = db.query(DailySnick).filter(DailySnick.id == sub.daily_snick_id).one()
    from ..models.snick import Snick
    snick = db.query(Snick).filter(Snick.id == ds.snick_id).one()
    image_ref = sub.content or ""
    if sub.media_id:
        media = db.query(Media).filter(Media.id == sub.media_id, Media.couple_id == ds.couple_id).first()
        if not media:
            sub.status = "NEEDS_PARTNER_CONFIRMATION"; return
        image_ref = MediaService.generate_signed_url(media)
    result = await ai_provider.verify_content(image_ref, f"Determine whether this image completes the mission: {snick.description}")
    confidence = max(0.0, min(1.0, float(result.get("confidence", 0))))
    sub.ai_confidence_score = confidence
    sub.ai_verification_result = str(result.get("result", ""))
    if confidence >= 0.8:
        sub.status = "APPROVED"; ds.state = DailySnickState.VERIFIED
        EventBus.publish(db, "SNICK_VERIFIED", "daily_snick", str(ds.id), {
            "submission_id": str(sub.id), "verification_method": "ai", "confidence": confidence,
            "couple_id": str(ds.couple_id), "media_id": str(sub.media_id) if sub.media_id else None,
        }, str(sub.submitted_by_user_id))
    else:
        sub.status = "NEEDS_PARTNER_CONFIRMATION"


def handle_snick_verified(event, db):
    ds = db.query(DailySnick).filter(DailySnick.id == event.aggregate_id).one()
    RewardService.award_diamonds(db, str(ds.couple_id), 10, RewardReason.SNICK_VERIFIED,
                                 f"event:{event.id}", str(event.actor_user_id) if event.actor_user_id else None)
    p = event.payload or {}; mid = p.get("media_id")
    if mid:
        media = db.query(Media).filter(Media.id == mid, Media.couple_id == ds.couple_id).first()
        if media and not db.query(Memory).filter(Memory.media_id == media.id, Memory.couple_id == ds.couple_id).first():
            m = Memory(couple_id=ds.couple_id, creator_id=event.actor_user_id, media_id=media.id,
                       title="Completed Snick", description="Automatically saved from a verified Snick.")
            db.add(m); db.flush()
            EventBus.publish(db, "MEMORY_CREATED", "memory", str(m.id), {"couple_id": str(ds.couple_id), "media_id": str(media.id)}, event.actor_user_id)
    EventBus.publish(db, "STREAK_UPDATED", "couple", str(ds.couple_id), {"couple_id": str(ds.couple_id)}, event.actor_user_id)


def handle_diamonds_awarded(event, db):
    p = event.payload or {}
    EventBus.publish(db, "XP_AWARDED", "couple", str(event.aggregate_id), p, event.actor_user_id)
    EventBus.publish(db, "STATS_UPDATED", "couple", str(event.aggregate_id), p, event.actor_user_id)
    EventBus.publish(db, "LEADERBOARD_UPDATED", "couple", str(event.aggregate_id), p, event.actor_user_id)
    if event.actor_user_id:
        EventBus.publish(db, "NOTIFICATION_REQUESTED", "user", str(event.actor_user_id), {
            "title": "💎 Diamonds earned!", "body": f"You earned {p.get('amount', 0)} diamonds.", "type": "DIAMONDS_AWARDED"
        }, event.actor_user_id)


def handle_xp_awarded(event, db):
    uid = event.actor_user_id
    if not uid: return
    total = sum(r.amount for r in db.query(DiamondTransaction).filter(DiamondTransaction.user_id == uid).all())
    level = db.query(Level).filter(Level.threshold <= total).order_by(Level.threshold.desc()).first()
    if level and not db.query(UserLevel).filter_by(user_id=uid, level_id=level.id).first():
        db.add(UserLevel(user_id=uid, level_id=level.id))
        EventBus.publish(db, "LEVEL_UP", "user", str(uid), {"level_id": str(level.id), "name": level.name, "total_xp": total}, uid)
    for badge in db.query(Badge).filter(Badge.is_active.is_(True), Badge.threshold <= total).all():
        if not db.query(UserBadge).filter_by(user_id=uid, badge_id=badge.id).first():
            db.add(UserBadge(user_id=uid, badge_id=badge.id))
            EventBus.publish(db, "BADGE_AWARDED", "user", str(uid), {"badge_id": str(badge.id), "name": badge.name}, uid)


def handle_stats_updated(event, db):
    cid = event.aggregate_id; p = event.payload or {}
    stats = db.query(CoupleStats).filter_by(couple_id=cid).first()
    if not stats:
        stats = CoupleStats(couple_id=cid); db.add(stats)
    stats.total_diamonds += int(p.get("amount", 0))
    if p.get("reason") == RewardReason.SNICK_VERIFIED.value:
        # Count verified daily Snicks from the source of truth rather than trusting event count.
        stats.snicks_completed = db.query(DailySnick).filter(DailySnick.couple_id == cid, DailySnick.state == DailySnickState.VERIFIED).count()
    total = db.query(DailySnick).filter(DailySnick.couple_id == cid).count()
    stats.completion_rate = stats.snicks_completed / total if total else 0.0


def handle_leaderboard_updated(event, db):
    leaderboard_service.update_score(event.aggregate_id, int((event.payload or {}).get("amount", 0)))


def handle_notification_requested(event, db):
    p = event.payload or {}
    ok = NotificationService.send_push_notification(str(event.aggregate_id), p.get("title", "SnickyLink"), p.get("body", ""), {"type": p.get("type", "SYSTEM")}, db)
    EventBus.publish(db, "NOTIFICATION_SENT", "notification", str(event.id), {"recipient_user_id": str(event.aggregate_id), "type": p.get("type", "SYSTEM"), "delivered": bool(ok)}, event.actor_user_id)


def handle_snicks_activated(event, db):
    from ..models.snick import Snick
    ds = db.query(DailySnick).filter(DailySnick.id == event.aggregate_id).one(); s = db.query(Snick).filter(Snick.id == ds.snick_id).one()
    for m in db.query(CoupleMember).filter(CoupleMember.couple_id == ds.couple_id).all():
        EventBus.publish(db, "NOTIFICATION_REQUESTED", "user", str(m.user_id), {"title":"🎯 New Snick Unlocked!", "body":f"Time for your mission: {s.title}", "type":"SNICK_ACTIVE"}, str(m.user_id))


def handle_streak_updated(event, db):
    cid = event.aggregate_id; stats = db.query(CoupleStats).filter_by(couple_id=cid).first()
    if not stats: stats = CoupleStats(couple_id=cid); db.add(stats)
    current = RewardService.update_streak(db, cid)
    stats.current_streak = current; stats.longest_streak = max(stats.longest_streak or 0, current)


def handle_media_uploaded(event, db):
    media = db.query(Media).filter(Media.id == event.aggregate_id).one()
    if media.processed: return
    content = MediaService.download_file(media.file_path)
    MediaService.validate_image(content, media.mime_type)
    thumb_path = MediaService.generate_thumbnail(content, media.mime_type, str(media.couple_id), str(media.id))
    media.thumbnail_url = MediaService.sign_path(thumb_path)
    media.processed = True


async def _moderate_post(post, db):
    prompt = "Screen this community content for harassment, hate, sexual exploitation, threats, self-harm encouragement, scams, or illegal content. Return JSON with flagged, confidence, reason."
    result = await ai_provider.moderate_content(post.content or "", prompt)
    if post.media_id:
        media = db.query(Media).filter(Media.id == post.media_id, Media.couple_id == post.couple_id).first()
        if media:
            try:
                image_result = await ai_provider.moderate_image(MediaService.generate_signed_url(media), prompt)
                if image_result.get("flagged"): result = image_result
            except Exception:
                result = {"flagged": True, "confidence": 0, "reason": "media_moderation_error"}
    return result


def handle_community_posted(event, db):
    post = db.query(CommunityPost).filter(CommunityPost.id == event.aggregate_id).one()
    if post.moderation_status in {"APPROVED", "FLAGGED"}: return
    result = asyncio.run(_moderate_post(post, db))
    post.moderation_status = "FLAGGED" if result.get("flagged") else "APPROVED"
    post.moderation_reason = result.get("reason")
    if post.moderation_status == "APPROVED":
        EventBus.publish(db, "COMMUNITY_POST_APPROVED", "community_post", str(post.id), {}, event.actor_user_id)


def handle_report_resolved(event, db):
    post = db.query(CommunityPost).filter(CommunityPost.id == event.aggregate_id).first()
    if not post: return
    threshold = int(os.getenv("SUSPENSION_REPORT_THRESHOLD", "3"))
    post_ids = db.query(CommunityPost.id).filter(CommunityPost.creator_id == post.creator_id).subquery()
    count = db.query(PostReport).filter(PostReport.post_id.in_(post_ids), PostReport.status == "RESOLVED").count()
    if count >= threshold:
        user = db.query(User).filter(User.id == post.creator_id).one()
        if not user.suspended:
            user.suspended = True; user.suspended_at = datetime.now(timezone.utc); user.suspension_reason = f"{count} resolved reports"
            EventBus.publish(db, "USER_SUSPENDED", "user", str(user.id), {"resolved_reports": count}, str(user.id))


def handle_calendar_reminder(event, db):
    p = event.payload or {}; cid = p.get("couple_id")
    if not cid: return
    for m in db.query(CoupleMember).filter(CoupleMember.couple_id == cid).all():
        NotificationService.send_push_notification(str(m.user_id), "📅 Upcoming reminder", p.get("title", "Calendar event"), {"type":"CALENDAR_REMINDER"}, db)
        EventBus.publish(db, "NOTIFICATION_SENT", "calendar_event", str(event.aggregate_id), {"recipient_user_id":str(m.user_id), "type":"CALENDAR_REMINDER", "delivered":True}, str(m.user_id))


def handle_photo_shared(event, db):
    p = event.payload or {}; mid = p.get("media_id")
    if not mid: return
    if db.query(Memory).filter(Memory.media_id == mid, Memory.couple_id == event.payload.get("couple_id")).first(): return
    memory = Memory(couple_id=event.payload["couple_id"], creator_id=event.actor_user_id, media_id=mid,
                    title="A moment together", description="Saved automatically from your private chat.")
    db.add(memory); db.flush()
    EventBus.publish(db, "MEMORY_CREATED", "memory", str(memory.id), {"couple_id":event.payload["couple_id"], "media_id":mid}, event.actor_user_id)


def handle_noop(event, db):
    return None


def register_event_handlers():
    handlers = {
        "SNICK_SUBMITTED": handle_snick_submitted,
        "AI_VERIFICATION_REQUESTED": handle_ai_verification_requested,
        "SNICK_VERIFIED": handle_snick_verified,
        "DIAMONDS_AWARDED": handle_diamonds_awarded,
        "XP_AWARDED": handle_xp_awarded,
        "STATS_UPDATED": handle_stats_updated,
        "LEADERBOARD_UPDATED": handle_leaderboard_updated,
        "NOTIFICATION_REQUESTED": handle_notification_requested,
        "SNICK_ACTIVATED": handle_snicks_activated,
        "MEDIA_UPLOADED": handle_media_uploaded,
        "COMMUNITY_POSTED": handle_community_posted,
        "REPORT_RESOLVED": handle_report_resolved,
        "CALENDAR_REMINDER_DUE": handle_calendar_reminder,
        "PHOTO_SHARED": handle_photo_shared,
        "MEMORY_CREATED": handle_noop,
        "COMMUNITY_POST_APPROVED": handle_noop,
        "LEVEL_UP": handle_noop,
        "BADGE_AWARDED": handle_noop,
        "NOTIFICATION_SENT": handle_noop,
        "USER_SUSPENDED": handle_noop,
        "STREAK_UPDATED": handle_streak_updated,
    }
    for name, handler in handlers.items(): EventBus.subscribe(name, handler)
