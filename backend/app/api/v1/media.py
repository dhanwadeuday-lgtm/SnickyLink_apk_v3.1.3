from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from uuid import UUID

from ...db.session import get_db, DbSession
from ..deps import get_current_user, get_current_couple_id, get_current_active_user
from ...models.user import User
from ...models.media import Media
from ...services.media_service import MediaService
from ...services.event_bus import EventBus

router = APIRouter()

class MediaOut(BaseModel):
    id: UUID
    file_path: str
    signed_url: str
    mime_type: str
    thumbnail_url: Optional[str] = None

class MediaUploadRequest(BaseModel):
    # This is just for documentation, actual upload is via multipart
    pass

@router.post("/upload", response_model=MediaOut)
async def upload_media(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    couple_id: UUID = Depends(get_current_couple_id),
    db: DbSession = Depends(get_db)
):
    content = await file.read()
    try:
        mime_type = MediaService.validate_image(content, file.content_type or "")
    except ValueError as exc:
        detail = str(exc)
        code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE if "size" in detail.lower() else status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
        raise HTTPException(status_code=code, detail=detail)

    try:
        # 2. Upload to Object Storage
        file_path, _ = MediaService.upload_file(
            file_content=content,
            mime_type=mime_type,
            couple_id=str(couple_id),
            owner_id=str(current_user.id)
        )

        # 3. Save to Database
        media = Media(
            couple_id=couple_id,
            owner_id=current_user.id,
            file_path=file_path,
            mime_type=mime_type,
            size_bytes=len(content)
        )
        db.add(media)
        EventBus.publish(db,"MEDIA_UPLOADED","media",str(media.id),
                         {"couple_id":str(couple_id),"mime_type":mime_type,"size_bytes":len(content),"file_path":file_path},
                         str(current_user.id))
        db.commit()
        db.refresh(media)

        # 4. Return Media ID and Signed URL
        return MediaOut(
            id=media.id,
            file_path=media.file_path,
            signed_url=MediaService.generate_signed_url(media),
            mime_type=media.mime_type,
            thumbnail_url=media.thumbnail_url
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Media upload failed: {str(e)}"
        )
