from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone, timedelta
from typing import Optional
from ..models.snick import DiamondTransaction, CoupleStats, RewardReason, DailySnick, DailySnickState
from ..models.couple import CoupleMember
from .leaderboard_service import leaderboard_service
from .event_bus import EventBus

class RewardService:
    @staticmethod
    def award_diamonds(db: Session, couple_id: str, amount: int, reason: RewardReason, source_event_id: str, user_id: Optional[str] = None):
        """
        Idempotently award diamonds to a couple/user and update stats.
        """
        # Check for existing transaction to ensure idempotency
        existing = db.query(DiamondTransaction).filter(DiamondTransaction.source_event_id == source_event_id).first()
        if existing:
            return existing

        # 1. Write to immutable ledger
        transaction = DiamondTransaction(
            couple_id=couple_id,
            user_id=user_id,
            amount=amount,
            reason=reason,
            source_event_id=source_event_id
        )
        db.add(transaction)
        db.flush()

        # Downstream projections are event-driven. This service only owns the ledger.
        EventBus.publish(db, "DIAMONDS_AWARDED", "couple", str(couple_id),
                         {"amount": amount, "reason": reason.value, "transaction_id": str(transaction.id)}, user_id)
        db.flush()
        return transaction

    @staticmethod
    def update_streak(db: Session, couple_id: str):
        """
        Recomputes streak based on daily completions.
        A streak is active if the couple completed a snick today or yesterday,
        and has consecutive completions leading back from that point.
        """
        today = datetime.now(timezone.utc).date()

        # Find unique dates where at least one snick was verified
        verified_dates = db.query(func.date(DailySnick.assigned_date))\
            .filter(DailySnick.couple_id == couple_id, DailySnick.state == DailySnickState.VERIFIED)\
            .distinct().all()

        # Convert to a set of dates for O(1) lookup
        dates_set = {d[0] for d in verified_dates}

        if not dates_set:
            return 0

        # Check if streak is still alive (completed today or yesterday)
        if today not in dates_set and (today - timedelta(days=1)) not in dates_set:
            return 0

        # Determine where to start counting from
        start_date = today if today in dates_set else today - timedelta(days=1)

        streak = 0
        check_date = start_date
        while check_date in dates_set:
            streak += 1
            check_date -= timedelta(days=1)

        return streak
