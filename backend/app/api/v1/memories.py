from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID

from ...db.session import get_db, DbSession
from ..deps import get_current_user, get_current_couple_id, get_current_active_user
from ...models.user import User
from ...models.memory import Memory
from ...models.media import Media

router = APIRouter()

class MemoryCreateRequest(BaseModel):
    media_id: UUID
    title: str
    description: Optional[str] = None

class MemoryOut(BaseModel):
    id: UUID
    title: str
    description: Optional[str]
    media_id: UUID
    created_at: str

    @classmethod
    def from_orm(cls, m: Memory):
        return cls(
            id=m.id,
            title=m.title,
            description=m.description,
            media_id=m.media_id,
            created_at=m.created_at.isoformat()
        )

@router.post("/memories")
async def create_memory(
    req: MemoryCreateRequest,
    current_user: User = Depends(get_current_active_user),
    couple_id: UUID = Depends(get_current_couple_id),
    db: DbSession = Depends(get_db)
):
    # Verify media belongs to the couple
    media = db.query(Media).filter(Media.id == req.media_id, Media.couple_id == couple_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media not found or does not belong to this couple")

    memory = Memory(
        couple_id=couple_id,
        creator_id=current_user.id,
        media_id=req.media_id,
        title=req.title,
        description=req.description
    )
    db.add(memory)
    db.commit()
    db.refresh(memory)
    return MemoryOut.from_orm(memory)

@router.get("/memories", response_model=List[MemoryOut])
async def get_memories(
    couple_id: UUID = Depends(get_current_couple_id),
    db: DbSession = Depends(get_db)
):
    memories = db.query(Memory).filter(Memory.couple_id == couple_id).order_by(Memory.created_at.desc()).all()
    return [MemoryOut.from_orm(m) for m in memories]
