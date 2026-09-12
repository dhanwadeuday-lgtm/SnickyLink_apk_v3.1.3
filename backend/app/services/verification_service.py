from sqlalchemy.orm import Session
from ..models.snick import SnickSubmission, DailySnick, DailySnickState, Snick, SubmissionType
from .ai_service import ai_provider
from .analytics_service import AnalyticsService
from .notification_service import NotificationService
from .event_bus import EventBus
from datetime import datetime, timezone

class VerificationService:
    CONFIDENCE_THRESHOLD_AUTO = 0.8  # Auto-verify if confidence > 80%

    # Status a submission lands in when it cannot be auto-verified and needs a
    # human (the partner) to review it. Used uniformly for: low-confidence AI
    # results, PARTNER_CONFIRMATION-type submissions, and TEXT submissions
    # (there is no automated way to verify free-text content).
    STATUS_NEEDS_PARTNER_CONFIRMATION = "NEEDS_PARTNER_CONFIRMATION"

    @staticmethod
    async def process_submission(db: Session, submission_id: str):
        """
        Orchestrates the verification flow for a submission.

        Terminal outcomes of this method are one of:
          - APPROVED (only via AI auto-verification above the confidence threshold)
          - NEEDS_PARTNER_CONFIRMATION (AI low-confidence, text, or explicit
            partner-confirmation submissions) -- the partner then calls
            SnickService.decide_submission(...) via POST /submissions/{id}/confirm
            or the approve/reject decision endpoint to reach a terminal APPROVED
            or REJECTED state and (on approval) publish SNICK_VERIFIED.

        NOTE: This method itself never publishes SNICK_VERIFIED for the
        partner-confirmation path -- that only happens once a partner actually
        decides, in SnickService.decide_submission. Publishing it here would be
        premature since nothing has actually been verified yet.
        """
        sub = db.query(SnickSubmission).filter(SnickSubmission.id == submission_id).first()
        if not sub:
            return None

        ds = db.query(DailySnick).filter(DailySnick.id == sub.daily_snick_id).first()
        snick_pool = db.query(Snick).filter(Snick.id == ds.snick_id).first()

        if snick_pool.requires_photo and sub.submission_type == SubmissionType.PHOTO:
            # AI-assisted verification for photo submissions.
            prompt = f"Verify if this image shows the user completing the mission: {snick_pool.description}"
            ai_res = await ai_provider.verify_content(sub.content, prompt)

            sub.ai_confidence_score = ai_res["confidence"]
            sub.ai_verification_result = ai_res["result"]

            if sub.ai_confidence_score >= VerificationService.CONFIDENCE_THRESHOLD_AUTO:
                sub.status = "APPROVED"
                ds.state = DailySnickState.VERIFIED

                EventBus.publish(
                    db, "SNICK_VERIFIED", "daily_snick", str(ds.id),
                    {
                        "submission_id": str(sub.id),
                        "verification_method": "ai",
                        "confidence": sub.ai_confidence_score,
                        "couple_id": str(ds.couple_id),
                    },
                    str(sub.submitted_by_user_id),
                )

                NotificationService.notify_partner_confirmed(
                    str(sub.submitted_by_user_id), snick_pool.title, db
                )

                AnalyticsService.log_event(
                    db=db,
                    event_name="snick_completed",
                    couple_id=str(ds.couple_id),
                    properties={"verification_method": "ai", "confidence": sub.ai_confidence_score},
                )
            else:
                # Low-confidence AI result: fall back to a human decision rather
                # than auto-rejecting, since the AI may simply be uncertain.
                sub.status = VerificationService.STATUS_NEEDS_PARTNER_CONFIRMATION

        elif sub.submission_type == SubmissionType.PARTNER_CONFIRMATION:
            # No automated check applies to this type by definition -- the
            # partner's decision IS the verification. The actual approve/reject
            # transition (state change + SNICK_VERIFIED publish) happens in
            # SnickService.decide_submission, called from the confirm/decision
            # endpoints. This method's job is only to put the submission into
            # the correct waiting state.
            sub.status = VerificationService.STATUS_NEEDS_PARTNER_CONFIRMATION

        else:
            # TEXT submissions (and any other non-photo, non-partner-confirmation
            # type): there is no automated way to verify free-text content, so
            # these always require partner review. If auto-approval or a
            # different text-verification rule is wanted later (e.g. minimum
            # length heuristics, profanity/spam checks, or a timeout-based
            # auto-approve), it should be added as an explicit branch here --
            # this is a deliberate policy choice, not a placeholder.
            sub.status = VerificationService.STATUS_NEEDS_PARTNER_CONFIRMATION

        db.commit()
        return sub
