import random
from datetime import datetime, timedelta, timezone
from typing import List
from sqlalchemy.orm import Session
from ..models.snick import Snick, DailySnick, DailySnickState, SnickSubmission, SubmissionType
from ..models.couple import Couple, CoupleMember
from .notification_service import NotificationService
from .personalization_service import PersonalizationService
from .event_bus import EventBus


class SnickService:
    @staticmethod
    def assign_daily_snicks(db: Session, couple_id: str, date: datetime = None):
        """
        Selects 5 Snicks for a couple for a given date using the PersonalizationService.
        """
        if date is None:
            date = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

        # Delegate selection to PersonalizationService
        existing = db.query(DailySnick).filter(DailySnick.couple_id == couple_id, DailySnick.assigned_date == date).first()
        if existing:
            return [x for x in db.query(Snick).join(DailySnick, Snick.id == DailySnick.snick_id).filter(DailySnick.couple_id == couple_id, DailySnick.assigned_date == date).order_by(DailySnick.order_index).all()]
        selected = PersonalizationService.select_daily_snicks(db, couple_id, date)

        # 4. Create DailySnicks with 2-hour windows
        for i, snick in enumerate(selected):
            start_time = date + timedelta(hours=i * 2)
            end_time = start_time + timedelta(hours=2)

            daily_snick = DailySnick(
                couple_id=couple_id,
                snick_id=snick.id,
                assigned_date=date,
                order_index=i + 1,
                window_start=start_time,
                window_end=end_time,
                state=DailySnickState.LOCKED
            )
            db.add(daily_snick)

        db.commit()
        return selected

    @staticmethod
    def get_today_snicks(db: Session, couple_id: str) -> List[DailySnick]:
        """
        Returns today's snicks and updates their state based on time.
        """
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

        snicks = db.query(DailySnick).filter(
            DailySnick.couple_id == couple_id,
            DailySnick.assigned_date == today
        ).order_by(DailySnick.order_index).all()

        now = datetime.now(timezone.utc)
        updated = False

        for s in snicks:
            # Window Management
            if s.state == DailySnickState.LOCKED and now >= s.window_start:
                s.state = DailySnickState.ACTIVE
                updated = True
                EventBus.publish(db,"SNICK_ACTIVATED","daily_snick",str(s.id),{"couple_id":str(s.couple_id)},None)
            elif s.state in [DailySnickState.ACTIVE, DailySnickState.SUBMITTED] and now >= s.window_end:
                # Only expire if not already verified
                if s.state != DailySnickState.VERIFIED:
                    s.state = DailySnickState.EXPIRED
                    updated = True

        if updated:
            db.commit()

        return snicks

    @staticmethod
    def submit_snick(db: Session, daily_snick_id: str, user_id: str, content: str, submission_type: SubmissionType, media_id: str = None):
        """
        Validates and records a snick submission.
        """
        ds = db.query(DailySnick).filter(DailySnick.id == daily_snick_id).first()
        if not ds:
            raise ValueError("Daily snick not found")

        # Validation
        now = datetime.now(timezone.utc)
        if now < ds.window_start or now > ds.window_end:
            raise ValueError("Submission window is not open")

        if ds.state == DailySnickState.VERIFIED:
            raise ValueError("Snick already verified")

        # Create submission
        submission = SnickSubmission(
            daily_snick_id=ds.id,
            submitted_by_user_id=user_id,
            submission_type=submission_type,
            content=content,
            media_id=media_id,
            status="PENDING"
        )
        db.add(submission)

        # Transition state
        ds.state = DailySnickState.SUBMITTED
        EventBus.publish(db, "SNICK_SUBMITTED", "daily_snick", str(ds.id),
                         {"submission_id": str(submission.id), "submission_type": submission_type.value}, user_id)
        db.commit()
        return submission

    @staticmethod
    def decide_submission(db: Session, submission_id: str, deciding_user_id: str, approved: bool):
        """Partner approves/rejects a pending submission and emits SNICK_VERIFIED on approval."""
        sub = db.query(SnickSubmission).filter(SnickSubmission.id == submission_id).first()
        if not sub:
            raise ValueError("Submission not found")
        if sub.submitted_by_user_id == deciding_user_id:
            raise ValueError("You cannot review your own submission")
        if sub.status in {"APPROVED", "REJECTED"}:
            raise ValueError("Submission has already been decided")

        ds = db.query(DailySnick).filter(DailySnick.id == sub.daily_snick_id).first()
        if not ds:
            raise ValueError("Daily snick not found")

        sub.confirmed_by_user_id = deciding_user_id
        sub.confirmed_at = datetime.now(timezone.utc)

        if approved:
            sub.status = "APPROVED"
            ds.state = DailySnickState.VERIFIED
            EventBus.publish(
                db,
                "SNICK_VERIFIED",
                "daily_snick",
                str(ds.id),
                {
                    "submission_id": str(sub.id),
                    "verification_method": "partner",
                    "couple_id": str(ds.couple_id),
                },
                deciding_user_id,
            )
        else:
            sub.status = "REJECTED"
            ds.state = DailySnickState.FAILED

        db.commit()
        return sub

    @staticmethod
    def confirm_submission(db: Session, submission_id: str, confirming_user_id: str):
        """Backward-compatible approval alias."""
        return SnickService.decide_submission(db, submission_id, confirming_user_id, True)
