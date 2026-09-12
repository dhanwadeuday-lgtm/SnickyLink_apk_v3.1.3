import os
from typing import Dict, Any, Optional
import requests
from sqlalchemy.orm import Session
from ..models.device import UserDevice
from ..models.notification import Notification

class NotificationService:
    FCM_API_KEY = os.getenv("FCM_SERVER_KEY")
    FCM_URL = os.getenv("FCM_URL", "https://fcm.googleapis.com/fcm/send")

    @staticmethod
    def send_push_notification(user_id: str, title: str, body: str, data: Optional[Dict[str, Any]] = None, db: Session = None):
        if db is None:
            return False
        notification = Notification(user_id=user_id, title=title, message=body, type=(data or {}).get("type", "SYSTEM"))
        db.add(notification)
        db.flush()
        devices = db.query(UserDevice).filter(UserDevice.user_id == user_id, UserDevice.is_active.is_(True)).all()
        if not devices or not NotificationService.FCM_API_KEY:
            return True
        payload = {"registration_ids": [d.device_token for d in devices], "notification": {"title": title, "body": body, "sound": "default"}, "data": data or {}}
        try:
            r = requests.post(NotificationService.FCM_URL, headers={"Authorization": f"key={NotificationService.FCM_API_KEY}", "Content-Type": "application/json"}, json=payload, timeout=10)
            r.raise_for_status()
            return True
        except requests.RequestException:
            return False

    @staticmethod
    def notify_snick_active(couple_id: str, snick_title: str, db: Session):
        from ..models.couple import CoupleMember
        for m in db.query(CoupleMember).filter(CoupleMember.couple_id == couple_id).all():
            NotificationService.send_push_notification(str(m.user_id), "🎯 New Snick Unlocked!", f"Time for your mission: {snick_title}", {"type": "snick_active"}, db)

    @staticmethod
    def notify_partner_confirmed(user_id: str, snick_title: str, db: Session):
        return NotificationService.send_push_notification(user_id, "💖 Partner Approved!", f"Your partner verified: {snick_title}. You've earned diamonds!", {"type": "snick_verified"}, db)
