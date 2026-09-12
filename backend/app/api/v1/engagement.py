from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from ...db.session import get_db, DbSession
from ..deps import get_current_user, get_current_couple_id, get_current_active_user
from ...models.user import User
from ...models.calendar import CalendarEvent
from ...services.leaderboard_service import leaderboard_service

router = APIRouter()

# --- Calendar Models ---
class CalendarEventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    event_date: datetime
    is_all_day: bool = False
    is_anniversary: bool = False
    memory_id: Optional[UUID] = None

class CalendarEventOut(BaseModel):
    id: UUID
    title: str
    description: Optional[str]
    event_date: datetime
    is_all_day: bool
    is_anniversary: bool
    memory_id: Optional[UUID]

    @classmethod
    def from_orm(cls, event: CalendarEvent):
        return cls(
            id=event.id,
            title=event.title,
            description=event.description,
            event_date=event.event_date,
            is_all_day=event.is_all_day,
            is_anniversary=event.is_anniversary,
            memory_id=event.memory_id
        )

# --- Leaderboard Models ---
class RankingEntry(BaseModel):
    couple_id: str
    score: int
    rank: int

class CoupleRankResponse(BaseModel):
    rank: Optional[int]
    score: int

# --- Endpoints ---

@router.post("/calendar/events", response_model=CalendarEventOut)
async def create_event(
    req: CalendarEventCreate,
    current_user: User = Depends(get_current_active_user),
    couple_id: UUID = Depends(get_current_couple_id),
    db: DbSession = Depends(get_db)
):
    if req.memory_id:
        from ...models.memory import Memory
        if not db.query(Memory).filter(Memory.id == req.memory_id, Memory.couple_id == couple_id).first():
            raise HTTPException(status_code=404, detail="Memory not found for this couple")

    event = CalendarEvent(
        couple_id=couple_id,
        title=req.title,
        description=req.description,
        event_date=req.event_date,
        is_all_day=req.is_all_day,
        is_anniversary=req.is_anniversary,
        memory_id=req.memory_id,
        created_by_user_id=current_user.id
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return CalendarEventOut.from_orm(event)

@router.get("/calendar/events", response_model=List[CalendarEventOut])
async def get_events(
    couple_id: UUID = Depends(get_current_couple_id),
    db: DbSession = Depends(get_db)
):
    events = db.query(CalendarEvent).filter(CalendarEvent.couple_id == couple_id).order_by(CalendarEvent.event_date).all()
    return [CalendarEventOut.from_orm(e) for e in events]

@router.get("/leaderboard/top", response_model=List[RankingEntry])
async def get_top_rankings(
    time_frame: str = "all_time",
    couple_id: UUID = Depends(get_current_couple_id),
    db: DbSession = Depends(get_db)
):
    rankings = leaderboard_service.get_rankings(time_frame=time_frame)

    return [
        RankingEntry(
            couple_id=couple_id_str,
            score=int(score),
            rank=idx + 1
        )
        for idx, (couple_id_str, score) in enumerate(rankings)
    ]

@router.get("/leaderboard/me", response_model=CoupleRankResponse)
async def get_my_rank(
    time_frame: str = "all_time",
    couple_id: UUID = Depends(get_current_couple_id),
    db: DbSession = Depends(get_db)
):
    rank_info = leaderboard_service.get_couple_rank(str(couple_id), time_frame=time_frame)
    return CoupleRankResponse(**rank_info)
