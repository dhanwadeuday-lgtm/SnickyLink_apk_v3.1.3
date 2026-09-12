from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone, timedelta

from ...db.session import get_db, DbSession
from ..deps import get_current_user, get_current_couple_id, get_current_active_user
from ...models.user import User
from ...models.chat import ChatMessage
from ...models.media import Media
from ...models.couple import CoupleMember
from ...models.chat_keys import ChatKey
from ...services.media_service import MediaService
from ...services.event_bus import EventBus

router = APIRouter()

class MessageSendRequest(BaseModel):
    encrypted_content: str
    expires_at_seconds: Optional[int] = None # If provided, message disappears after X seconds
    media_id: Optional[UUID] = None

class MessageOut(BaseModel):
    id: UUID
    sender_id: UUID
    encrypted_content: str
    expires_at: Optional[datetime]
    media_url: Optional[str]
    created_at: datetime

    @classmethod
    def from_orm(cls, msg: ChatMessage, db: Session):
        media_url = None
        if msg.media_id:
            media = db.query(Media).filter(Media.id == msg.media_id).first()
            if media:
                media_url = MediaService.generate_signed_url(media)

        return cls(
            id=msg.id,
            sender_id=msg.sender_id,
            encrypted_content=msg.encrypted_content,
            expires_at=msg.expires_at,
            media_url=media_url,
            created_at=msg.created_at
        )

class PublicKeyRequest(BaseModel):
    public_key: str

class PublicKeyOut(BaseModel):
    public_key: str
    version: int

    @classmethod
    def from_key(cls, key: ChatKey):
        return cls(public_key=key.public_key, version=key.key_version)

@router.post("/keys", response_model=PublicKeyOut)
async def upload_public_key(
    req: PublicKeyRequest,
    current_user: User = Depends(get_current_active_user),
    db: DbSession = Depends(get_db)
):
    # Upsert the public key for the user
    key = db.query(ChatKey).filter(ChatKey.user_id == current_user.id).first()
    if key:
        key.public_key = req.public_key
        key.key_version += 1
    else:
        key = ChatKey(user_id=current_user.id, public_key=req.public_key)
        db.add(key)

    db.commit()
    db.refresh(key)
    return PublicKeyOut.from_key(key)

@router.get("/keys/partner", response_model=PublicKeyOut)
async def get_partner_public_key(
    current_user: User = Depends(get_current_active_user),
    couple_id: UUID = Depends(get_current_couple_id),
    db: DbSession = Depends(get_db)
):
    # Find the partner's user ID in the couple
    partner = db.query(CoupleMember).filter(
        CoupleMember.couple_id == couple_id,
        CoupleMember.user_id != current_user.id
    ).first()

    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found in couple")

    # Fetch the partner's public key
    key = db.query(ChatKey).filter(ChatKey.user_id == partner.user_id).first()
    if not key:
        raise HTTPException(status_code=404, detail="Partner has not uploaded their public key yet")

    return PublicKeyOut.from_key(key)

@router.post("/messages/send")
async def send_message(
    req: MessageSendRequest,
    current_user: User = Depends(get_current_active_user),
    couple_id: UUID = Depends(get_current_couple_id),
    db: DbSession = Depends(get_db)
):
    expires_at = None
    if req.expires_at_seconds:
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=req.expires_at_seconds)

    if not req.encrypted_content.strip():
        raise HTTPException(status_code=400, detail="Encrypted content is required")
    if req.expires_at_seconds is not None and not (1 <= req.expires_at_seconds <= 7 * 24 * 3600):
        raise HTTPException(status_code=400, detail="Disappearing duration must be between 1 second and 7 days")
    if req.media_id:
        media = db.query(Media).filter(Media.id == req.media_id, Media.couple_id == couple_id).first()
        if not media:
            raise HTTPException(status_code=404, detail="Media not found for this couple")
    message = ChatMessage(couple_id=couple_id, sender_id=current_user.id, encrypted_content=req.encrypted_content, expires_at=expires_at, media_id=req.media_id)
    db.add(message); db.flush()
    if req.media_id:
        EventBus.publish(db, "PHOTO_SHARED", "chat_message", str(message.id), {"couple_id":str(couple_id), "media_id":str(req.media_id)}, str(current_user.id))
    db.commit(); db.refresh(message)
    return {"message_id": message.id}

@router.get("/messages/history", response_model=List[MessageOut])
async def get_chat_history(
    couple_id: UUID = Depends(get_current_couple_id),
    db: DbSession = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
    since_timestamp: Optional[datetime] = None
):
    now = datetime.now(timezone.utc)
    # Fetch messages that haven't expired
    messages = db.query(ChatMessage).filter(
        ChatMessage.couple_id == couple_id,
        (ChatMessage.expires_at == None) | (ChatMessage.expires_at > now),
        *( [ChatMessage.created_at > since_timestamp] if since_timestamp else [] )
    ).order_by(ChatMessage.created_at.desc()).offset(offset).limit(limit).all()

    return [MessageOut.from_orm(m, db) for m in reversed(messages)]
