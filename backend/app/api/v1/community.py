from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID

from ...db.session import get_db, DbSession
from ..deps import get_current_user, get_current_couple_id, get_current_active_user
from ...models.user import User
from ...models.community import CommunityPost, PostVisibility, PostReaction
from ...models.media import Media
from ...services.community_service import CommunityService
from ...services.event_bus import EventBus

router = APIRouter()
community_service = CommunityService() # Instance for Redis support

class PostCreateRequest(BaseModel):
    content: str
    media_id: Optional[UUID] = None
    visibility: PostVisibility = PostVisibility.PRIVATE_COUPLE

class PostOut(BaseModel):
    id: UUID
    creator_id: UUID
    content: str
    media_id: Optional[UUID]
    visibility: str
    created_at: str

    @classmethod
    def from_orm(cls, post: CommunityPost):
        return cls(
            id=post.id,
            creator_id=post.creator_id,
            content=post.content,
            media_id=post.media_id,
            visibility=post.visibility.value,
            created_at=post.created_at.isoformat()
        )

class ReactionRequest(BaseModel):
    reaction_type: str

class ReportRequest(BaseModel):
    reason: str

class BlockRequest(BaseModel):
    blocked_id: UUID

@router.post("/posts", response_model=PostOut)
async def create_post(
    req: PostCreateRequest,
    current_user: User = Depends(get_current_active_user),
    couple_id: UUID = Depends(get_current_couple_id),
    db: DbSession = Depends(get_db)
):
    if not req.content.strip() and not req.media_id:
        raise HTTPException(status_code=400, detail="Post content or media is required")
    if req.media_id:
        media = db.query(Media).filter(Media.id == req.media_id, Media.couple_id == couple_id, Media.owner_id == current_user.id).first()
        if not media:
            raise HTTPException(status_code=404, detail="Media not found or not owned by this user")
    post = community_service.create_post(
        db=db, couple_id=couple_id, creator_id=current_user.id, content=req.content.strip(),
        media_id=req.media_id, visibility=req.visibility)
    EventBus.publish(db,"COMMUNITY_POSTED","community_post",str(post.id),
                     {"post_id":str(post.id),"has_media":bool(req.media_id)},str(current_user.id))
    db.commit()
    return PostOut.from_orm(post)

@router.get("/feed", response_model=List[PostOut])
async def get_feed(
    current_user: User = Depends(get_current_active_user),
    db: DbSession = Depends(get_db),
    limit: int = 20,
    offset: int = 0
):
    posts = community_service.get_community_feed(
        db=db,
        current_user_id=current_user.id,
        limit=limit,
        offset=offset
    )
    return [PostOut.from_orm(p) for p in posts]

@router.post("/posts/{post_id}/react")
async def react_to_post(
    post_id: UUID,
    req: ReactionRequest,
    current_user: User = Depends(get_current_active_user),
    db: DbSession = Depends(get_db)
):
    community_service.add_reaction(db, str(post_id), str(current_user.id), req.reaction_type)
    return {"message": "Reaction added"}

@router.post("/posts/{post_id}/report")
async def report_post(
    post_id: UUID,
    req: ReportRequest,
    current_user: User = Depends(get_current_active_user),
    db: DbSession = Depends(get_db)
):
    community_service.report_post(db, str(current_user.id), str(post_id), req.reason)
    return {"message": "Post reported successfully"}

@router.post("/block")
async def block_user(
    req: BlockRequest,
    current_user: User = Depends(get_current_active_user),
    db: DbSession = Depends(get_db)
):
    if req.blocked_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot block yourself")

    community_service.block_user(db, str(current_user.id), str(req.blocked_id))
    return {"message": "User blocked"}
