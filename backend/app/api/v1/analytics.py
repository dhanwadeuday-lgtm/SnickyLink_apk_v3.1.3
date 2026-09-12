from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import List, Dict, Any
from uuid import UUID
from datetime import datetime, timezone, timedelta

from ...db.session import get_db, DbSession
from ..deps import get_current_couple_id
from ...models.snick import DailySnick, DailySnickState
from ...models.couple import CoupleStats
from ...services.reward_service import RewardService
from ...models.analytics import AnalyticsEvent

router = APIRouter()

class StatsSummary(BaseModel):
    total_snicks: int
    completion_rate: float
    current_streak: int
    total_diamonds: int

class ActivityDay(BaseModel):
    date: str
    completed: bool

@router.get("/summary", response_model=StatsSummary)
async def get_couple_summary(
    couple_id: UUID = Depends(get_current_couple_id),
    db: DbSession = Depends(get_db)
):
    stats = db.query(CoupleStats).filter(CoupleStats.couple_id == couple_id).first()
    if not stats:
        # Return zeros if no stats record exists yet
        return StatsSummary(
            total_snicks=0,
            completion_rate=0.0,
            current_streak=0,
            total_diamonds=0
        )

    # Recompute streak on the fly for accuracy
    streak = RewardService.update_streak(db, str(couple_id))

    return StatsSummary(
        total_snicks=stats.snicks_completed,
        completion_rate=stats.completion_rate,
        current_streak=streak,
        total_diamonds=stats.total_diamonds
    )

@router.get("/activity", response_model=List[ActivityDay])
async def get_activity_heatmap(
    couple_id: UUID = Depends(get_current_couple_id),
    db: DbSession = Depends(get_db),
    days: int = 30
):
    today = datetime.now(timezone.utc).date()

    # Find all verified dates for this couple
    verified_dates = {
        d[0] for d in db.query(func.date(DailySnick.assigned_date))\
            .filter(DailySnick.couple_id == couple_id, DailySnick.state == DailySnickState.VERIFIED)\
            .distinct().all()
    }

    # Generate list for the last 'days' days
    activity = []
    for i in range(days):
        date = today - timedelta(days=i)
        activity.append(ActivityDay(
            date=date.isoformat(),
            completed=date in verified_dates
        ))

    return activity


@router.get("/funnel")
async def get_funnel(couple_id: UUID = Depends(get_current_couple_id), db: DbSession = Depends(get_db)):
    rows=db.query(AnalyticsEvent.event_name,func.count(AnalyticsEvent.id)).filter(AnalyticsEvent.couple_id==couple_id).group_by(AnalyticsEvent.event_name).all()
    return {"events":{name:int(count) for name,count in rows}}
