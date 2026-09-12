from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from uuid import UUID
from datetime import datetime

from ...db.session import get_db, DbSession
from ..deps import get_current_user, get_current_active_user
from ...models.user import User
from ...models.notification import Notification
from ...models.device import UserDevice

router = APIRouter()

class DeviceRegisterRequest(BaseModel):
    device_token: str
    platform: str = "unknown"

@router.post("/devices")
async def register_device(req: DeviceRegisterRequest, current_user: User = Depends(get_current_active_user), db: DbSession = Depends(get_db)):
    device = db.query(UserDevice).filter(UserDevice.device_token == req.device_token).first()
    if device:
        device.user_id = current_user.id
        device.platform = req.platform
        device.is_active = True
    else:
        device = UserDevice(user_id=current_user.id, device_token=req.device_token, platform=req.platform)
        db.add(device)
    db.commit()
    return {"status": "registered"}

@router.delete("/devices/{device_token}")
async def unregister_device(device_token: str, current_user: User = Depends(get_current_active_user), db: DbSession = Depends(get_db)):
    device = db.query(UserDevice).filter(UserDevice.user_id == current_user.id, UserDevice.device_token == device_token).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    device.is_active = False
    db.commit()
    return {"status": "unregistered"}

class NotificationOut(BaseModel):
    id: UUID
    title: str
    message: str
    type: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True

@router.get("/", response_model=List[NotificationOut])
async def get_notifications(
    current_user: User = Depends(get_current_active_user),
    db: DbSession = Depends(get_db)
):
    notifications = db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).order_by(Notification.created_at.desc()).all()
    return notifications

@router.post("/mark-read/{notification_id}")
async def mark_notification_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: DbSession = Depends(get_db)
):
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.is_read = True
    db.commit()
    return {"status": "marked as read"}

@router.post("/mark-all-read")
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_active_user),
    db: DbSession = Depends(get_db)
):
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).update({"is_read": True})
    db.commit()
    return {"status": "all marked as read"}
