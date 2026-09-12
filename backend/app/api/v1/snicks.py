from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID

from ...db.session import get_db, DbSession
from ..deps import get_current_user, get_current_couple_id, get_current_active_user
from ...models.user import User
from ...models.snick import DailySnick, DailySnickState, SnickSubmission, SubmissionType
from ...services.snick_service import SnickService
from ...services.verification_service import VerificationService
from ...services.analytics_service import AnalyticsService

router = APIRouter()

class SnickTodayResponse(BaseModel):
    id: UUID
    snick_id: UUID
    order_index: int
    window_start: str
    window_end: str
    state: str

    @classmethod
    def from_orm(cls, obj):
        return cls(
            id=obj.id,
            snick_id=obj.snick_id,
            order_index=obj.order_index,
            window_start=obj.window_start.isoformat(),
            window_end=obj.window_end.isoformat(),
            state=obj.state.value
        )

class SubmissionRequest(BaseModel):
    content: str = ""
    submission_type: SubmissionType
    media_id: Optional[UUID] = None

class SubmissionDecisionRequest(BaseModel):
    approved: bool

@router.get("/today", response_model=List[SnickTodayResponse])
async def get_today_snicks(
    couple_id: UUID = Depends(get_current_couple_id),
    db: DbSession = Depends(get_db)
):
    snicks = SnickService.get_today_snicks(db, str(couple_id))
    return [SnickTodayResponse.from_orm(s) for s in snicks]

@router.post("/{daily_snick_id}/submit")
async def submit_snick(
    daily_snick_id: UUID,
    req: SubmissionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    couple_id: UUID = Depends(get_current_couple_id),
    db: DbSession = Depends(get_db)
):
    # Verify the snick belongs to the couple
    from ...models.snick import DailySnick
    ds = db.query(DailySnick).filter(DailySnick.id == daily_snick_id, DailySnick.couple_id == couple_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Daily snick not found for this couple")

    try:
        submission = SnickService.submit_snick(
            db, str(daily_snick_id), str(current_user.id), req.content, req.submission_type, str(req.media_id) if req.media_id else None
        )

        # Log Analytics Event
        AnalyticsService.log_event(
            db=db,
            event_name="snick_submitted",
            couple_id=str(couple_id),
            user_id=str(current_user.id),
            properties={"daily_snick_id": str(daily_snick_id), "type": req.submission_type.value}
        )

        return {"message": "Submitted successfully", "submission_id": submission.id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

async def run_verification(submission_id: UUID):
    # Background tasks need their own session
    from ...db.session import SessionLocal
    db = SessionLocal()
    try:
        await VerificationService.process_submission(db, str(submission_id))
    finally:
        db.close()

@router.post("/submissions/{submission_id}/decision")
async def decide_submission(
    submission_id: UUID,
    req: SubmissionDecisionRequest,
    current_user: User = Depends(get_current_active_user),
    couple_id: UUID = Depends(get_current_couple_id),
    db: DbSession = Depends(get_db)
):
    sub = db.query(SnickSubmission).filter(SnickSubmission.id == submission_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")

    ds = db.query(DailySnick).filter(DailySnick.id == sub.daily_snick_id).first()
    if not ds or ds.couple_id != couple_id:
        raise HTTPException(status_code=403, detail="Forbidden: Submission does not belong to your couple")

    try:
        result = SnickService.decide_submission(
            db, str(submission_id), str(current_user.id), req.approved
        )
        return {
            "message": "Submission approved" if req.approved else "Submission rejected",
            "status": result.status,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/submissions/{submission_id}/confirm")
async def confirm_submission(
    submission_id: UUID,
    current_user: User = Depends(get_current_active_user),
    couple_id: UUID = Depends(get_current_couple_id),
    db: DbSession = Depends(get_db)
):
    """Backward-compatible approval endpoint."""
    sub = db.query(SnickSubmission).filter(SnickSubmission.id == submission_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")
    ds = db.query(DailySnick).filter(DailySnick.id == sub.daily_snick_id).first()
    if not ds or ds.couple_id != couple_id:
        raise HTTPException(status_code=403, detail="Forbidden: Submission does not belong to your couple")
    try:
        SnickService.decide_submission(db, str(submission_id), str(current_user.id), True)
        return {"message": "Confirmed; verification event queued"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{daily_snick_id}/skip")
async def skip_snick(
    daily_snick_id: UUID,
    current_user: User = Depends(get_current_active_user),
    couple_id: UUID = Depends(get_current_couple_id),
    db: DbSession = Depends(get_db)
):
    from ...models.snick import DailySnick, DailySnickState
    ds = db.query(DailySnick).filter(DailySnick.id == daily_snick_id, DailySnick.couple_id == couple_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Daily snick not found")

    ds.state = DailySnickState.FAILED
    db.commit()
    return {"message": "Snick skipped"}
